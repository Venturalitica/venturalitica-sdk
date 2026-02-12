from unittest.mock import patch

from venturalitica import enforce, monitor


def test_monitor():
    with patch("venturalitica.probes.CarbonProbe") as mock_carbon:
        with monitor("Test Task"):
            pass
        # Should call start and stop on probes
        assert mock_carbon.return_value.start.called
        assert mock_carbon.return_value.stop.called

def test_enforce_session_flag():
    # Since we can't easily reset the global if it's already True from previous tests,
    # we just verify that calling enforce() ensures it is True.
    enforce(metrics={'acc': 0.9}, policy="non_existent.yaml")
    import venturalitica.api
    assert venturalitica.api._SESSION_ENFORCED

def test_enforce_file_not_found(capsys):
    enforce(policy="missing.yaml")
    captured = capsys.readouterr()
    assert "Policy file not found" in captured.out

def test_enforce_exception(capsys):
    with patch("venturalitica.api.AssuranceValidator", side_effect=ValueError("Boom")):
        enforce(policy="valid.yaml")
    captured = capsys.readouterr()

    assert "Unexpected error" in captured.out
