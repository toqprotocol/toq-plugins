"""Binary bundling and extraction for the toq daemon."""

import platform
import shutil
import stat
import subprocess
from pathlib import Path

TOQ_HOME = Path.home() / ".toq"
BIN_DIR = TOQ_HOME / "bin"
BINARY_NAME = "toq"
VERSION_CHECK_TIMEOUT_SECONDS = 5

# Set by each plugin to point to its bundled binary directory.
# e.g. Path(__file__).parent / "bin"
_bundled_bin_dir: Path | None = None


class UnsupportedPlatformError(RuntimeError):
    """Raised when the current platform has no bundled binary."""


def detect_platform() -> str:
    """Return platform tag like 'darwin-aarch64' or 'linux-x86_64'."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }

    if system not in ("darwin", "linux"):
        raise UnsupportedPlatformError(f"Unsupported OS: {system}")

    arch = arch_map.get(machine)
    if arch is None:
        raise UnsupportedPlatformError(f"Unsupported architecture: {machine}")

    return f"{system}-{arch}"


def binary_path() -> Path:
    """Path where the extracted binary lives."""
    return BIN_DIR / BINARY_NAME


def bundled_binary_path() -> Path:
    """Path to the binary inside the installed plugin wheel."""
    if _bundled_bin_dir is None:
        raise RuntimeError(
            "No bundled binary directory configured. "
            "Call toq_plugins_common.binary.set_bundled_bin_dir() first"
        )
    return _bundled_bin_dir / detect_platform() / BINARY_NAME


def set_bundled_bin_dir(path: Path) -> None:
    """Set the directory containing platform-specific bundled binaries."""
    global _bundled_bin_dir
    _bundled_bin_dir = path


def _get_version(path: Path) -> str | None:
    """Run the binary and return its version string, or None on failure."""
    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=VERSION_CHECK_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return None


def ensure_extracted() -> Path:
    """Extract the bundled binary to ~/.toq/bin/toq if needed.

    Skips extraction if the binary exists and versions match.
    Returns the path to the binary.
    """
    target = binary_path()
    bundled = bundled_binary_path()

    if not bundled.exists():
        raise FileNotFoundError(
            f"No bundled toq binary for {detect_platform()}"
        )

    if target.exists():
        target_ver = _get_version(target)
        bundled_ver = _get_version(bundled)
        if target_ver and bundled_ver and target_ver == bundled_ver:
            return target

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundled, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return target
