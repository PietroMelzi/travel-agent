import asyncio
import json
import logging
from collections import deque
from datetime import datetime, timezone

import weave
from dotenv import load_dotenv
from agents import InputGuardrail, Runner
from agents.exceptions import InputGuardrailTripwireTriggered

from travel_agent.agent_setup import create_agent
from travel_agent.input_guardrails import travel_guardrail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

try:
    weave.init("travel-agent")
except Exception as e:
    log.warning("Weave init skipped: %s", e)


def build_message_with_history(history: deque[tuple[str, str]], new_input: str) -> str:
    """Build the message to send to the LLM: current time, last 5 turns, and the new user input."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    parts = [f"Current time: {now}"]
    if history:
        parts.append("\n\nPrevious conversation:")
        for user, assistant in history:
            parts.append(f"\n\nYou: {user}")
            parts.append(f"\nAssistant: {assistant}")
    parts.append(f"\n\nYou: {new_input}")
    return "".join(parts)


def _load_agent():
    load_dotenv()
    with open("travel_agent/agent_config.json", encoding="utf-8") as f:
        agent_config = json.load(f)
    manager_agent = create_agent(agent_config, "manager_agent")
    # manager_agent.input_guardrails = [InputGuardrail(guardrail_function=travel_guardrail)]
    return manager_agent


async def main(agent):
    print("Travel agent. Enter your question (or 'quit'/'exit' to stop).")
    history: deque[tuple[str, str]] = deque(maxlen=5)
    while True:
        try:
            user_input = (await asyncio.to_thread(input, "👤 You: ")).strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                log.info("User requested exit")
                break

            message = build_message_with_history(history, user_input)
            log.info("Running query with travel agent")
            result = await Runner.run(agent, message)
            log.info("Request completed successfully")
            history.append((user_input, result.final_output))
            print("🤖 Assistant:", result.final_output)
            print()
        except InputGuardrailTripwireTriggered as e:
            log.warning("Guardrail blocked this input: %s", e)
            print("This request was blocked: it doesn't seem to be about travel.\n")
        except Exception as e:
            log.exception("Agent run failed: %s", e)
            print(f"Error: {e}. Please try again.\n")


if __name__ == "__main__":
    try:
        manager_agent = _load_agent()
    except FileNotFoundError as e:
        log.error("Agent config file not found: %s", e)
        raise SystemExit(1) from e
    except json.JSONDecodeError as e:
        log.error("Invalid JSON in agent config: %s", e)
        raise SystemExit(1) from e
    except KeyError as e:
        log.error("Invalid agent config: missing key %s", e)
        raise SystemExit(1) from e

    asyncio.run(main(manager_agent))
