from __future__ import annotations

from app.agents.base_agent import BaseRetailAgent


class TesterAgent(BaseRetailAgent):
    name = "Tester"
    role = "QA Automation Engineer"
    goal = (
        "Generate unit, integration, API, automation, and performance test plans "
        "targeting 90%+ coverage, covering positive, negative, and boundary cases."
    )
    backstory = (
        "You are a meticulous QA engineer who never ships a feature without "
        "comprehensive positive, negative, and boundary test coverage."
    )

    def task_description(self, project_brief: str) -> str:
        return (
            f"Produce a test plan (unit, integration, API, automation) for the "
            f"following feature, listing concrete positive/negative/boundary "
            f"test cases.\n\nFeature:\n{project_brief}"
        )

    def fallback_output(self, project_brief: str) -> str:
        return (
            "## Test Plan (simulated - configure OPENAI_API_KEY for LLM generation)\n\n"
            f"**Feature:** {project_brief.strip()}\n\n"
            "### Positive\n- Valid input returns 200/201 with expected payload.\n\n"
            "### Negative\n- Invalid/missing fields return 422 with validation errors.\n"
            "- Duplicate unique fields (SKU/email) return 409/400 with a clear message.\n\n"
            "### Boundary\n- Zero/negative quantities are rejected.\n"
            "- Maximum field lengths are enforced.\n"
        )
