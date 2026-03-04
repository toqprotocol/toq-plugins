"""Tests for toq_common.binary module."""

import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from toq_common import binary


def test_detect_platform_darwin_arm():
    with patch.object(platform, "system", return_value="Darwin"), \
         patch.object(platform, "machine", return_value="arm64"):
        assert binary.detect_platform() == "darwin-aarch64"


def test_detect_platform_linux_x86():
    with patch.object(platform, "system", return_value="Linux"), \
         patch.object(platform, "machine", return_value="x86_64"):
        assert binary.detect_platform() == "linux-x86_64"


def test_detect_platform_unsupported_os():
    with patch.object(platform, "system", return_value="Windows"), \
         patch.object(platform, "machine", return_value="x86_64"):
        with pytest.raises(binary.UnsupportedPlatformError, match="Unsupported OS"):
            binary.detect_platform()


def test_detect_platform_unsupported_arch():
    with patch.object(platform, "system", return_value="Linux"), \
         patch.object(platform, "machine", return_value="mips"):
        with pytest.raises(binary.UnsupportedPlatformError, match="Unsupported architecture"):
            binary.detect_platform()


def test_binary_path():
    path = binary.binary_path()
    assert path == Path.home() / ".toq" / "bin" / "toq"


def test_bundled_binary_path_raises_without_set():
    binary._bundled_bin_dir = None
    with pytest.raises(RuntimeError, match="No bundled binary directory"):
        binary.bundled_binary_path()


def test_set_bundled_bin_dir():
    test_path = Path("/tmp/test-bin")
    binary.set_bundled_bin_dir(test_path)
    assert binary._bundled_bin_dir == test_path
    binary._bundled_bin_dir = None  # cleanup
