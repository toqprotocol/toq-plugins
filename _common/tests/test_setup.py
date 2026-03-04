"""Tests for toq_common.setup module."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from toq_common import setup


def test_is_configured_true(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text("[agent]")
    with patch.object(setup, "CONFIG_PATH", config):
        assert setup.is_configured() is True


def test_is_configured_false(tmp_path):
    with patch.object(setup, "CONFIG_PATH", tmp_path / "missing.toml"):
        assert setup.is_configured() is False


def test_ensure_configured_noop_when_configured(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text("[agent]")
    with patch.object(setup, "CONFIG_PATH", config), \
         patch("subprocess.run") as mock_run:
        setup.ensure_configured()
        mock_run.assert_not_called()


def test_ensure_configured_runs_setup(tmp_path):
    with patch.object(setup, "CONFIG_PATH", tmp_path / "missing.toml"), \
         patch("toq_common.setup.binary_path", return_value=Path("/usr/bin/toq")), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        setup.ensure_configured(agent_name="bot", connection_mode="open")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "--agent-name=bot" in cmd
        assert "--connection-mode=open" in cmd


def test_ensure_configured_raises_on_failure(tmp_path):
    import pytest
    with patch.object(setup, "CONFIG_PATH", tmp_path / "missing.toml"), \
         patch("toq_common.setup.binary_path", return_value=Path("/usr/bin/toq")), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="setup failed")
        with pytest.raises(RuntimeError, match="toq setup failed"):
            setup.ensure_configured()


def test_ensure_configured_uses_defaults(tmp_path):
    with patch.object(setup, "CONFIG_PATH", tmp_path / "missing.toml"), \
         patch("toq_common.setup.binary_path", return_value=Path("/usr/bin/toq")), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        setup.ensure_configured()
        cmd = mock_run.call_args[0][0]
        assert "--agent-name=agent" in cmd
        assert "--connection-mode=approval" in cmd
        assert "--adapter=http" in cmd
