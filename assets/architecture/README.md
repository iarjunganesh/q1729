# Architecture assets — source of truth

Theme-aware renders of the pipeline diagram used at the top of `README.md`.

## Files

| File | Purpose |
| --- | --- |
| `pipeline.mmd` | Canonical Mermaid source — edit this first |
| `pipeline-light.svg` | Light-theme render, background matched to GitHub's light canvas (`#ffffff`) |
| `pipeline-dark.svg` | Dark-theme render, background matched to GitHub's dark canvas (`#0d1117`) |
| `pipeline-light.config.json` / `pipeline-dark.config.json` | Mermaid theme variables (background, text, line, cluster-border colors) per theme |

The Mermaid source is the only authority for the diagram's structure. Do not
hand-edit an SVG to change a node, label, or edge — update `pipeline.mmd` and
regenerate both renders together, or the two themes will silently diverge.

Node fill colors come from `classDef`s in `pipeline.mmd` itself and are
intentionally the same in both themes — they're opaque boxes with white text,
already dark/saturated enough to read on either background. Only the
**canvas** background, line color, and default text color change per theme
(via the two `.config.json` files); that's the actual meaning of "theme-aware"
here, not a second color palette.

## Diagram design rules

- Keep the flow left-to-right and shallow: series → silicon (local/cloud) →
  crossover analysis → narrator → findings draft.
- The `silicon` subgraph is the one CUDA-Q codebase story — `local` and
  `cloud` are visually nested inside it on purpose, because it's the same
  `quantum/backend.py` code path on both, not a fork.
- Use `<br/>` for node label wrapping; avoid long unwrapped strings.
- Keep the six `classDef` colors semantically stable across any future edit:
  math (Ramanujan series, amber), classical (CUDA kernel, NVIDIA green),
  quantum (QAE circuit, blue), backend (target selection, purple), ai
  (narrator, cyan), result (crossover analysis, red). `assets/brand/`'s
  banner reuses this exact palette so the two read as one system — see
  `assets/brand/README.md`.

## Regenerate the renders

Requires Node.js (any recent version). From this directory, using the free
and open-source Mermaid CLI — no paid design or image-generation service:

```bash
npx --yes -p @mermaid-js/mermaid-cli mmdc -i pipeline.mmd -o pipeline-light.svg -b "#ffffff" -c pipeline-light.config.json --scale 3
npx --yes -p @mermaid-js/mermaid-cli mmdc -i pipeline.mmd -o pipeline-dark.svg -b "#0d1117" -c pipeline-dark.config.json --scale 3
```

Regenerate both together whenever `pipeline.mmd` changes, even if a change
looks theme-agnostic — Mermaid's layout engine can shift node positions
between runs, and a stale partner render is worse than an obviously-missing
one.

## Where this is used

- [Project README](../../README.md) — the Architecture section, embedded via
  a `<picture>` element that switches on `prefers-color-scheme`.
