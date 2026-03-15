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
    def toq_block(identifier: str) -> str:
        """Block a toq peer by public key, address, or wildcard pattern.

        Args:
            identifier: public key, toq address (toq://host/name), or wildcard (toq://host/*, toq://*/name, toq://*)
        """
        if identifier.startswith("toq://"):
            client.block(from_addr=identifier)
        else:
            client.block(key=identifier)
        return f"Blocked {identifier}"

    @tool("toq_unblock")
    def toq_unblock(identifier: str) -> str:
        """Unblock a previously blocked toq peer.

        Args:
            identifier: public key, toq address, or wildcard pattern
        """
        if identifier.startswith("toq://"):
            client.unblock(from_addr=identifier)
        else:
            client.unblock(key=identifier)
        return f"Unblocked {identifier}"

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
    def toq_approve(identifier: str) -> str:
        """Approve a pending request by ID, or pre-approve by key/address/wildcard.

        Args:
            identifier: public key, toq address, or wildcard pattern
        """
        if identifier.startswith("toq://"):
            client.approve(from_addr=identifier)
        else:
            client.approve(key=identifier)
        return f"Approved {identifier}"

    @tool("toq_deny")
    def toq_deny(approval_id: str) -> str:
        """Deny a pending connection request.

        Args:
            approval_id: the approval request ID
        """
        client.deny(approval_id)
        return f"Denied {approval_id}"

    @tool("toq_revoke")
    def toq_revoke(identifier: str) -> str:
        """Revoke a previously approved agent or rule.

        Args:
            identifier: public key, toq address, or wildcard pattern
        """
        if identifier.startswith("toq://"):
            client.revoke(from_addr=identifier)
        else:
            client.revoke(key=identifier)
        return f"Revoked {identifier}"

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

    @tool("toq_permissions")
    def toq_permissions() -> str:
        """List all permission rules (approved and blocked)."""
        perms = client.permissions()
        lines = ["Approved:"]
        for r in perms.get("approved", []):
            lines.append(f"  {r.get('type', '?')}: {r.get('value', '?')}")
        if len(lines) == 1:
            lines.append("  (none)")
        lines.append("Blocked:")
        for r in perms.get("blocked", []):
            lines.append(f"  {r.get('type', '?')}: {r.get('value', '?')}")
        if lines[-1] == "Blocked:":
            lines.append("  (none)")
        return "\n".join(lines)

    @tool("toq_ping")
    def toq_ping(address: str) -> str:
        """Ping a remote agent to discover its public key.

        Args:
            address: toq address to ping (e.g. toq://host/name)
        """
        result = client.ping(address)
        key = result.get("public_key", "unknown")
        reachable = result.get("reachable", False)
        status = "reachable" if reachable else "unreachable"
        return f"Agent: {result.get('agent_name', '?')}\nAddress: {address}\nPublic key: {key}\nStatus: {status}"

    @tool("toq_handlers")
    def toq_handlers() -> str:
        """List all registered message handlers with their status."""
        items = client.handlers()
        if not items:
            return "No handlers registered"
        lines = []
        for h in items:
            enabled = "enabled" if h.get("enabled") else "disabled"
            active = h.get("active", 0)
            provider = h.get("provider", "")
            if provider:
                model = h.get("model", "?")
                lines.append(f"{h.get('name', '?')} - {enabled}, {active} active, provider: {provider}, model: {model}")
            else:
                lines.append(f"{h.get('name', '?')} - {enabled}, {active} active, command: {h.get('command', '?')}")
        return "\n".join(lines)

    @tool("toq_add_handler")
    def toq_add_handler(name: str, command: str, filter_from: str = "", filter_type: str = "") -> str:
        """Register a new message handler that runs when messages arrive.

        Args:
            name: unique handler name
            command: shell command to execute (receives message JSON on stdin)
            filter_from: optional sender address/wildcard filter (comma-separated for multiple)
            filter_type: optional message type filter (e.g. message.send)
        """
        kwargs: dict = {}
        if filter_from:
            kwargs["filter_from"] = [f.strip() for f in filter_from.split(",")]
        if filter_type:
            kwargs["filter_type"] = [t.strip() for t in filter_type.split(",")]
        client.add_handler(name, command, **kwargs)
        return f"Added handler '{name}'"

    @tool("toq_remove_handler")
    def toq_remove_handler(name: str) -> str:
        """Remove a registered message handler.

        Args:
            name: handler name to remove
        """
        client.remove_handler(name)
        return f"Removed handler '{name}'"

    @tool("toq_stop_handler")
    def toq_stop_handler(name: str) -> str:
        """Stop all running processes for a handler.

        Args:
            name: handler name
        """
        result = client.stop_handler(name)
        stopped = result.get("stopped", 0)
        return f"Stopped {stopped} process(es) for '{name}'"

    return [
        toq_send, toq_send_stream, toq_peers, toq_status,
        toq_block, toq_unblock, toq_approvals, toq_approve, toq_deny,
        toq_revoke, toq_history, toq_permissions, toq_ping,
        toq_handlers, toq_add_handler, toq_remove_handler, toq_stop_handler,
    ]
