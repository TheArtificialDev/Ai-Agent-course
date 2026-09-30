import os
from pathlib import Path
from secrets import compare_digest

import chainlit as cl
import dotenv
from agents import InputGuardrailTripwireTriggered, Runner, SQLiteSession
from nutrition_agent import exa_search_mcp, nutrition_agent
from openai.types.responses import ResponseTextDeltaEvent

dotenv.load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@cl.on_chat_start
async def on_chat_start():
    session = SQLiteSession(
        os.getenv("CHATBOT_SESSION_DB_PATH", "conversation_history")
    )
    cl.user_session.set("agent_session", session)
    if exa_search_mcp is not None:
        await exa_search_mcp.connect()
    else:
        await cl.Message(
            content="Web search is unavailable because EXA_API_KEY is not configured."
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    session = cl.user_session.get("agent_session")

    result = Runner.run_streamed(
        nutrition_agent,
        message.content,
        session=session,
    )

    msg = cl.Message(content="")
    async for event in result.stream_events():
        # Stream final message text to screen
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            await msg.stream_token(token=event.data.delta)
            print(event.data.delta, end="", flush=True)

        elif (
            event.type == "raw_response_event"
            and hasattr(event.data, "item")
            and hasattr(event.data.item, "type")
            and event.data.item.type == "function_call"
            and len(event.data.item.arguments) > 0
        ):
            with cl.Step(name=f"{event.data.item.name}", type="tool") as step:
                step.input = event.data.item.arguments
                print(
                    f"\nTool call: {event.data.item.name} with args: "
                    f"{event.data.item.arguments}"
                )

    await msg.update()


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    configured_username = os.getenv("CHAINLIT_USERNAME")
    configured_password = os.getenv("CHAINLIT_PASSWORD")

    if configured_username and configured_password and compare_digest(
        username, configured_username
    ) and compare_digest(password, configured_password):
        return cl.User(
            identifier=username,
            metadata={"role": "student", "provider": "credentials"},
        )

    return None
