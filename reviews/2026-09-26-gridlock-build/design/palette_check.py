"""Palette check for DIRECTION.md: WCAG contrast, CIELAB lightness, colour-vision-deficiency separation."""
import itertools

THEMES = {
    "light": {
        "canvas": "#f4f6f4", "panel": "#ffffff", "ink": "#23282e", "pencil": "#5b6670",
        "highlight_fill": "#f2e64d", "highlight_text": "#23282e",
        "utilities": {
            "Dominion Energy SC": "#b8481f", "Georgia Power": "#1d3b73",
            "Georgia Transmission Corp.": "#0f7a70", "MEAG Power": "#6d5bd0",
            "Dalton Utilities": "#7a5a2b", "Georgia ITS (joint)": "#4b5563",
        },
    },
    "dark": {
        "canvas": "#16191c", "panel": "#1d2125", "ink": "#e8ecef", "pencil": "#a7b1ba",
        "highlight_fill": "#5a5210", "highlight_text": "#f7f3cf",
        "utilities": {
            "Dominion Energy SC": "#f08a5d", "Georgia Power": "#8fb0f0",
            "Georgia Transmission Corp.": "#45c2b3", "MEAG Power": "#b3a4f5",
            "Dalton Utilities": "#d0a867", "Georgia ITS (joint)": "#aeb6c2",
        },
    },
}

# Machado et al. 2009 simulation matrices, severity 1.0 (linear RGB)
CVD = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_lin(h):
    h = h.lstrip("#")
    return tuple(lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def lum(rl):
    return 0.2126 * rl[0] + 0.7152 * rl[1] + 0.0722 * rl[2]


def contrast(a, b):
    la, lb = lum(rgb_lin(a)), lum(rgb_lin(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def lab(rl):
    x = (0.4124 * rl[0] + 0.3576 * rl[1] + 0.1805 * rl[2]) / 0.95047
    y = 0.2126 * rl[0] + 0.7152 * rl[1] + 0.0722 * rl[2]
    z = (0.0193 * rl[0] + 0.1192 * rl[1] + 0.9505 * rl[2]) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def simulate(rl, m):
    return tuple(max(0.0, min(1.0, sum(m[i][j] * rl[j] for j in range(3)))) for i in range(3))


def de(a, b):
    return sum((p - q) ** 2 for p, q in zip(a, b)) ** 0.5


for name, t in THEMES.items():
    print(f"== {name} theme ==")
    for u, c in t["utilities"].items():
        print(f"  {u:28s} {c}  vs canvas {contrast(c, t['canvas']):4.2f}:1  L*={lab(rgb_lin(c))[0]:5.1f}")
    print(f"  ink on panel {contrast(t['ink'], t['panel']):.2f}:1 · pencil text on panel {contrast(t['pencil'], t['panel']):.2f}:1"
          f" · highlight text on fill {contrast(t['highlight_text'], t['highlight_fill']):.2f}:1"
          f" · highlight fill vs panel {contrast(t['highlight_fill'], t['panel']):.2f}:1")
    cols = t["utilities"]
    for kind in ["normal"] + list(CVD):
        worst = None
        for (u1, c1), (u2, c2) in itertools.combinations(cols.items(), 2):
            r1, r2 = rgb_lin(c1), rgb_lin(c2)
            if kind != "normal":
                r1, r2 = simulate(r1, CVD[kind]), simulate(r2, CVD[kind])
            d = de(lab(r1), lab(r2))
            if worst is None or d < worst[0]:
                worst = (d, u1, u2)
        print(f"  closest pair ({kind:6s}): dE={worst[0]:5.1f}  {worst[1]} / {worst[2]}")
