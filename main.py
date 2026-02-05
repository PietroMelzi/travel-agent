import asyncio
import json
import logging
import weave
from collections import deque
from utils import build_message_with_history, load_agent
from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered

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
        manager_agent = load_agent()
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
