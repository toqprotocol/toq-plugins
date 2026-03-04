"""toq protocol plugin for CrewAI."""

from pathlib import Path

import toq
from toq_common import binary, daemon, setup

from toq_crewai.listener import listen
from toq_crewai.tools import make_tools

binary.set_bundled_bin_dir(Path(__file__).parent / "bin")


class ToqClient:
    """Wraps a toq AsyncClient with CrewAI tools."""

    def __init__(self, async_client: toq.AsyncClient) -> None:
        self._client = async_client

    def tools(self) -> list:
        """Return CrewAI tools bound to this client."""
        return make_tools(self._client)

    @property
    def sdk(self) -> toq.AsyncClient:
        """Access the underlying toq SDK client."""
        return self._client


def connect(
    *,
    agent_name: str | None = None,
    connection_mode: str | None = None,
    adapter: str | None = None,
    api_port: int | None = None,
) -> ToqClient:
    """Ensure toq is extracted, configured, and running. Returns a ToqClient."""
    binary.ensure_extracted()
    setup.ensure_configured(
        agent_name=agent_name,
        connection_mode=connection_mode,
        adapter=adapter,
    )
    port = api_port or daemon.DEFAULT_API_PORT
    if api_port is None:
        daemon.ensure_running(api_port=port)
    return ToqClient(toq.connect_async(f"http://127.0.0.1:{port}"))


__all__ = ["connect", "listen", "ToqClient"]
