"""Tests for toq_crewai tools."""

import sys
from unittest.mock import AsyncMock, MagicMock

# TODO: Remove this mock once toq SDK is published to PyPI (roadmap item 9)
mock_toq = MagicMock()
mock_toq.AsyncClient = MagicMock
sys.modules["toq"] = mock_toq

from toq_crewai.tools import make_tools


def mock_client():
    client = AsyncMock()
    client.send = AsyncMock(return_value={"status": "delivered", "thread_id": "t1"})
    client.send_streaming = AsyncMock(return_value={"status": "delivered", "thread_id": "t2"})
    client.peers = AsyncMock(return_value=[])
    client.status = AsyncMock(return_value={"status": "running"})
    client.block = AsyncMock()
    client.unblock = AsyncMock()
    client.approvals = AsyncMock(return_value=[])
    client.approve = AsyncMock()
    client.deny = AsyncMock()
    return client


def test_make_tools_returns_9():
    tools = make_tools(mock_client())
    assert len(tools) == 9


def test_make_tools_names():
    tools = make_tools(mock_client())
    names = {t.name for t in tools}
    assert names == {
        "toq_send", "toq_send_stream", "toq_peers", "toq_status",
        "toq_block", "toq_unblock", "toq_approvals", "toq_approve", "toq_deny",
    }


def test_toq_send():
    client = mock_client()
    tools = make_tools(client)
    send = next(t for t in tools if t.name == "toq_send")
    result = send.run("toq://host/agent", "hi")
    assert "delivered" in result
    client.send.assert_awaited_once()


def test_toq_peers_empty():
    client = mock_client()
    tools = make_tools(client)
    peers = next(t for t in tools if t.name == "toq_peers")
    result = peers.run()
    assert result == "No peers"


def test_toq_block():
    client = mock_client()
    tools = make_tools(client)
    block = next(t for t in tools if t.name == "toq_block")
    result = block.run("ed25519:abc")
    assert "Blocked" in result
    client.block.assert_awaited_once_with("ed25519:abc")


def test_toq_approvals_empty():
    client = mock_client()
    tools = make_tools(client)
    approvals = next(t for t in tools if t.name == "toq_approvals")
    result = approvals.run()
    assert result == "No pending approvals"


def test_toq_approve():
    client = mock_client()
    tools = make_tools(client)
    approve = next(t for t in tools if t.name == "toq_approve")
    result = approve.run("key1")
    assert "Approved" in result
    client.approve.assert_awaited_once_with("key1")
