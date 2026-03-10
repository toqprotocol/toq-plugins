"""Tests for toq_langchain tools."""

import sys
from unittest.mock import MagicMock

# TODO: Remove this mock once toq SDK is published to PyPI (roadmap item 9)
mock_toq = MagicMock()
mock_toq.AsyncClient = MagicMock
sys.modules["toq"] = mock_toq

from toq_langchain.tools import make_tools


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
    client.handlers = MagicMock(return_value=[{"name": "h1", "command": "echo", "enabled": True, "active": 0}])
    client.add_handler = MagicMock(return_value={"status": "added", "name": "h1"})
    client.remove_handler = MagicMock(return_value={"status": "removed", "name": "h1"})
    client.stop_handler = MagicMock(return_value={"stopped": 2, "name": "h1"})
    return client


def test_make_tools_returns_17():
    tools = make_tools(mock_client())
    assert len(tools) == 17


def test_make_tools_names():
    tools = make_tools(mock_client())
    names = {t.name for t in tools}
    assert names == {
        "toq_send", "toq_send_stream", "toq_peers", "toq_status",
        "toq_block", "toq_unblock", "toq_approvals", "toq_approve", "toq_deny",
        "toq_revoke", "toq_history", "toq_permissions", "toq_ping",
        "toq_handlers", "toq_add_handler", "toq_remove_handler", "toq_stop_handler",
    }


def test_toq_send():
    client = mock_client()
    tools = make_tools(client)
    send = next(t for t in tools if t.name == "toq_send")
    result = send.invoke({"address": "toq://host/agent", "message": "hi"})
    assert "delivered" in result
    assert "toq://host/agent" in result
    client.send.assert_called_once_with("toq://host/agent", "hi")


def test_toq_send_stream():
    client = mock_client()
    tools = make_tools(client)
    send = next(t for t in tools if t.name == "toq_send_stream")
    result = send.invoke({"address": "toq://host/agent", "message": "hi"})
    assert "Streamed" in result
    client.stream_start.assert_called_once()
    client.stream_chunk.assert_called()
    client.stream_end.assert_called_once()


def test_toq_peers_empty():
    client = mock_client()
    tools = make_tools(client)
    peers = next(t for t in tools if t.name == "toq_peers")
    result = peers.invoke({})
    assert result == "No peers"


def test_toq_peers_with_data():
    client = mock_client()
    client.peers = MagicMock(return_value=[
        {"address": "toq://a/one", "status": "connected", "public_key": "key1"},
    ])
    tools = make_tools(client)
    peers = next(t for t in tools if t.name == "toq_peers")
    result = peers.invoke({})
    assert "toq://a/one" in result
    assert "connected" in result
    assert "key1" in result


def test_toq_status():
    client = mock_client()
    tools = make_tools(client)
    status = next(t for t in tools if t.name == "toq_status")
    result = status.invoke({})
    assert "running" in result


def test_toq_block():
    client = mock_client()
    tools = make_tools(client)
    block = next(t for t in tools if t.name == "toq_block")
    result = block.invoke({"identifier": "ed25519:abc"})
    assert "Blocked" in result
    client.block.assert_called_once_with(key="ed25519:abc")


def test_toq_block_by_address():
    client = mock_client()
    tools = make_tools(client)
    block = next(t for t in tools if t.name == "toq_block")
    result = block.invoke({"identifier": "toq://host/*"})
    assert "Blocked" in result
    client.block.assert_called_once_with(from_addr="toq://host/*")


def test_toq_unblock():
    client = mock_client()
    tools = make_tools(client)
    unblock = next(t for t in tools if t.name == "toq_unblock")
    result = unblock.invoke({"identifier": "ed25519:abc"})
    assert "Unblocked" in result
    client.unblock.assert_called_once_with(key="ed25519:abc")


def test_toq_approvals_empty():
    client = mock_client()
    tools = make_tools(client)
    approvals = next(t for t in tools if t.name == "toq_approvals")
    result = approvals.invoke({})
    assert result == "No pending approvals"


def test_toq_approvals_with_data():
    client = mock_client()
    client.approvals = MagicMock(return_value=[
        {"id": "key1", "address": "toq://a/one"},
    ])
    tools = make_tools(client)
    approvals = next(t for t in tools if t.name == "toq_approvals")
    result = approvals.invoke({})
    assert "key1" in result
    assert "toq://a/one" in result


def test_toq_approve():
    client = mock_client()
    tools = make_tools(client)
    approve = next(t for t in tools if t.name == "toq_approve")
    result = approve.invoke({"identifier": "toq://host/*"})
    assert "Approved" in result
    client.approve.assert_called_once_with(from_addr="toq://host/*")


def test_toq_deny():
    client = mock_client()
    tools = make_tools(client)
    deny = next(t for t in tools if t.name == "toq_deny")
    result = deny.invoke({"approval_id": "key1"})
    assert "Denied" in result
    client.deny.assert_called_once_with("key1")


def test_toq_permissions():
    client = mock_client()
    tools = make_tools(client)
    perms = next(t for t in tools if t.name == "toq_permissions")
    result = perms.invoke({})
    assert "Approved:" in result
    assert "(none)" in result


def test_toq_ping():
    client = mock_client()
    tools = make_tools(client)
    ping = next(t for t in tools if t.name == "toq_ping")
    result = ping.invoke({"address": "toq://h/a"})
    assert "reachable" in result
    assert "test" in result
    client.ping.assert_called_once_with("toq://h/a")


def test_toq_handlers():
    client = mock_client()
    tools = make_tools(client)
    t = next(t for t in tools if t.name == "toq_handlers")
    result = t.invoke({})
    assert "h1" in result
    client.handlers.assert_called_once()


def test_toq_add_handler():
    client = mock_client()
    tools = make_tools(client)
    t = next(t for t in tools if t.name == "toq_add_handler")
    result = t.invoke({"name": "test", "command": "echo hi", "filter_from": "toq://host/*"})
    assert "Added" in result
    client.add_handler.assert_called_once()


def test_toq_remove_handler():
    client = mock_client()
    tools = make_tools(client)
    t = next(t for t in tools if t.name == "toq_remove_handler")
    result = t.invoke({"name": "test"})
    assert "Removed" in result
    client.remove_handler.assert_called_once_with("test")


def test_toq_stop_handler():
    client = mock_client()
    tools = make_tools(client)
    t = next(t for t in tools if t.name == "toq_stop_handler")
    result = t.invoke({"name": "test"})
    assert "Stopped" in result
    client.stop_handler.assert_called_once_with("test")
