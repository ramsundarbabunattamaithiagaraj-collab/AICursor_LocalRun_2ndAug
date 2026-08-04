"""Shared base for all SDLC agents (Section 5).

Each concrete agent defines its role, goal, and backstory for CrewAI, plus a
`fallback_output` used when no LLM provider is configured so the platform
remains runnable/demoable without external API keys (graceful degradation,
matching the project's availability-first defaults).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseRetailAgent(ABC):
    name: str
    role: str
    goal: str
    backstory: str

    def build_crewai_agent(self, llm):
        from crewai import Agent

        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            llm=llm,
            verbose=False,
            memory=True,
            max_iter=5,
        )

    @abstractmethod
    def task_description(self, project_brief: str) -> str:
        ...

    @abstractmethod
    def fallback_output(self, project_brief: str) -> str:
        """Deterministic, template-based output used when no LLM is configured."""
        ...
