"""Live NIM smoke test — runs only when NVIDIA_API_KEY is exported.

One real chat-completions call against the sample run file. Costs API quota;
skips cleanly (like the cudaq suite) when the key is absent.
"""

import pytest

from analysis import narrator

pytestmark = pytest.mark.skipif(
    not narrator.nim_configured(),
    reason="NVIDIA_API_KEY not set — see .env.example (ADR 003)",
)


def test_narrator_drafts_findings_from_sample_run():
    draft = narrator.narrate("data/sample_run.json", timeout=120.0)

    assert isinstance(draft, str)
    assert len(draft) > 200, "expected a findings draft, got a stub"
    # the draft must engage with the actual run data, not generic filler
    assert any(marker in draft.lower() for marker in ("classical", "qae", "h100", "5070"))
