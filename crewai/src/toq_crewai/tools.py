"""CrewAI tools for the toq protocol."""

import json

from crewai.tools import tool

from toq import Client


def make_tools(client: Client) -> list:
    """Create CrewAI tools bound to a toq client."""

    @tool("toq_send")
    def toq_send(address: str, message: str) -> str:
        """Send a message to another toq agent. Returns delivery confirmation.
        Replies arrive via the listener, not as a return value.

        Args:
            address: toq address (e.g. toq://example.com/agent-name)
            message: message text to send
        """
        resp = client.send(address, message)
        return f"Sent to {address} (status: {resp.get('status', 'unknown')}, thread: {resp.get('thread_id', 'unknown')})"

    @tool("toq_send_stream")
    def toq_send_stream(address: str, message: str) -> str:
        """Send a streaming message to another toq agent. Delivers text
        word-by-word for real-time display on the receiver's side.

        Args:
            address: toq address (e.g. toq://example.com/agent-name)
            message: message text to send
        """
        s = client.stream_start(address)
        sid = s["stream_id"]
        for word in message.split():
            client.stream_chunk(sid, word + " ")
        client.stream_end(sid)
        return f"Streamed to {address} (thread: {s.get('thread_id', 'unknown')})"

    @tool("toq_peers")
    def toq_peers() -> str:
        """List all known toq peers with their connection status."""
        peers = client.peers()
        if not peers:
            return "No peers"
        lines = []
        for p in peers:
            addr = p.get("address", "unknown")
            status = p.get("status", "unknown")
            key = p.get("public_key", "unknown")
            lines.append(f"{addr} - {status} (key: {key})")
        return "\n".join(lines)

    @tool("toq_status")
    def toq_status() -> str:
        """Check the toq daemon status."""
        s = client.status()
        return json.dumps(s)

    @tool("toq_block")
    def toq_block(public_key: str) -> str:
        """Block a toq peer by their public key.

        Args:
            public_key: the peer's Ed25519 public key
        """
        client.block(public_key)
        return f"Blocked {public_key}"

    @tool("toq_unblock")
    def toq_unblock(public_key: str) -> str:
        """Unblock a previously blocked toq peer.

        Args:
            public_key: the peer's Ed25519 public key
        """
        client.unblock(public_key)
        return f"Unblocked {public_key}"

    @tool("toq_approvals")
    def toq_approvals() -> str:
        """List pending connection approval requests."""
        items = client.approvals()
        if not items:
            return "No pending approvals"
        lines = []
        for a in items:
            lines.append(f"{a.get('id', '?')} from {a.get('address', 'unknown')}")
        return "\n".join(lines)

    @tool("toq_approve")
    def toq_approve(approval_id: str) -> str:
        """Approve a pending connection request.

        Args:
            approval_id: the approval request ID
        """
        client.approve(approval_id)
        return f"Approved {approval_id}"

    @tool("toq_deny")
    def toq_deny(approval_id: str) -> str:
        """Deny a pending connection request.

        Args:
            approval_id: the approval request ID
        """
        client.deny(approval_id)
        return f"Denied {approval_id}"

    @tool("toq_revoke")
    def toq_revoke(approval_id: str) -> str:
        """Revoke a previously approved agent. Removes from allowed list without blocking.

        Args:
            approval_id: the encoded public key of the agent to revoke
        """
        client.revoke(approval_id)
        return f"Revoked {approval_id}"

    @tool("toq_history")
    def toq_history(limit: int = 20, from_addr: str = "") -> str:
        """Query received message history.

        Args:
            limit: max messages to return (default 20)
            from_addr: filter by sender address substring (optional)
        """
        msgs = client.history(limit=limit, from_addr=from_addr or None)
        if not msgs:
            return "No messages"
        lines = []
        for m in msgs:
            sender = m.get("from", "unknown")
            text = m.get("body", {}).get("text", "")
            ts = m.get("timestamp", "")
            lines.append(f"[{ts}] {sender}: {text}")
        return "\n".join(lines)

    return [
        toq_send, toq_send_stream, toq_peers, toq_status,
        toq_block, toq_unblock, toq_approvals, toq_approve, toq_deny,
        toq_revoke, toq_history,
    ]
