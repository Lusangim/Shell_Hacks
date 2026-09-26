"""Measured browser probes for the remaining UI contract."""

from pathlib import Path
import re


STATES = ("default", "empty", "detail", "area", "late", "error")
VIEWPORTS = ((1440, 900), (390, 844))
THEMES = ("light", "dark")
MINIMUM_JS = "(actual, minimum) => actual < minimum"


PERFORMANCE_INIT = """(() => {
  window.auditTiming = {content: null, shift: 0, shifts: []};
  new PerformanceObserver(list => {
    for (const item of list.getEntries()) if (!item.hadRecentInput) {
      window.auditTiming.shift += item.value;
      window.auditTiming.shifts.push({value:item.value,time:item.startTime,
        sources:item.sources.map(source=>source.node?.id || source.node?.className || source.node?.nodeName)});
    }
  }).observe({type:'layout-shift', buffered:true});
  const observer = new MutationObserver(() => {
    if (document.querySelector('[data-testid="overlap-row"]')) {
      window.auditTiming.content = performance.now(); observer.disconnect();
    }
  });
  observer.observe(document, {childList:true, subtree:true});
})();"""


def timing_issues(content_ms, slider_ms, shift):
    issues = []
    if content_ms is None or content_ms >= 2500:
        issues.append(f"main content {content_ms} ms >= 2500")
    if slider_ms >= 200:
        issues.append(f"slider {slider_ms} ms >= 200")
    if shift >= 0.1:
        issues.append(f"layout shift {shift} >= 0.1")
    return issues


def status_issues(before, after, role):
    if role != "status" or before == after or not re.search(r"\d", after):
        return [f"filter count not announced: {before!r} -> {after!r}, role={role!r}"]
    return []


def recovery_issues(map_count, list_count, message, errors):
    issues = []
    if not map_count or not list_count:
        issues.append("optional failure removed map or list")
    if not re.search(r"try|retry|check|reload|choose|select|local server", message, re.I):
        issues.append("optional failure lacks recovery action")
    return issues + list(errors)


def print_issues(page, expected_text=()):
    return page.evaluate("""expected => {
      const issues=[], visible=el=>el.getClientRects().length && getComputedStyle(el).visibility!=='hidden';
      const report=document.querySelector('#print-report');
      if(!report || !visible(report)) return ['missing visible print report'];
      for(const el of document.querySelectorAll('button,input,select,textarea'))if(visible(el))issues.push('printed control '+(el.id||el.tagName));
      for(const field of ['report_date','filters','source_documents'])if(![...report.querySelectorAll(`[data-src="${field}"]`)].some(el=>visible(el)&&el.textContent.trim()))issues.push('missing print '+field);
      for(const text of expected)if(!report.innerText.includes(text))issues.push('missing complete detail '+text.slice(0,80));
      for(const el of report.querySelectorAll('*')) {
        if(!visible(el))continue;
        const s=getComputedStyle(el);
        if(['hidden','clip'].includes(s.overflow) && (el.scrollWidth>el.clientWidth+1 || el.scrollHeight>el.clientHeight+1))issues.push('clipped print '+el.tagName);
      }
      return issues;
    }""", list(expected_text))


def wait_for_print(page):
    page.wait_for_function("() => window.auditPrinted === true")


def motion_source_issues(css):
    issues = []
    for match in re.finditer(r"transition(?:-property)?\s*:\s*([^;}]+)", re.sub(r"/\*.*?\*/", "", css, flags=re.S), re.I):
        declaration = match.group(0)
        if re.search(r"\b(all|height|width|margin|padding|top|left|right|bottom|inset|flex|grid)\b|\bease-in(?!-)", match.group(1)):
            issues.append(declaration)
    return issues


def matrix_issues(cases):
    expected = {(state, width, theme) for state in STATES for width, _ in VIEWPORTS for theme in THEMES}
    return sorted(expected - set(cases))


def surface_issues(page, focus_only=False):
    probe = Path(__file__).with_name("surface.js").read_text(encoding="utf-8")
    return page.evaluate(f"mode => ({probe})(mode, ({MINIMUM_JS}))", focus_only)
