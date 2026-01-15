from pydantic import BaseModel
from agents import Agent, Runner, GuardrailFunctionOutput


class IsTravelQuestion(BaseModel):
    is_travel_question: bool
    reasoning: str


guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about travel.",
    output_type=IsTravelQuestion,
)


async def travel_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(IsTravelQuestion)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_travel_question,
    )