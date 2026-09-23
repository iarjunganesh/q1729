# q1729 brand assets

`q1729-banner-light.svg` and `q1729-banner-dark.svg` are the canonical
theme-aware hero banners at the top of `README.md`. They share one visual
language with the architecture diagram (`assets/architecture/`): the same
six-role node palette, rounded node styling, and typography. The right-side
**pipeline-at-a-glance** panel previews the full diagram's own flow
(Ramanujan series → CUDA kernel + CUDA-Q on one local GPU → validated run
archive → findings drafted by NIM and reviewed by a human) rather than
inventing a second visual story. The left column states what is measured —
the series on a CUDA kernel against simulated QAE, on an RTX 5070 Laptop GPU,
with H100 planned — and carries the taxicab-number identity
(`1729 = 1³ + 12³ = 9³ + 10³`) that gives the repo its name. The copy was
corrected on 2026-09-23: it previously asked how fast a GPU computes π "as a
quantum computer" and implied a measured H100 axis, neither of which the
evidence supports.

## Palette (locked)

The four node colors are pulled directly from `assets/architecture/pipeline.mmd`'s
`classDef`s and are **identical in both themes** — opaque fills with white
text already read cleanly on any background:

| Role | Color | Meaning |
| --- | --- | --- |
| `math` | `#B45309` | Ramanujan's series |
| `classical` | `#76B900` | CUDA kernel + CUDA-Q on one GPU (NVIDIA green) |
| `result` | `#DC2626` | Validated run archive |
| `ai` | `#0EA5E9` | NIM draft and human review |

Only the **canvas** — background gradient, dot grid, wordmark gradient,
headline/body text, and panel — changes per theme, matching GitHub's own
light (`#ffffff`) and dark (`#0d1117`) README canvas so the banner sits flush
against the page with no visible seam:

| Role | Dark | Light |
| --- | --- | --- |
| Canvas background | `#0d1117` → `#05070a` | `#ffffff` → `#eef2f7` |
| Wordmark gradient | `#f59e0b` → `#4ade80` | `#B45309` → `#4E7A00` |
| Headline ink | `#f1f5f9` | `#0f172a` |
| Taxicab-identity pill | `#60a5fa` | `#1D4ED8` |

Keep these values in `build_banner.py` in sync with the `classDef`s in
`assets/architecture/pipeline.mmd` if either changes — that shared palette is
what makes the banner and the diagram read as one system rather than two
unrelated graphics.

## Files

| File | Purpose |
| --- | --- |
| `build_banner.py` | Source of truth; emits both SVGs |
| `q1729-banner-dark.svg` / `-light.svg` | Canonical banners embedded in `README.md` |

## Regenerate

Edit `build_banner.py` (never the SVG output) and regenerate both themes
together — plain Python, no paid design tool, no Node/browser dependency:

```bash
python build_banner.py
```

The filenames are referenced directly from `README.md` via a `<picture>`
element that switches on `prefers-color-scheme` — keep them stable, or update
the README's `<source>` paths in the same commit if you ever rename them.

## History

The 2026-09-06 audit flagged the banner as illustrative branding that
overstated the project: it asked how fast a GPU computes π "as a quantum
computer" and presented a consumer-RTX-to-H100 axis that had not been
measured. q1729 simulates quantum circuits on classical hardware. On
2026-09-23 the copy and the pipeline-at-a-glance panel were corrected in
`build_banner.py` to match the redrawn architecture diagram, the panel's nodes
were centered, and both themes were regenerated. The palette table is a
selected palette, not an exhaustive count of source colors.
