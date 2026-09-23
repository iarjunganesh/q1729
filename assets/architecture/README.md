# Architecture assets — source of truth

Theme-aware renders of the repository architecture, embedded in the
`README.md` "Architecture and direction" section.

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

- Keep the flow left-to-right and shallow: inputs (series, known amplitude,
  protocol) → the `gpu` subgraph (one harness run, both arms) → run JSON →
  figures / NIM draft → human review record.
- Draw only what the code does. The series feeds the CUDA kernel, never QAE;
  QAE encodes the known amplitude π/4. Exact SymPy checks the kernel, not
  every path. NIM drafts; a human approves.
- Unbuilt or unmeasured work (the Phase 2 decoder study, H100/multi-GPU) uses
  the dashed `planned` style and a dotted edge, so it cannot be read as a
  result.
- Use `<br/>` for node label wrapping; avoid long unwrapped strings.
- Keep the six `classDef` colors semantically stable across any future edit:
  math (Ramanujan series and graphs, amber), classical (CUDA kernel, NVIDIA
  green), quantum (QAE circuit, blue), backend (protocol and budget, purple),
  ai (narrator and review, cyan), result (run archive and figures, red). The
  seventh, `planned`, is an outline for work that does not exist yet. `assets/brand/`'s
  banner reuses this exact palette so the two read as one system — see
  `assets/brand/README.md`.

## Regenerate the renders

Requires Node.js 24 LTS or newer (latest LTS 24.21.0 checked 2026-09-23; rendered
with Node 26.7.0). From this directory, using the free
and open-source Mermaid CLI — no paid design or image-generation service:

```bash
npx --yes -p @mermaid-js/mermaid-cli@11.17.0 mmdc -i pipeline.mmd -o pipeline-light.svg -b "#ffffff" -c pipeline-light.config.json --scale 3
npx --yes -p @mermaid-js/mermaid-cli@11.17.0 mmdc -i pipeline.mmd -o pipeline-dark.svg -b "#0d1117" -c pipeline-dark.config.json --scale 3
```

Regenerate both together whenever `pipeline.mmd` changes, even if a change
looks theme-agnostic — Mermaid's layout engine can shift node positions
between runs, and a stale partner render is worse than an obviously-missing
one.

## Where this is used

`README.md` embeds both renders through a `<picture>` element that switches on
`prefers-color-scheme`; keep the filenames stable.

## History

The 2026-09-06 audit found the original diagram overstated the pipeline: it
fed the series into QAE, showed an H100 path as if built, and had SymPy
"validate every path". The README used a plain inline diagram meanwhile. On
2026-09-23 the source was redrawn from the code — schema-5 archive, protocol
and budget, human review, Phase 2 graphs, planned work dashed — and both
themes were regenerated with Mermaid CLI 11.17.0.
