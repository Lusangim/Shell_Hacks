"""Generate utility colours at fixed CIELAB lightness steps (LCh), then re-run the checks."""
import math
import itertools
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("pc", r"C:\Users\lucia\dev\gridlock-runs\palette_check.py")


def lab_to_hex(L, a, b):
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    finv = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    x, y, z = 0.95047 * finv(fx), finv(fy), 1.08883 * finv(fz)
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    bl = 0.0557 * x - 0.2040 * y + 1.0570 * z
    enc = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return "#" + "".join(f"{round(max(0, min(1, enc(c))) * 255):02x}" for c in (r, g, bl))


def lch(L, C, h):
    return lab_to_hex(L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h)))


# hue (deg), chroma per utility; lightness per theme (light: dark lines on paper; dark: light lines on slate)
SPEC = {
    "Georgia Power": (275, 42, 27, 86),
    "MEAG Power": (330, 46, 38, 56),
    "Dominion Energy SC": (45, 62, 48, 69),
    "Georgia Transmission Corp.": (185, 34, 57, 78),
    "Minor utilities (Dalton Utilities, Georgia ITS)": (65, 9, 44, 64),
}
light = {u: lch(v[2], v[1], v[0]) for u, v in SPEC.items()}
dark = {u: lch(v[3], v[1] * 0.85, v[0]) for u, v in SPEC.items()}
print("light:", light)
print("dark:", dark)

sys.argv = ["pc"]
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module  # loaded below with patched themes
src = open(r"C:\Users\lucia\dev\gridlock-runs\palette_check.py", encoding="utf-8").read()
src = src.replace('"utilities": {\n            "Dominion Energy SC": "#b8481f"', '"utilities": LIGHT_UTILS, "_x": {\n            "Dominion Energy SC": "#b8481f"', 1)
src = src.replace('"utilities": {\n            "Dominion Energy SC": "#f08a5d"', '"utilities": DARK_UTILS, "_x": {\n            "Dominion Energy SC": "#f08a5d"', 1)
exec(compile(src, "palette_check", "exec"), {"LIGHT_UTILS": light, "DARK_UTILS": dark, "__name__": "__main__"})

