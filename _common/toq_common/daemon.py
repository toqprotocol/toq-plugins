"""Daemon lifecycle management for the toq daemon."""

import atexit
import logging
import subprocess
import time

import httpx

from toq_common.binary import TOQ_HOME, binary_path

logger = logging.getLogger("toq_common.daemon")

DEFAULT_PORT = 9009
HEALTH_TIMEOUT_SECONDS = 10
HEALTH_POLL_INTERVAL_SECONDS = 0.25
HEALTH_CHECK_TIMEOUT_SECONDS = 2
SHUTDOWN_TIMEOUT_SECONDS = 5
KILL_TIMEOUT_SECONDS = 2
LOG_DIR = TOQ_HOME / "logs"

_managed_process: subprocess.Popen | None = None
_log_file = None
_atexit_registered = False


def _health_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/v1/health"


def _shutdown_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/v1/daemon/shutdown"


def is_running(port: int = DEFAULT_PORT) -> bool:
    """Check if the daemon is responding on the given port."""
    try:
        resp = httpx.get(_health_url(port), timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
        return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def start(port: int = DEFAULT_PORT) -> subprocess.Popen:
    """Start the toq daemon and wait for it to become healthy."""
    global _managed_process, _log_file, _atexit_registered

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _log_file = open(LOG_DIR / "daemon.log", "a")

    try:
        proc = subprocess.Popen(
            [str(binary_path()), "up", "--foreground"],
            stdout=_log_file,
            stderr=_log_file,
        )
    except Exception:
        _log_file.close()
        _log_file = None
        raise

    deadline = time.monotonic() + HEALTH_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            _log_file.close()
            _log_file = None
            raise RuntimeError(
                f"toq daemon exited immediately (code {proc.returncode})"
            )
        if is_running(port):
            _managed_process = proc
            if not _atexit_registered:
                atexit.register(_atexit_stop, port)
                _atexit_registered = True
            return proc
        time.sleep(HEALTH_POLL_INTERVAL_SECONDS)

    proc.terminate()
    _log_file.close()
    _log_file = None
    raise RuntimeError(
        f"toq daemon did not become healthy within {HEALTH_TIMEOUT_SECONDS}s"
    )


def stop(port: int = DEFAULT_PORT) -> None:
    """Stop the daemon if we started it."""
    global _managed_process, _log_file

    if _managed_process is None:
        return

    try:
        httpx.post(
            _shutdown_url(port),
            json={"graceful": True},
            timeout=SHUTDOWN_TIMEOUT_SECONDS,
        )
    except (httpx.ConnectError, httpx.TimeoutException):
        pass

    try:
        _managed_process.wait(timeout=SHUTDOWN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        _managed_process.terminate()
        try:
            _managed_process.wait(timeout=KILL_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            _managed_process.kill()

    _managed_process = None
    if _log_file is not None:
        _log_file.close()
        _log_file = None


def ensure_running(port: int = DEFAULT_PORT) -> None:
    """Start the daemon if it's not already running."""
    if not is_running(port):
        start(port)


def _atexit_stop(port: int) -> None:
    """Registered with atexit to clean up the daemon on exit."""
    try:
        stop(port)
    except Exception:
        pass
