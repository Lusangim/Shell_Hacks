"""Small Playwright probes adapted from Lucky's read-only website auditors.

The in-page checks keep the source auditors' clipping and skip-link rules. The
focus probe compares focused styles with each element's unfocused styles and
visits every tab stop, addressing the old box-shadow and 25-stop blind spots.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse


FOCUSABLE = (
    'a[href], button, input:not([type="hidden"]), select, textarea, '
    '[tabindex]:not([tabindex="-1"]), summary'
)

OVERFLOW_JS = r"""() => {
  const VW = window.innerWidth, out = [];
  if (document.documentElement.scrollWidth > VW + 1)
    out.push({kind: 'overflow-page', detail: `${document.documentElement.scrollWidth} > ${VW}`});
  document.querySelectorAll('main *').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1 || r.width <= VW + 2) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const clips = ['auto', 'scroll', 'hidden', 'clip'];
    let clipped = clips.includes(cs.overflowX) || el.getAttribute('aria-hidden') === 'true';
    for (let anc = el.parentElement; anc && anc !== document.body && !clipped; anc = anc.parentElement) {
      const style = getComputedStyle(anc);
      clipped = clips.includes(style.overflowX) || anc.getAttribute('aria-hidden') === 'true';
    }
    if (!clipped) out.push({kind: 'overflow-el', detail: `${Math.round(r.width)} > ${VW}`, tag: el.tagName});
  });
  return out;
}"""

KEYBOARD_STATIC_JS = r"""() => {
  const out = [];
  document.querySelectorAll('[tabindex]').forEach((el) => {
    const value = Number.parseInt(el.getAttribute('tabindex'), 10);
    if (value > 0) out.push(`positive tabindex ${value}`);
  });
  const skip = document.querySelector('.skip-link, a[href^="#"][class*="skip"]');
  if (!skip) out.push('missing skip link');
  else if (!document.querySelector(skip.getAttribute('href'))) out.push('broken skip target');
  ['aria-controls', 'aria-labelledby', 'aria-describedby'].forEach((attr) => {
    document.querySelectorAll(`[${attr}]`).forEach((el) => {
      (el.getAttribute(attr) || '').split(/\s+/).filter(Boolean).forEach((id) => {
        if (!document.getElementById(id)) out.push(`${attr} missing #${id}`);
      });
    });
  });
  return out;
}"""

TEXT_LINT_JS = r"""() => {
  const own = [], visible = [];
  // These markers describe computed presentation text, not verbatim plan prose.
  const authored = new Set(['estimate_scope', 'savings_status', 'savings_caveat',
    'assumption', 'assumption_evidence', 'geometry', 'location_caveat', 'accuracy',
    'accuracy_pair', 'distance_km', 'touch_reason', 'timeline', 'year_gap']);
  const names = [...new Set([...document.querySelectorAll('[data-src="name"]')]
    .map(el => el.textContent.trim()).filter(Boolean))].sort((a, b) => b.length - a.length);
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walk.nextNode()) {
    const node = walk.currentNode, parent = node.parentElement;
    if (!parent || parent.closest('script, style, noscript, [hidden], [aria-hidden="true"]')) continue;
    const source = parent.closest('[data-src]')?.dataset.src;
    if (source && !authored.has(source) && !source.startsWith('brief_')) continue;
    if (getComputedStyle(parent).display === 'none') continue;
    const text = node.textContent || '';
    // A brief answer can interpolate complete source names with their real dashes.
    // Exempt only exact known names; lint the surrounding authored sentence.
    const prose = source ? names.reduce((value, name) => value.replaceAll(name, ''), text) : text;
    if (/[\u2013\u2014]|\b(seamless|unleash|revolutionize)\b/i.test(prose)) own.push(text.trim().slice(0, 80));
  }
  const text = document.body.innerText || '';
  if (/\b(?:undefined|NaN|null)\b|\[object\b/.test(text)) visible.push('placeholder token');
  return {own, visible};
}"""


def external_request_urls(urls: list[str], base_url: str) -> list[str]:
    origin = urlparse(base_url)
    return [url for url in urls if (urlparse(url).scheme, urlparse(url).netloc) != (origin.scheme, origin.netloc)]


def color_literals_outside_tokens(root: Path) -> list[str]:
    """Inspect authored UI files, never the vendored Leaflet source."""
    problems = []
    pattern = re.compile(r"(?<![\w-])#[0-9a-fA-F]{3,8}\b|\b(?:rgb|hsl|oklch|lab|lch)\s*\(", re.I)
    for folder in (root / "web" / "css", root / "web" / "js"):
        for path in folder.glob("*"):
            if not path.is_file() or path.name == "tokens.css":
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    problems.append(f"{path.relative_to(root).as_posix()}:{number}")
    return problems


def focus_style(page) -> dict[str, str]:
    return page.evaluate("""() => {
      const el = document.activeElement, cs = getComputedStyle(el);
      return {outlineStyle: cs.outlineStyle, outlineWidth: cs.outlineWidth,
              outlineColor: cs.outlineColor, boxShadow: cs.boxShadow,
              borderColor: cs.borderColor, backgroundColor: cs.backgroundColor};
    }""")


def visible_focus_failures(page) -> list[str]:
    """Tab every stop and require a changed indicator, including the final stop."""
    count = page.evaluate("""(selector) => Array.from(document.querySelectorAll(selector)).filter((el) => {
      const cs = getComputedStyle(el);
      return !el.disabled && (el.getClientRects().length > 0 || cs.position === 'fixed') &&
             cs.display !== 'none' && cs.visibility !== 'hidden' && !el.closest('[hidden], [inert]');
    }).length""", FOCUSABLE)
    baseline = page.evaluate("""(selector) => Array.from(document.querySelectorAll(selector)).map((el) => {
      const cs = getComputedStyle(el);
      return {outlineStyle: cs.outlineStyle, outlineWidth: cs.outlineWidth,
              outlineColor: cs.outlineColor, boxShadow: cs.boxShadow,
              borderColor: cs.borderColor, backgroundColor: cs.backgroundColor};
    })""", FOCUSABLE)
    failures = []
    page.evaluate("document.activeElement?.blur()")
    for index in range(count):
        page.keyboard.press("Tab")
        actual = page.evaluate("""(selector) => {
          const all = Array.from(document.querySelectorAll(selector));
          return all.indexOf(document.activeElement);
        }""", FOCUSABLE)
        if actual < 0:
            active = page.evaluate("document.activeElement?.outerHTML.slice(0, 140)")
            failures.append(f"tab {index + 1}: no focusable element ({active})")
            continue
        focused = focus_style(page)
        before = baseline[actual]
        outline = (
            focused["outlineStyle"] != "none"
            and float(focused["outlineWidth"].removesuffix("px")) >= 2
            and any(focused[key] != before[key] for key in ("outlineStyle", "outlineWidth", "outlineColor"))
        )
        changed = any(focused[key] != before[key] for key in ("boxShadow", "borderColor", "backgroundColor"))
        if not outline and not changed:
            active = page.evaluate("document.activeElement?.outerHTML.slice(0, 140)")
            failures.append(f"tab {index + 1}: no changed focus indicator ({active})")
    return failures
