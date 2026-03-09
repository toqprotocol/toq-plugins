"""Tests for toq_crewai tools."""

import sys
from unittest.mock import MagicMock

# TODO: Remove this mock once toq SDK is published to PyPI (roadmap item 9)
mock_toq = MagicMock()
mock_toq.AsyncClient = MagicMock
sys.modules["toq"] = mock_toq

from toq_crewai.tools import make_tools


def mock_client():
    client = MagicMock()
    client.send = MagicMock(return_value={"status": "delivered", "thread_id": "t1"})
    client.stream_start = MagicMock(return_value={"stream_id": "s1", "thread_id": "t2"})
    client.stream_chunk = MagicMock(return_value={"chunk_id": "c1"})
    client.stream_end = MagicMock(return_value={"chunk_id": "e1"})
    client.peers = MagicMock(return_value=[])
    client.status = MagicMock(return_value={"status": "running"})
    client.block = MagicMock()
    client.unblock = MagicMock()
    client.approvals = MagicMock(return_value=[])
    client.approve = MagicMock()
    client.deny = MagicMock()
    client.revoke = MagicMock()
    client.history = MagicMock(return_value=[])
    client.permissions = MagicMock(return_value={"approved": [], "blocked": []})
    client.ping = MagicMock(return_value={"agent_name": "test", "address": "toq://h/a", "public_key": "k", "reachable": True})
    return client


def test_make_tools_returns_13():
    tools = make_tools(mock_client())
    assert len(tools) == 13


def test_make_tools_names():
    tools = make_tools(mock_client())
    names = {t.name for t in tools}
    assert names == {
        "toq_send", "toq_send_stream", "toq_peers", "toq_status",
        "toq_block", "toq_unblock", "toq_approvals", "toq_approve", "toq_deny",
        "toq_revoke", "toq_history", "toq_permissions", "toq_ping",
    }


def test_toq_send():
    client = mock_client()
    tools = make_tools(client)
    send = next(t for t in tools if t.name == "toq_send")
    result = send.run("toq://host/agent", "hi")
    assert "delivered" in result
    client.send.assert_called_once()


def test_toq_send_stream():
    client = mock_client()
    tools = make_tools(client)
    send = next(t for t in tools if t.name == "toq_send_stream")
    result = send.run("toq://host/agent", "hi")
    assert "Streamed" in result
    client.stream_start.assert_called_once()
    client.stream_chunk.assert_called()
    client.stream_end.assert_called_once()


def test_toq_peers_empty():
    client = mock_client()
    tools = make_tools(client)
    peers = next(t for t in tools if t.name == "toq_peers")
    result = peers.run()
    assert result == "No peers"


def test_toq_peers_with_data():
    client = mock_client()
    client.peers = MagicMock(return_value=[
        {"address": "toq://a/one", "status": "connected", "public_key": "key1"},
    ])
    tools = make_tools(client)
    peers = next(t for t in tools if t.name == "toq_peers")
    result = peers.run()
    assert "toq://a/one" in result
    assert "connected" in result


def test_toq_status():
    client = mock_client()
    tools = make_tools(client)
    status = next(t for t in tools if t.name == "toq_status")
    result = status.run()
    assert "running" in result


def test_toq_block():
    client = mock_client()
    tools = make_tools(client)
    block = next(t for t in tools if t.name == "toq_block")
    result = block.run("ed25519:abc")
    assert "Blocked" in result
    client.block.assert_called_once_with(key="ed25519:abc")


def test_toq_block_by_address():
    client = mock_client()
    tools = make_tools(client)
    block = next(t for t in tools if t.name == "toq_block")
    result = block.run("toq://host/*")
    assert "Blocked" in result
    client.block.assert_called_once_with(from_addr="toq://host/*")


def test_toq_unblock():
    client = mock_client()
    tools = make_tools(client)
    unblock = next(t for t in tools if t.name == "toq_unblock")
    result = unblock.run("ed25519:abc")
    assert "Unblocked" in result
    client.unblock.assert_called_once_with(key="ed25519:abc")


def test_toq_approvals_empty():
    client = mock_client()
    tools = make_tools(client)
    approvals = next(t for t in tools if t.name == "toq_approvals")
    result = approvals.run()
    assert result == "No pending approvals"


def test_toq_approvals_with_data():
    client = mock_client()
    client.approvals = MagicMock(return_value=[
        {"id": "key1", "address": "toq://a/one"},
    ])
    tools = make_tools(client)
    approvals = next(t for t in tools if t.name == "toq_approvals")
    result = approvals.run()
    assert "key1" in result
    assert "toq://a/one" in result


def test_toq_approve():
    client = mock_client()
    tools = make_tools(client)
    approve = next(t for t in tools if t.name == "toq_approve")
    result = approve.run("toq://host/*")
    assert "Approved" in result
    client.approve.assert_called_once_with(from_addr="toq://host/*")


def test_toq_deny():
    client = mock_client()
    tools = make_tools(client)
    deny = next(t for t in tools if t.name == "toq_deny")
    result = deny.run("key1")
    assert "Denied" in result
    client.deny.assert_called_once_with("key1")


def test_toq_permissions():
    client = mock_client()
    tools = make_tools(client)
    perms = next(t for t in tools if t.name == "toq_permissions")
    result = perms.run()
    assert "Approved:" in result
    assert "(none)" in result


def test_toq_ping():
    client = mock_client()
    tools = make_tools(client)
    ping = next(t for t in tools if t.name == "toq_ping")
    result = ping.run("toq://h/a")
    assert "reachable" in result
    assert "test" in result
    client.ping.assert_called_once_with("toq://h/a")
