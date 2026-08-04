from __future__ import annotations

from app.agents.base_agent import BaseRetailAgent


class ArchitectAgent(BaseRetailAgent):
    name = "Architect"
    role = "Principal Solutions Architect"
    goal = (
        "Design a scalable, secure solution architecture including database "
        "design, API contracts, component diagram, and deployment topology."
    )
    backstory = (
        "You are a principal architect specialized in retail platforms, skilled "
        "in FastAPI, event-driven design, and cloud-native deployment on Docker/Kubernetes."
    )

    def task_description(self, project_brief: str) -> str:
        return (
            f"Design the solution architecture for this retail project. Include "
            f"a component diagram (as a text/mermaid description), key API "
            f"endpoints, a normalized database schema outline, and a security "
            f"architecture summary.\n\nProject Brief:\n{project_brief}"
        )

    def fallback_output(self, project_brief: str) -> str:
        return (
            "## Architecture Overview (simulated - configure OPENAI_API_KEY for LLM generation)\n\n"
            f"**Scope:** {project_brief.strip()}\n\n"
            "### Layers\n"
            "- Presentation: Streamlit UI\n"
            "- API: FastAPI (routers -> services -> repositories -> ORM models)\n"
            "- Data: SQLite via SQLAlchemy (swappable for PostgreSQL in production)\n"
            "- RAG: ChromaDB vector store + embedding model\n\n"
            "### Security\n"
            "- JWT bearer tokens, bcrypt password hashing, role-based access (admin/staff/customer)\n\n"
            "### Deployment\n"
            "- Dockerized backend + frontend, docker-compose for local orchestration\n"
        )
