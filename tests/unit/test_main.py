import main


def test_status_check_runs_everywhere(capsys):
    """main() must work with or without cudaq installed (ADR 002)."""
    main.main()
    out = capsys.readouterr().out
    assert "Ramanujan series term 0: 1103" in out
    assert "pi from 2 terms: 3.14159265358979" in out
    assert "cudaq cudaq_available:" in out
    assert "nim nim_configured:" in out
