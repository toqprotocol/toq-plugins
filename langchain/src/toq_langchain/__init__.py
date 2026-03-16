"""toq protocol plugin for LangChain."""

from pathlib import Path

import toq
from toq_plugins_common import binary, daemon, setup

from toq_langchain.listener import listen
from toq_langchain.tools import make_tools

# Point toq_plugins_common at this plugin's bundled binaries.
binary.set_bundled_bin_dir(Path(__file__).parent / "bin")


class ToqClient:
    """Wraps a toq AsyncClient with LangChain tools."""

    def __init__(self, client: toq.Client) -> None:
        self._client = client

    def tools(self) -> list:
        """Return LangChain tools bound to this client."""
        return make_tools(self._client)

    @property
    def sdk(self) -> toq.Client:
        """Access the underlying toq SDK client."""
        return self._client


def connect(
    *,
    agent_name: str | None = None,
    connection_mode: str | None = None,
    adapter: str | None = None,
    port: int | None = None,
) -> ToqClient:
    """Ensure toq is extracted, configured, and running. Returns a ToqClient."""
    binary.ensure_extracted()
    setup.ensure_configured(
        agent_name=agent_name,
        connection_mode=connection_mode,
        adapter=adapter,
    )
    auto_start = port is None
    port = port or daemon.DEFAULT_PORT
    if auto_start:
        daemon.ensure_running(port=port)
    return ToqClient(toq.connect(f"http://127.0.0.1:{port}"))


__all__ = ["connect", "listen", "ToqClient"]
