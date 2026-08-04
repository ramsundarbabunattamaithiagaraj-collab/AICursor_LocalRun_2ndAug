from __future__ import annotations

from app.agents.base_agent import BaseRetailAgent


class BusinessAnalystAgent(BaseRetailAgent):
    name = "Business Analyst"
    role = "Senior Retail Business Analyst"
    goal = (
        "Understand stakeholder requirements and produce a BRD, FRD, SRS, "
        "user stories, and acceptance criteria for the given retail project brief."
    )
    backstory = (
        "You are a seasoned business analyst with 15 years in retail technology "
        "(e-commerce, POS, inventory, loyalty). You translate vague business asks "
        "into precise, testable requirements."
    )

    def task_description(self, project_brief: str) -> str:
        return (
            f"Analyze the following retail project brief and produce: "
            f"(1) a concise Business Requirement Document, (2) key Functional "
            f"Requirements, (3) 3-5 User Stories with Acceptance Criteria "
            f"(Given/When/Then).\n\nProject Brief:\n{project_brief}"
        )

    def fallback_output(self, project_brief: str) -> str:
        return (
            "## Business Requirement Document (simulated - configure OPENAI_API_KEY for LLM generation)\n\n"
            f"**Objective:** {project_brief.strip()}\n\n"
            "### Functional Requirements\n"
            "- The system shall allow browsing and searching the product catalog.\n"
            "- The system shall track inventory availability per store/warehouse.\n"
            "- The system shall support cart, checkout, and order status tracking.\n\n"
            "### User Story\n"
            "As a customer, I want to search products by keyword and category, "
            "so that I can quickly find items I want to purchase.\n\n"
            "**Acceptance Criteria:**\n"
            "- Given a keyword, When I search, Then matching active products are returned.\n"
            "- Given a category filter, When applied, Then only products in that category appear.\n"
        )
