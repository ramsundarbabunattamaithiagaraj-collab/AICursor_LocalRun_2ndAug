from __future__ import annotations

from app.agents.base_agent import BaseRetailAgent


class DeveloperAgent(BaseRetailAgent):
    name = "Developer"
    role = "Senior Full-Stack Developer"
    goal = (
        "Implement production-ready backend/frontend code following SOLID, DRY, "
        "Clean Code, type hints, repository pattern, dependency injection, and PEP8."
    )
    backstory = (
        "You are a senior engineer who writes clean, modular, well-tested Python "
        "code and follows enterprise coding standards without exception."
    )

    def task_description(self, project_brief: str) -> str:
        return (
            f"Propose an implementation plan (module breakdown, key classes, "
            f"and pseudocode) for the following feature, following SOLID/DRY/"
            f"Repository Pattern/Dependency Injection.\n\nFeature:\n{project_brief}"
        )

    def fallback_output(self, project_brief: str) -> str:
        return (
            "## Implementation Plan (simulated - configure OPENAI_API_KEY for LLM generation)\n\n"
            f"**Feature:** {project_brief.strip()}\n\n"
            "1. Define Pydantic schemas for request/response contracts.\n"
            "2. Add a repository class encapsulating SQLAlchemy queries.\n"
            "3. Implement a service class with business rules and validation.\n"
            "4. Expose a FastAPI router that depends on the service via DI.\n"
            "5. Add unit tests for the service (positive/negative/boundary).\n"
        )
