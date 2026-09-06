# Security Policy

## Scope

q1729 is a local research repository, with no deployed network service.
It reads supplied run files and optionally sends them to the NVIDIA NIM API.
Those files can contain environment or other user-supplied information.

## Secrets and data

- `NVIDIA_API_KEY` is the runtime credential, read from the environment at call
  time. `.env` is gitignored but not loaded automatically; never log the key.
- CI may also use `CODECOV_TOKEN`; it is separate from the runtime credential.
- The narrator sends the full JSON object, including system/environment metadata,
  not just performance numbers or GPU names. Review the payload before sending.
- Narration is unchecked model output. It is not trusted executable input or
  validated scientific evidence. Semantic input validation remains a Phase 1 task.

## Build and CI

CI uses read-only repository permissions. The tag-triggered release workflow
has write permission for publishing releases; it does not currently depend on
a separate quality-gate job. Quality/ancestry/version enforcement is open work.
Dependency currency follows AGENTS.md; it does not guarantee dependency safety.

Architecture rendering uses Node.js/Mermaid CLI and its browser tooling locally.
Brand generation uses its Python source. Neither generated SVG should be edited
manually; these are different toolchains. No new tooling was installed by this audit.

## Reporting

Report vulnerabilities through a private GitHub security advisory rather than a
public issue. Maintainer response is best-effort.
