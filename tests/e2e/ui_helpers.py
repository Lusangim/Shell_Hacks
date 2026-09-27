"""User-facing navigation shared by browser journeys."""

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
