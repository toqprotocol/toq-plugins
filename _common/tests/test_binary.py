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


def test_detect_platform_darwin_x86():
    with patch.object(platform, "system", return_value="Darwin"), \
         patch.object(platform, "machine", return_value="x86_64"):
        assert binary.detect_platform() == "darwin-x86_64"


def test_detect_platform_linux_aarch64():
    with patch.object(platform, "system", return_value="Linux"), \
         patch.object(platform, "machine", return_value="aarch64"):
        assert binary.detect_platform() == "linux-aarch64"


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


def test_bundled_binary_path_returns_correct_after_set():
    test_path = Path("/tmp/test-bin")
    binary.set_bundled_bin_dir(test_path)
    with patch.object(binary, "detect_platform", return_value="darwin-aarch64"):
        result = binary.bundled_binary_path()
        assert result == test_path / "darwin-aarch64" / "toq"
    binary._bundled_bin_dir = None  # cleanup


def test_ensure_extracted_copies_when_target_missing(tmp_path):
    bundled_dir = tmp_path / "bundled" / "darwin-aarch64"
    bundled_dir.mkdir(parents=True)
    bundled_bin = bundled_dir / "toq"
    bundled_bin.write_text("#!/bin/sh\necho toq 0.1.0")
    bundled_bin.chmod(0o755)

    target_dir = tmp_path / "bin"
    target = target_dir / "toq"

    binary.set_bundled_bin_dir(tmp_path / "bundled")

    with patch.object(binary, "BIN_DIR", target_dir), \
         patch.object(binary, "detect_platform", return_value="darwin-aarch64"):
        result = binary.ensure_extracted()
        assert result == target
        assert target.exists()

    binary._bundled_bin_dir = None


def test_ensure_extracted_raises_if_bundled_missing(tmp_path):
    bundled_dir = tmp_path / "bundled"
    bundled_dir.mkdir()
    binary.set_bundled_bin_dir(bundled_dir)

    with patch.object(binary, "BIN_DIR", tmp_path / "bin"), \
         patch.object(binary, "detect_platform", return_value="darwin-aarch64"):
        with pytest.raises(FileNotFoundError, match="No bundled toq binary"):
            binary.ensure_extracted()

    binary._bundled_bin_dir = None


def test_ensure_extracted_skips_if_versions_match(tmp_path):
    import shutil

    bundled_dir = tmp_path / "bundled" / "darwin-aarch64"
    bundled_dir.mkdir(parents=True)
    bundled_bin = bundled_dir / "toq"
    bundled_bin.write_text("fake")
    bundled_bin.chmod(0o755)

    target_dir = tmp_path / "bin"
    target_dir.mkdir()
    target = target_dir / "toq"
    target.write_text("fake")
    target.chmod(0o755)

    binary.set_bundled_bin_dir(tmp_path / "bundled")

    with patch.object(binary, "BIN_DIR", target_dir), \
         patch.object(binary, "detect_platform", return_value="darwin-aarch64"), \
         patch.object(binary, "_get_version", return_value="toq 0.1.0"):
        result = binary.ensure_extracted()
        assert result == target

    binary._bundled_bin_dir = None
