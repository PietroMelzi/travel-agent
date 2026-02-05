import json
from datetime import datetime, timezone
from collections import deque
from dotenv import load_dotenv
from travel_agent.agent_setup import create_agent


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


def load_agent():
    load_dotenv()
    with open("travel_agent/agent_config.json", encoding="utf-8") as f:
        agent_config = json.load(f)
    manager_agent = create_agent(agent_config, "manager_agent")
    # manager_agent.input_guardrails = [InputGuardrail(guardrail_function=travel_guardrail)]
    return manager_agent
