import json 
from dotenv import load_dotenv
from agents import InputGuardrail, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
import asyncio
from travel_agent.input_guardrails import travel_guardrail
from travel_agent.agent_setup import create_agent


load_dotenv()
agent_config = json.load(open("travel_agent/agent_config.json"))
manager_agent = create_agent(agent_config, "manager_agent")
manager_agent.input_guardrails = [InputGuardrail(guardrail_function=travel_guardrail)]


async def main():
    try:
        result = await Runner.run(manager_agent, "Plan me a trip to Barcelona for 10 days in March.")
        print(result.final_output)
    except InputGuardrailTripwireTriggered as e:
        print("Guardrail blocked this input:", e)

if __name__ == "__main__":
    asyncio.run(main())