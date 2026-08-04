from __future__ import annotations

from app.agents.architect_agent import ArchitectAgent
from app.agents.base_agent import BaseRetailAgent
from app.agents.business_analyst_agent import BusinessAnalystAgent
from app.agents.developer_agent import DeveloperAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.tester_agent import TesterAgent

AGENT_REGISTRY: dict[str, BaseRetailAgent] = {
    "business_analyst": BusinessAnalystAgent(),
    "architect": ArchitectAgent(),
    "developer": DeveloperAgent(),
    "tester": TesterAgent(),
    "documentation": DocumentationAgent(),
}


def resolve_agents(target_agent: str) -> list[BaseRetailAgent]:
    if target_agent == "all":
        return list(AGENT_REGISTRY.values())
    agent = AGENT_REGISTRY.get(target_agent)
    return [agent] if agent else []
