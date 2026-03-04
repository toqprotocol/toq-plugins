"""LangChain tools for the toq protocol."""

import asyncio
import json

from langchain_core.tools import tool

from toq import AsyncClient


def make_tools(client: AsyncClient) -> list:
    """Create LangChain tools bound to a toq client."""

    @tool
    def toq_send(address: str, message: str) -> str:
        """Send a message to another toq agent. Returns delivery confirmation.
        Replies arrive via the listener, not as a return value.

        Args:
            address: toq address (e.g. toq://example.com/agent-name)
            message: message text to send
        """
        resp = asyncio.run(client.send(address, message))
        return f"Sent to {address} (status: {resp.get('status', 'unknown')}, thread: {resp.get('thread_id', 'unknown')})"

    @tool
    def toq_send_stream(address: str, message: str) -> str:
        """Send a streaming message to another toq agent. Returns delivery confirmation.

        Args:
            address: toq address (e.g. toq://example.com/agent-name)
            message: message text to send
        """
        resp = asyncio.run(client.send_streaming(address, message))
        return f"Streaming sent to {address} (status: {resp.get('status', 'unknown')}, thread: {resp.get('thread_id', 'unknown')})"

    @tool
    def toq_peers() -> str:
        """List all known toq peers with their connection status."""
        peers = asyncio.run(client.peers())
        if not peers:
            return "No peers"
        lines = []
        for p in peers:
            addr = p.get("address", "unknown")
            status = p.get("status", "unknown")
            key = p.get("public_key", "unknown")
            lines.append(f"{addr} - {status} (key: {key})")
        return "\n".join(lines)

    @tool
    def toq_status() -> str:
        """Check the toq daemon status."""
        s = asyncio.run(client.status())
        return json.dumps(s)

    @tool
    def toq_block(public_key: str) -> str:
        """Block a toq peer by their public key.

        Args:
            public_key: the peer's Ed25519 public key
        """
        asyncio.run(client.block(public_key))
        return f"Blocked {public_key}"

    @tool
    def toq_unblock(public_key: str) -> str:
        """Unblock a previously blocked toq peer.

        Args:
            public_key: the peer's Ed25519 public key
        """
        asyncio.run(client.unblock(public_key))
        return f"Unblocked {public_key}"

    @tool
    def toq_approvals() -> str:
        """List pending connection approval requests."""
        items = asyncio.run(client.approvals())
        if not items:
            return "No pending approvals"
        lines = []
        for a in items:
            lines.append(f"{a.get('id', '?')} from {a.get('address', 'unknown')}")
        return "\n".join(lines)

    @tool
    def toq_approve(approval_id: str) -> str:
        """Approve a pending connection request.

        Args:
            approval_id: the approval request ID
        """
        asyncio.run(client.approve(approval_id))
        return f"Approved {approval_id}"

    @tool
    def toq_deny(approval_id: str) -> str:
        """Deny a pending connection request.

        Args:
            approval_id: the approval request ID
        """
        asyncio.run(client.deny(approval_id))
        return f"Denied {approval_id}"

    return [
        toq_send, toq_send_stream, toq_peers, toq_status,
        toq_block, toq_unblock, toq_approvals, toq_approve, toq_deny,
    ]
