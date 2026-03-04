"""Tests for toq_langchain listener."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

# TODO: Remove this mock once toq SDK is published to PyPI (roadmap item 9)
mock_toq = MagicMock()
mock_toq.AsyncClient = MagicMock
sys.modules["toq"] = mock_toq

import pytest
from toq_langchain.listener import listen


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

    agent = AsyncMock()
    agent.ainvoke = AsyncMock(return_value={"output": "reply"})

    await listen(client, agent)

    agent.ainvoke.assert_awaited_once()
    msg.reply.assert_awaited_once_with("reply")


@pytest.mark.asyncio
async def test_listen_handles_dict_body():
    msg = FakeMessage("toq://remote/bot", {"text": "hello world"})
    client = AsyncMock()
    client.messages = lambda: fake_messages([msg])

    agent = AsyncMock()
    agent.ainvoke = AsyncMock(return_value="ok")

    await listen(client, agent)

    call_args = agent.ainvoke.call_args[0][0]
    assert "hello world" in call_args["messages"][0]["content"]


@pytest.mark.asyncio
async def test_listen_handles_non_dict_body():
    msg = FakeMessage("toq://remote/bot", "raw string")
    client = AsyncMock()
    client.messages = lambda: fake_messages([msg])

    agent = AsyncMock()
    agent.ainvoke = AsyncMock(return_value="ok")

    await listen(client, agent)

    call_args = agent.ainvoke.call_args[0][0]
    assert "raw string" in call_args["messages"][0]["content"]


@pytest.mark.asyncio
async def test_listen_continues_on_error():
    msg1 = FakeMessage("toq://remote/bot", {"text": "first"})
    msg2 = FakeMessage("toq://remote/bot", {"text": "second"})
    client = AsyncMock()
    client.messages = lambda: fake_messages([msg1, msg2])

    agent = AsyncMock()
    agent.ainvoke = AsyncMock(side_effect=[RuntimeError("boom"), {"output": "ok"}])

    await listen(client, agent)

    assert agent.ainvoke.await_count == 2
    msg2.reply.assert_awaited_once()
