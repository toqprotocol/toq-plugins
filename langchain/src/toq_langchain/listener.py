"""Listener that feeds incoming toq messages into a LangChain agent."""

import logging

from toq import AsyncClient

logger = logging.getLogger("toq_langchain.listener")


async def listen(client: AsyncClient, agent: object) -> None:
    """Listen for incoming toq messages and process them with the agent.

    Runs indefinitely until cancelled. Each message is processed
    independently; errors on one message don't crash the loop.
    """
    async for msg in client.messages():
        try:
            sender = msg.sender
            text = msg.body.get("text", "") if isinstance(msg.body, dict) else str(msg.body)
            context = f"Incoming toq message from {sender}: {text}"

            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": context}]}
            )

            output = result.get("output", str(result)) if isinstance(result, dict) else str(result)
            await msg.reply(output)
        except Exception:
            logger.exception("Error processing message from %s", msg.sender)
