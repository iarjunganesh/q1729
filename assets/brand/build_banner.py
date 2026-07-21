#!/usr/bin/env python3
"""Generate the canonical q1729 banner (light + dark SVG).

Source of truth for the README hero banner. Shares its six-role palette
(math / classical / quantum / backend / ai / result) with the architecture
diagram (assets/architecture/pipeline.mmd) so the two read as one system —
see assets/brand/README.md for the locked values.

    python build_banner.py     # writes both SVGs

Edit this file, never the SVG output. Regenerate both themes together.
"""

from __future__ import annotations

import html
import pathlib
from dataclasses import dataclass

W, H = 1600, 400
FONT = "Inter, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

# Six-role node palette — identical in both themes (opaque fills with white
# text already read cleanly on either canvas), matching the classDefs in
# assets/architecture/pipeline.mmd exactly.
MATH = "#B45309"
CLASSICAL = "#76B900"
RESULT = "#DC2626"
AI = "#0EA5E9"


@dataclass(frozen=True)
class Theme:
    name: str
    bg0: str
    bg1: str
    grid: str
    ink: str
    ink_soft: str
    panel: str
    panel_stroke: str
    line: str
    wordmark0: str
    wordmark1: str
    eyebrow: str
    pill: str


# Canvas backgrounds match GitHub's own light/dark README canvas (#ffffff /
# #0d1117) so the banner sits flush against the page with no visible seam —
# the same reasoning as the architecture diagram's theme configs.
DARK = Theme(
    name="dark",
    bg0="#0d1117",
    bg1="#05070a",
    grid="#1b2438",
    ink="#f1f5f9",
    ink_soft="#94a3b8",
    panel="#111827",
    panel_stroke="#233047",
    line="#7c8aa5",
    wordmark0="#f59e0b",
    wordmark1="#4ade80",
    eyebrow="#4ade80",
    pill="#60a5fa",
)

LIGHT = Theme(
    name="light",
    bg0="#ffffff",
    bg1="#eef2f7",
    grid="#dbe3ef",
    ink="#0f172a",
    ink_soft="#64748b",
    panel="#ffffff",
    panel_stroke="#cbd5e1",
    line="#7688a1",
    wordmark0="#B45309",
    wordmark1="#4E7A00",
    eyebrow="#4E7A00",
    pill="#1D4ED8",
)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def text(x, y, s, *, size, fill, weight=400, anchor="start", spacing=None, opacity=1.0):
    ls = f' letter-spacing="{spacing}"' if spacing is not None else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{op}>{esc(s)}</text>'
    )


def rrect(x, y, w, h, r, *, fill, stroke="none", sw=0, opacity=1.0):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke != "none" else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" ry="{r}" fill="{fill}"{st}{op}/>'


def node(cx, cy, w, h, fill, label):
    x, y = cx - w / 2, cy - h / 2
    return "".join(
        [
            f'<g filter="url(#soft)">{rrect(x, y, w, h, 10, fill=fill)}</g>',
            rrect(x + 1, y + 1, w - 2, h * 0.55, 9, fill="url(#sheen)", opacity=0.14),
            text(cx, cy + 5, label, size=13.5, fill="#ffffff", weight=700, anchor="middle"),
        ]
    )


def arrow(x0, y, x1, color):
    return (
        f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" stroke="{color}" '
        f'stroke-width="2.2" stroke-linecap="round" marker-end="url(#bah)"/>'
    )


def pipeline_glance(t: Theme, x, y, w, h) -> str:
    """The four-stage pipeline at a glance, mirroring pipeline.mmd's own
    node colors (math -> classical -> result -> ai) so the banner previews
    the full diagram rather than inventing a second visual story."""
    S = [rrect(x, y, w, h, 20, fill=t.panel, stroke=t.panel_stroke, sw=1.4, opacity=0.95)]
    S.append(f'<circle cx="{x + 26:.1f}" cy="{y + 34:.1f}" r="4.5" fill="{CLASSICAL}"/>')
    S.append(text(x + 40, y + 39, "PIPELINE AT A GLANCE", size=13, fill=t.ink_soft, weight=700, spacing="0.13em"))

    stages = [
        (MATH, "Ramanujan", "1914 series"),
        (CLASSICAL, "CUDA-Q", "silicon"),
        (RESULT, "Crossover", "analysis"),
        (AI, "NIM", "narrator"),
    ]
    n = len(stages)
    nw, nh = 148, 68
    gap = (w - 2 * 36 - n * nw) / (n - 1)
    fy = y + h - nh / 2 - 30
    cxs = [x + 36 + nw / 2 + i * (nw + gap) for i in range(n)]
    for (fill, title, sub), cx in zip(stages, cxs, strict=True):
        S.append(node(cx, fy, nw, nh, fill, title))
        S.append(text(cx, fy + 22, sub, size=10.5, fill="#ffffff", weight=500, anchor="middle", opacity=0.88))
    for cx0, cx1 in zip(cxs, cxs[1:], strict=False):  # intentionally unequal-length pairwise walk
        S.append(arrow(cx0 + nw / 2 + 4, fy, cx1 - nw / 2 - 4, t.line))
    return "".join(S)


def build(t: Theme) -> str:
    S = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">'
    ]

    S.append("<defs>")
    S.append(
        f'<radialGradient id="bg" cx="20%" cy="10%" r="120%">'
        f'<stop offset="0%" stop-color="{t.bg0}"/>'
        f'<stop offset="100%" stop-color="{t.bg1}"/></radialGradient>'
    )
    S.append(
        f'<linearGradient id="word" x1="0" y1="0" x2="1" y2="0.3">'
        f'<stop offset="0%" stop-color="{t.wordmark0}"/>'
        f'<stop offset="100%" stop-color="{t.wordmark1}"/></linearGradient>'
    )
    S.append(
        f'<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{t.wordmark0}"/>'
        f'<stop offset="100%" stop-color="{t.wordmark1}" stop-opacity="0"/></linearGradient>'
    )
    S.append(
        '<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#ffffff" stop-opacity="0.9"/>'
        '<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/></linearGradient>'
    )
    S.append(
        '<filter id="soft" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000000" '
        'flood-opacity="0.25"/></filter>'
    )
    S.append(
        f'<marker id="bah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0 0 L10 5 L0 10 L3 5 Z" fill="{t.line}"/></marker>'
    )
    S.append("</defs>")

    S.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    dots = ['<g opacity="0.55">']
    for gy in range(50, H - 20, 30):
        for gx in range(30, W - 20, 30):
            dots.append(f'<circle cx="{gx}" cy="{gy}" r="1" fill="{t.grid}"/>')
    dots.append("</g>")
    S.append("".join(dots))

    lx = 64
    S.append(text(lx, 96, "q1729", size=64, fill="url(#word)", weight=800, spacing="0.02em"))
    S.append(
        text(
            lx + 3,
            126,
            "RAMANUJAN'S MATHEMATICS MEETS THE NVIDIA STACK",
            size=13,
            fill=t.eyebrow,
            weight=700,
            spacing="0.13em",
        )
    )
    S.append(rrect(lx + 3, 138, 170, 3, 1.5, fill="url(#rule)"))
    S.append(text(lx, 186, "How fast can a GPU compute π —", size=30, fill=t.ink, weight=800))
    S.append(text(lx, 222, "classically, and as a quantum computer?", size=30, fill=t.ink, weight=800))
    S.append(
        text(lx + 2, 258, "Consumer RTX to datacenter H100 — with an AI layer", size=15.5, fill=t.ink_soft, weight=500)
    )
    S.append(text(lx + 2, 280, "that writes up what the numbers show.", size=15.5, fill=t.ink_soft, weight=500))

    # the taxicab-number identity that gives the repo its name
    pw, ph, py = 372, 40, 310
    S.append(rrect(lx, py, pw, ph, ph / 2, fill="none", stroke=t.pill, sw=1.6))
    S.append(
        text(
            lx + pw / 2,
            py + ph / 2 + 5,
            "1729 = 1³ + 12³ = 9³ + 10³",
            size=15,
            fill=t.pill,
            weight=700,
            anchor="middle",
            spacing="0.02em",
        )
    )

    S.append(pipeline_glance(t, 856, 78, 684, 244))

    S.append("</svg>")
    return "".join(S)


def main() -> None:
    here = pathlib.Path(__file__).parent
    for theme, fname in ((DARK, "q1729-banner-dark.svg"), (LIGHT, "q1729-banner-light.svg")):
        (here / fname).write_text(build(theme), encoding="utf-8")
        print(f"wrote {fname}")


if __name__ == "__main__":
    main()
