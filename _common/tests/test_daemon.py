"""Tests for toq_common.daemon module."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from toq_common import daemon


def test_is_running_true():
    with patch("httpx.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        assert daemon.is_running(9009) is True


def test_is_running_false_on_connect_error():
    import httpx
    with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
        assert daemon.is_running(9009) is False


def test_is_running_false_on_timeout():
    import httpx
    with patch("httpx.get", side_effect=httpx.TimeoutException("timeout")):
        assert daemon.is_running(9009) is False


def test_stop_noop_when_no_managed_process():
    daemon._managed_process = None
    daemon.stop()  # should not raise


def test_stop_sends_shutdown_and_waits():
    mock_proc = MagicMock()
    mock_proc.wait.return_value = 0
    daemon._managed_process = mock_proc
    daemon._log_file = MagicMock()

    with patch("httpx.post"):
        daemon.stop()

    assert daemon._managed_process is None
    mock_proc.wait.assert_called_once()


def test_ensure_running_starts_if_not_running():
    with patch.object(daemon, "is_running", return_value=False), \
         patch.object(daemon, "start") as mock_start:
        daemon.ensure_running()
        mock_start.assert_called_once()


def test_ensure_running_noop_if_running():
    with patch.object(daemon, "is_running", return_value=True), \
         patch.object(daemon, "start") as mock_start:
        daemon.ensure_running()
        mock_start.assert_not_called()


def test_atexit_stop_swallows_exceptions():
    with patch.object(daemon, "stop", side_effect=RuntimeError("boom")):
        daemon._atexit_stop(9009)  # should not raise


def test_start_raises_if_process_exits_immediately():
    mock_proc = MagicMock()
    mock_proc.poll.return_value = 1  # exited immediately
    mock_proc.returncode = 1

    with patch("subprocess.Popen", return_value=mock_proc), \
         patch("builtins.open", MagicMock()), \
         patch.object(daemon, "LOG_DIR", MagicMock()):
        with pytest.raises(RuntimeError, match="exited immediately"):
            daemon.start()


def test_start_raises_if_health_timeout():
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # still running

    with patch("subprocess.Popen", return_value=mock_proc), \
         patch("builtins.open", MagicMock()), \
         patch.object(daemon, "LOG_DIR", MagicMock()), \
         patch.object(daemon, "is_running", return_value=False), \
         patch.object(daemon, "HEALTH_TIMEOUT_SECONDS", 0.1), \
         patch.object(daemon, "HEALTH_POLL_INTERVAL_SECONDS", 0.05):
        with pytest.raises(RuntimeError, match="did not become healthy"):
            daemon.start()
        mock_proc.terminate.assert_called_once()


def test_stop_terminates_on_shutdown_timeout():
    mock_proc = MagicMock()
    mock_proc.wait.side_effect = [subprocess.TimeoutExpired("toq", 5), None]

    daemon._managed_process = mock_proc
    daemon._log_file = MagicMock()

    import httpx
    with patch("httpx.post", side_effect=httpx.ConnectError("refused")):
        daemon.stop()

    mock_proc.terminate.assert_called_once()
    assert daemon._managed_process is None
