"""Listener that feeds incoming toq messages into a CrewAI crew."""

import asyncio
import logging

from toq import AsyncClient

logger = logging.getLogger("toq_crewai.listener")


async def listen(client: AsyncClient, crew: object) -> None:
    """Listen for incoming toq messages and process them with the crew.

    Runs indefinitely until cancelled. Each message is processed
    independently; errors on one message don't crash the loop.
    """
    async for msg in client.messages():
        try:
            text = msg.body.get("text", "") if isinstance(msg.body, dict) else str(msg.body)

            result = await asyncio.to_thread(
                crew.kickoff,
                inputs={
                    "message": text,
                    "sender": msg.sender,
                    "thread_id": msg.thread_id or "",
                },
            )

            await msg.reply(str(result))
        except Exception:
            logger.exception("Error processing message from %s", msg.sender)
