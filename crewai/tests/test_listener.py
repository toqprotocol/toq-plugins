"""Tests for toq_crewai listener."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

# TODO: Remove this mock once toq SDK is published to PyPI (roadmap item 9)
mock_toq = MagicMock()
mock_toq.AsyncClient = MagicMock
sys.modules["toq"] = mock_toq

import pytest
from toq_crewai.listener import listen


class FakeMessage:
    def __init__(self, sender, body, thread_id=None):
        self.sender = sender
        self.body = body
        self.thread_id = thread_id
        self.reply = AsyncMock()


async def fake_messages(msgs):
    for m in msgs:
        yield m


@pytest.mark.asyncio
async def test_listen_processes_message():
    msg = FakeMessage("toq://remote/bot", {"text": "hello"})
    client = AsyncMock()
    client.messages = lambda: fake_messages([msg])

    crew = MagicMock()
    crew.kickoff = MagicMock(return_value="crew result")

    await listen(client, crew)

    crew.kickoff.assert_called_once()
    msg.reply.assert_awaited_once_with("crew result")


@pytest.mark.asyncio
async def test_listen_continues_on_error():
    msg1 = FakeMessage("toq://remote/bot", {"text": "first"})
    msg2 = FakeMessage("toq://remote/bot", {"text": "second"})
    client = AsyncMock()
    client.messages = lambda: fake_messages([msg1, msg2])

    crew = MagicMock()
    crew.kickoff = MagicMock(side_effect=[RuntimeError("boom"), "ok"])

    await listen(client, crew)

    assert crew.kickoff.call_count == 2
    msg2.reply.assert_awaited_once()
