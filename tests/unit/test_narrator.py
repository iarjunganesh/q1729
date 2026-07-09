import json

import httpx
import pytest

from analysis import narrator


@pytest.fixture
def run_file(tmp_path):
    path = tmp_path / "run.json"
    path.write_text(
        json.dumps(
            {
                "hardware": [{"id": "rtx-5070-8gb"}],
                "runs": [{"hardware": "rtx-5070-8gb", "method": "classical-cuda", "digits": 1000, "time_s": 0.004}],
            }
        ),
        encoding="utf-8",
    )
    return path


class FakeResponse:
    def __init__(self, content="## Findings\n...", status_error=None):
        self._content = content
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def test_nim_configured_reflects_env(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    assert narrator.nim_configured() is False
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    assert narrator.nim_configured() is True


def test_load_run_accepts_sample_file():
    run = narrator.load_run("data/sample_run.json")
    assert run["runs"], "sample run file must contain runs"


def test_load_run_rejects_missing_keys(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"runs": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="hardware"):
        narrator.load_run(bad)


def test_build_prompt_carries_numbers_verbatim(run_file):
    prompt = narrator.build_prompt(narrator.load_run(run_file))
    assert '"digits": 1000' in prompt
    assert '"time_s": 0.004' in prompt


def test_narrate_requires_key(monkeypatch, run_file):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="NVIDIA_API_KEY"):
        narrator.narrate(run_file)


def test_narrate_happy_path(monkeypatch, run_file):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]
        captured["headers"] = kwargs["headers"]
        return FakeResponse("## Findings\nclassical wins")

    monkeypatch.setattr(narrator.httpx, "post", fake_post)

    draft = narrator.narrate(run_file)

    assert draft == "## Findings\nclassical wins"
    assert captured["url"].endswith("/chat/completions")
    assert captured["headers"]["Authorization"] == "Bearer nvapi-test"
    assert captured["json"]["model"] == narrator.DEFAULT_MODEL
    # the run numbers travel in the user message, verbatim
    assert '"digits": 1000' in captured["json"]["messages"][1]["content"]


def test_narrate_honors_env_overrides(monkeypatch, run_file):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    monkeypatch.setenv("NIM_BASE_URL", "https://nim.example/v1")
    monkeypatch.setenv("NIM_MODEL", "nvidia/other-model")
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["model"] = kwargs["json"]["model"]
        return FakeResponse()

    monkeypatch.setattr(narrator.httpx, "post", fake_post)
    narrator.narrate(run_file)

    assert captured["url"] == "https://nim.example/v1/chat/completions"
    assert captured["model"] == "nvidia/other-model"


def test_narrate_propagates_http_errors(monkeypatch, run_file):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    error = httpx.HTTPStatusError("429", request=None, response=None)
    monkeypatch.setattr(narrator.httpx, "post", lambda url, **kw: FakeResponse(status_error=error))

    with pytest.raises(httpx.HTTPStatusError):
        narrator.narrate(run_file)


def test_report_without_key(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    info = narrator.report()
    assert info["nim_configured"] is False
    assert "NVIDIA_API_KEY" in info["hint"]


def test_report_with_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    info = narrator.report()
    assert info["nim_configured"] is True
    assert info["model"] == narrator.DEFAULT_MODEL
