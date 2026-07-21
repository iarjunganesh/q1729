# q1729 brand assets

`q1729-banner-light.svg` and `q1729-banner-dark.svg` are the canonical
theme-aware hero banners at the top of `README.md`. They share one visual
language with the architecture diagram (`assets/architecture/`): the same
six-role node palette, rounded node styling, and typography. The right-side
**pipeline-at-a-glance** panel previews the full diagram's own flow
(Ramanujan series → CUDA-Q silicon → crossover analysis → NIM narrator)
rather than inventing a second visual story, and the left column carries the
taxicab-number identity (`1729 = 1³ + 12³ = 9³ + 10³`) that gives the repo
its name.

## Palette (locked)

The four node colors are pulled directly from `assets/architecture/pipeline.mmd`'s
`classDef`s and are **identical in both themes** — opaque fills with white
text already read cleanly on any background:

| Role | Color | Meaning |
| --- | --- | --- |
| `math` | `#B45309` | Ramanujan's series |
| `classical` | `#76B900` | CUDA / CUDA-Q silicon (NVIDIA green) |
| `result` | `#DC2626` | Crossover analysis |
| `ai` | `#0EA5E9` | NIM / Nemotron narrator |

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
