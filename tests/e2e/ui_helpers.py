"""User-facing navigation shared by browser journeys."""

import re

from playwright.sync_api import expect


def open_more(page):
    """Reveal top-bar actions through their disclosure, preserving its state."""
    button = page.get_by_role("button", name="More", exact=True)
    expect(button).to_have_attribute("aria-controls", "more-menu")
    if button.get_attribute("aria-expanded") == "false":
        button.click()
    expect(button).to_have_attribute("aria-expanded", "true")
    expect(page.locator("#more-menu")).to_be_visible()


def close_more(page):
    """Close the disclosure before reaching content beneath the dropdown."""
    button = page.get_by_role("button", name="More", exact=True)
    if button.get_attribute("aria-expanded") == "true":
        button.click()
    expect(button).to_have_attribute("aria-expanded", "false")
    expect(page.locator("#more-menu")).to_be_hidden()


def open_pair_section(page, name):
    """Reach preserved pair evidence through its native disclosure."""
    summary = page.locator(".detail-pane summary").filter(has_text=re.compile(r"^" + re.escape(name) + r"$"))
    expect(summary).to_be_visible()
    if summary.locator("..").get_attribute("open") is None:
        summary.click()
    expect(summary.locator("..")).to_have_attribute("open", "")
    return summary.locator("..")


def reveal_brief(page):
    """Choose the brief view without altering its fetch or retry behavior."""
    button = page.get_by_role("button", name="Open brief", exact=True)
    expect(button).to_be_visible()
    button.click()
    expect(page.locator("#brief-panel")).to_be_visible()


def back_to_pair(page):
    page.get_by_role("button", name="Back to pair detail", exact=True).click()
    expect(page.locator("#overlap-detail")).to_be_visible()
    expect(page.locator("#brief-panel")).to_be_hidden()
