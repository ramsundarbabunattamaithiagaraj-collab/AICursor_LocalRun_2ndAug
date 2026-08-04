from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.agents import AgentRunRequest, AgentRunResponse
from app.services.agent_orchestration_service import get_agent_orchestration_service

router = APIRouter(prefix="/api/v1/agents", tags=["AI Agents (CrewAI)"])


@router.post("/run", response_model=AgentRunResponse)
def run_agents(payload: AgentRunRequest) -> AgentRunResponse:
    try:
        return get_agent_orchestration_service().run(payload.project_brief, payload.target_agent)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/roster")
def list_agents() -> list[dict]:
    from app.agents.crew_config import AGENT_REGISTRY

    return [
        {"key": key, "name": agent.name, "role": agent.role, "goal": agent.goal}
        for key, agent in AGENT_REGISTRY.items()
    ]
