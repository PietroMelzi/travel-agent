import logging
from agents import Agent
from travel_agent.tools.tool_mapping import map_tool_name_to_function

log = logging.getLogger(__name__)


def _sanitize_tool_name(name: str) -> str:
    """
    OpenAI tool names must match: ^[a-zA-Z0-9_-]+$

    We keep it simple and deterministic:
    - replace spaces with underscores
    - drop any other disallowed characters
    - ensure non-empty fallback
    """
    if not name:
        return "tool"

    safe_chars = []
    for ch in name.replace(" ", "_"):
        if ch.isalnum() or ch in ("_", "-"):
            safe_chars.append(ch)
    sanitized = "".join(safe_chars)
    return sanitized or "tool"


def create_agent(multi_agent_specs: dict, agent_key: str) -> Agent:
    agent_specs = multi_agent_specs[agent_key]
    log.info("Creating agent: %s", agent_specs.get("name", agent_key))

    agents_as_tools = [
        create_agent(multi_agent_specs, key)
        for key in agent_specs.get("agents_as_tools", [])
    ]
    agents_as_tools = [
        tool.as_tool(
            tool_name=_sanitize_tool_name(tool.name),
            tool_description=multi_agent_specs[key]["description"],
        )
        for key, tool in zip(agent_specs.get("agents_as_tools", []), agents_as_tools)
    ]

    handoffs = [
        create_agent(multi_agent_specs, agent_key)
        for agent_key in agent_specs.get("handoffs", [])
    ]

    tools = agent_specs.get("tools", [])
    tools = [map_tool_name_to_function[tool] for tool in tools]

    return Agent(
        name=agent_specs["name"],
        instructions=agent_specs["instructions"],
        tools=agents_as_tools + tools,
        handoffs=handoffs,
    )
