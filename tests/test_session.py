"""
Comprehensive tests for venturalitica.session module.
Covers GovernanceSession: init, symlinks, save_results, lifecycle, thread isolation.
"""

import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from venturalitica.session import GovernanceSession

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class FakeResult:
    """Minimal dataclass that mimics ComplianceResult."""

    control_id: str
    passed: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Run every test inside a fresh temp directory so .venturalitica/ is isolated."""
    monkeypatch.chdir(tmp_path)
    # Reset thread-local between tests
    GovernanceSession._local = threading.local()


# ===========================================================================
# __init__
# ===========================================================================


class TestInit:
    def test_creates_directories(self):
        session = GovernanceSession("myrun")
        assert session.base_dir.exists()
        assert session.artifacts_dir.exists()

    def test_run_id_format(self):
        session = GovernanceSession("audit")
        assert session.run_id.startswith("audit_")
        assert str(os.getpid()) in session.run_id

    def test_run_id_contains_timestamp(self):
        session = GovernanceSession("t")
        # timestamp part: YYYYMMDD_HHMMSS
        parts = session.run_id.split("_")
        # "t", "YYYYMMDD", "HHMMSS", "<pid>"
        assert len(parts) >= 3

    def test_results_file_path(self):
        session = GovernanceSession("x")
        assert session.results_file == session.base_dir / "results.json"


# ===========================================================================
# _update_latest_link
# ===========================================================================


class TestUpdateLatestLink:
    def test_creates_symlink(self):
        session = GovernanceSession("link")
        latest = Path(".venturalitica") / "runs" / "latest"
        if os.name != "nt":
            assert latest.is_symlink()
            assert os.readlink(str(latest)) == session.run_id

    def test_replaces_existing_symlink(self):
        _ = GovernanceSession("first")
        s2 = GovernanceSession("second")
        latest = Path(".venturalitica") / "runs" / "latest"
        if os.name != "nt":
            assert os.readlink(str(latest)) == s2.run_id

    def test_handles_existing_directory(self):
        """If 'latest' is a real directory (not a symlink), it is removed."""
        runs_dir = Path(".venturalitica") / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        latest = runs_dir / "latest"
        latest.mkdir()
        (latest / "dummy.txt").write_text("hi")

        # Creating a session should replace that directory with a symlink
        _ = GovernanceSession("replace")
        if os.name != "nt":
            assert latest.is_symlink()

    def test_handles_symlink_failure_gracefully(self):
        """If os.symlink fails, the fallback path is exercised without error."""
        with patch("os.symlink", side_effect=OSError("nope")):
            # Should not raise
            session = GovernanceSession("fallback")
            assert session.base_dir.exists()


# ===========================================================================
# save_results
# ===========================================================================


class TestSaveResults:
    def test_save_dataclass_objects(self):
        session = GovernanceSession("dc")
        results = [
            FakeResult(control_id="C1", passed=True),
            FakeResult(control_id="C2", passed=False),
        ]
        session.save_results(results)
        data = json.loads(session.results_file.read_text())
        assert len(data) == 2
        assert data[0]["control_id"] == "C1"
        assert data[1]["passed"] is False

    def test_save_plain_dicts(self):
        session = GovernanceSession("dict")
        results = [{"id": "D1", "score": 0.95}]
        session.save_results(results)
        data = json.loads(session.results_file.read_text())
        assert data[0]["id"] == "D1"

    def test_merge_with_existing(self):
        session = GovernanceSession("merge")
        session.save_results([{"run": 1}])
        session.save_results([{"run": 2}])
        data = json.loads(session.results_file.read_text())
        assert len(data) == 2
        assert data[0]["run"] == 1
        assert data[1]["run"] == 2

    def test_corrupt_existing_file_recovery(self):
        """If existing results.json is corrupt, save_results still writes new data."""
        session = GovernanceSession("corrupt")
        session.results_file.write_text("NOT VALID JSON!!!")

        session.save_results([{"ok": True}])
        data = json.loads(session.results_file.read_text())
        # The corrupt content was silently ignored (existing=[])
        assert data == [{"ok": True}]

    def test_save_results_exception_handling(self, capsys):
        """If the entire save operation fails, it prints a warning."""
        session = GovernanceSession("err")
        # Make results_file path unwritable by pointing to an impossible path
        session.results_file = Path("/nonexistent_root_dir/results.json")
        session.save_results([{"a": 1}])
        captured = capsys.readouterr()
        assert "Failed to save session results" in captured.out

    def test_save_empty_results(self):
        session = GovernanceSession("empty")
        session.save_results([])
        data = json.loads(session.results_file.read_text())
        assert data == []


# ===========================================================================
# get_current / start / stop lifecycle
# ===========================================================================


class TestLifecycle:
    def test_get_current_returns_none_initially(self):
        assert GovernanceSession.get_current() is None

    def test_start_sets_current(self):
        session = GovernanceSession.start("lifecycle")
        assert GovernanceSession.get_current() is session

    def test_stop_clears_current(self):
        GovernanceSession.start("lifecycle")
        GovernanceSession.stop()
        assert GovernanceSession.get_current() is None

    def test_start_returns_session(self):
        session = GovernanceSession.start("ret")
        assert isinstance(session, GovernanceSession)


# ===========================================================================
# Thread-local isolation
# ===========================================================================


class TestThreadIsolation:
    def test_sessions_are_thread_local(self):
        """Each thread sees its own current session (or None)."""
        main_session = GovernanceSession.start("main_thread")
        child_sees = [None]

        def child():
            child_sees[0] = GovernanceSession.get_current()

        t = threading.Thread(target=child)
        t.start()
        t.join()

        # Main thread has a session
        assert GovernanceSession.get_current() is main_session
        # Child thread did not inherit it
        assert child_sees[0] is None

    def test_child_thread_can_start_own_session(self):
        child_session = [None]

        def child():
            s = GovernanceSession.start("child")
            child_session[0] = s

        t = threading.Thread(target=child)
        t.start()
        t.join()

        assert child_session[0] is not None
        assert isinstance(child_session[0], GovernanceSession)
        # Main thread still has no session
        assert GovernanceSession.get_current() is None
