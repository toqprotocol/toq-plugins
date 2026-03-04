"""Programmatic setup for the toq daemon."""

import subprocess

from toq_common.binary import TOQ_HOME, binary_path

CONFIG_PATH = TOQ_HOME / "config.toml"

DEFAULT_AGENT_NAME = "agent"
DEFAULT_CONNECTION_MODE = "approval"
DEFAULT_ADAPTER = "http"
SETUP_TIMEOUT_SECONDS = 30


def is_configured() -> bool:
    """Return True if toq setup has been completed."""
    return CONFIG_PATH.exists()


def ensure_configured(
    *,
    agent_name: str | None = None,
    connection_mode: str | None = None,
    adapter: str | None = None,
) -> None:
    """Run toq setup --non-interactive if not already configured.

    If config already exists, this is a no-op. Parameters only apply
    to fresh setup.
    """
    if is_configured():
        return

    cmd = [
        str(binary_path()),
        "setup",
        "--non-interactive",
        f"--agent-name={agent_name or DEFAULT_AGENT_NAME}",
        f"--connection-mode={connection_mode or DEFAULT_CONNECTION_MODE}",
        f"--adapter={adapter or DEFAULT_ADAPTER}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=SETUP_TIMEOUT_SECONDS)
    if result.returncode != 0:
        raise RuntimeError(f"toq setup failed: {result.stderr.strip()}")
