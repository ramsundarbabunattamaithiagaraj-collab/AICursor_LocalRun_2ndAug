from __future__ import annotations

from app.agents.base_agent import BaseRetailAgent


class DocumentationAgent(BaseRetailAgent):
    name = "Documentation"
    role = "Technical Writer"
    goal = (
        "Generate Word documentation, API docs, user guides, installation "
        "guides, release notes, and deployment guides."
    )
    backstory = (
        "You are a technical writer who produces clear, enterprise-grade "
        "documentation for both technical and non-technical audiences."
    )

    def task_description(self, project_brief: str) -> str:
        return (
            f"Write a concise user-facing documentation summary (what it does, "
            f"how to use it, and how to install it) for the following feature.\n\n"
            f"Feature:\n{project_brief}"
        )

    def fallback_output(self, project_brief: str) -> str:
        return (
            "## Documentation Summary (simulated - configure OPENAI_API_KEY for LLM generation)\n\n"
            f"**Feature:** {project_brief.strip()}\n\n"
            "### Overview\nThis feature is part of the RetailIQ platform. See "
            "docs/User_Manual.md and docs/API_Guide.md for full details.\n\n"
            "### Installation\nFollow docs/Installation_Guide.md to set up the backend and frontend.\n"
        )
