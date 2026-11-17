import os
from dataclasses import dataclass

from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ModelMessage

AUTH_TOKEN = os.environ["AUTH_TOKEN"]
MCP_SERVER_URL = "http://127.0.0.1:9000/mcp"


def _require_approval(ctx, tool_def, tool_args) -> bool:
    """Tylko hold_booking wymaga zatwierdzenia przez użytkownika. Pozostałe narzędzia są wykonywane automatycznie."""
    return tool_def.name == "hold_booking"


def build_agent() -> Agent:
    lot_toolset = MCPToolset(
        MCP_SERVER_URL,
        auth=AUTH_TOKEN,
        include_instructions=True,
    ).approval_required(_require_approval)

    return Agent(
        "openai:gpt-4o-mini",
        toolsets=[lot_toolset],
        output_type=[str, DeferredToolRequests],
        system_prompt=(
            "Jesteś asystentem rezerwacji lotów LOT. Zawsze sprawdź dostępność "
            "miejsc (check_seat_availability) przed próbą rezerwacji. "
            "hold_booking wymaga zgody użytkownika — jeśli zostanie odrzucone, "
            "poinformuj o tym użytkownika i zaproponuj alternatywę."
        ),
    )


@dataclass
class TurnResult:
    """Odpowiedź agenta po jednej turze rozmowy. Jeśli agent zwrócił DeferredToolRequests, pole `text` będzie None, a pole `pending` będzie zawierało obiekty do zatwierdzenia/odrzucenia przez użytkownika."""
    text: str | None
    pending: DeferredToolRequests | None
    messages: list[ModelMessage]


async def send_message(
    agent: Agent,
    user_message: str | None,
    message_history: list[ModelMessage] | None = None,
    deferred_tool_results: DeferredToolResults | None = None,
) -> TurnResult:
    """Wykonuje jedną turę rozmowy. Przekaż user_message=None, gdy wznawiasz zatrzymaną turę wyłącznie z decyzjami zatwierdzenia/odrzucenia i niczym nowym do powiedzenia."""
    async with agent:
        result = await agent.run(
            user_message,
            message_history=message_history,
            deferred_tool_results=deferred_tool_results,
        )

    if isinstance(result.output, DeferredToolRequests):
        return TurnResult(text=None, pending=result.output, messages=result.all_messages())

    return TurnResult(text=result.output, pending=None, messages=result.all_messages())


def build_deferred_results(decisions: dict[str, bool]) -> DeferredToolResults:
    """Mapa decyzji tool_call_id -> True (approve) / False (deny)."""
    results = DeferredToolResults()
    for tool_call_id, approved in decisions.items():
        results.approvals[tool_call_id] = approved
    return results
