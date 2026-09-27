"""API-backed Start here and filtered impact checks."""

from collections import Counter
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


def expected_impact(pairs):
    if not pairs:
        return "No pairs match these filters."
    ranges = [pair["savings"] for pair in pairs if pair["savings"]["status"] == "range"]
    low = round(sum(item["low_usd"] for item in ranges) / 1000) * 1000
    high = round(sum(item["high_usd"] for item in ranges) / 1000) * 1000
    utilities = Counter(tuple(sorted((pair["a_utility"], pair["b_utility"]))) for pair in pairs)
    names, count = sorted(utilities.items(), key=lambda item: (-item[1], item[0]))[0]
    savings = f"possible savings of ${low:,} to ${high:,} across {len(ranges)} pairs" if ranges else "no savings ranges in these pairs"
    return (f"{len(pairs)} pairs · {sum(pair['cross_state'] for pair in pairs)} across the state line · "
            f"{savings} · most pairs: {names[0]} and {names[1]} ({count})")


@pytest.mark.parametrize("width,height,theme", [
    (1440, 900, "light"), (1440, 900, "dark"), (390, 844, "light"), (390, 844, "dark"),
])
def test_start_here_and_impact_follow_api_and_pass_axe(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        page.goto(live_server)
        hotspots = page.request.get(f"{live_server}/api/meta").json()["hotspots"]
        if width <= 700:
            # The phone peek folds Start here away; it appears once the sheet is expanded.
            expect(page.locator("#start-here")).to_be_hidden()
            page.locator("#sheet-toggle").click()
        buttons = page.locator("#start-here button")
        expect(buttons).to_have_count(len(hotspots))
        tops = set()
        for button, place in zip(buttons.all(), hotspots):
            short = place["label"].rsplit(" ", 1)[0] if place["label"].split()[-1] in {"city", "town", "CDP", "village"} else place["label"]
            expect(button).to_have_text(f"{short} · {place['pairs']}")
            expect(button).to_have_accessible_name(f"{place['label']}, {place['pairs']} close pairs")
            assert button.evaluate("element => element.getBoundingClientRect().height") >= 44
            tops.add(round(button.evaluate("element => element.getBoundingClientRect().top")))
        assert len(tops) == 1, "the chips stay on one row"
        pairs = page.request.get(f"{live_server}/api/overlaps").json()
        expect(page.locator("#impact-line")).to_have_text(expected_impact(pairs))
        buttons.first.click()
        expect(page.locator("#area-panel")).to_be_visible()
        expect(page.locator("#area-radius-output")).to_have_text("10 km")
        assert page.evaluate("""async () => {
          const { state } = await import('/web/js/state.js');
          const center = state.map.getCenter();
          return [center.lat, center.lng];
        }""") == [hotspots[0]["lat"], hotspots[0]["lon"]]
        axe = (Path(__file__).parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")
        violations = page.evaluate(axe + "\nwindow.axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]
        assert violations == []
        page.locator("#filters-toggle").click()
        page.locator("#filter-band").select_option("touching")
        touching = page.request.get(f"{live_server}/api/overlaps?band=touching").json()
        expect(page.locator("#impact-line")).to_have_text(expected_impact(touching))
        violations = page.evaluate("window.axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]
        assert violations == []
        browser.close()


def test_impact_empty_filters_message(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{live_server}/?year_min=2200")
        expect(page.locator("#impact-line")).to_have_text("No pairs match these filters.")
        browser.close()
