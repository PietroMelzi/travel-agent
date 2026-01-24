import asyncio
import json
import logging
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

weave.init('travel-agent')


def _load_agent():
    load_dotenv()
    with open("travel_agent/agent_config.json", encoding="utf-8") as f:
        agent_config = json.load(f)
    manager_agent = create_agent(agent_config, "manager_agent")
    manager_agent.input_guardrails = [InputGuardrail(guardrail_function=travel_guardrail)]
    return manager_agent


async def main(agent):
    try:
        log.info("Running query with travel agent")
        result = await Runner.run(
            agent,
            "Can you find me a flight from Madrid to Barcelona for 10 days in March from the 1st of the month? Today is 20th Jan 2026.",
        )
        log.info("Request completed successfully")
        log.info("Final output: %s", result.final_output)
    except InputGuardrailTripwireTriggered as e:
        log.warning("Guardrail blocked this input: %s", e)
    except Exception as e:
        log.exception("Agent run failed: %s", e)
        raise SystemExit(1) from e


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
