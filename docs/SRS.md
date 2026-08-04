# Software Requirement Specification (SRS)

## 1. Introduction
This SRS complements the [BRD](./BRD.md) and [FRD](./FRD.md), defining non-functional
requirements, interfaces, and constraints for the RetailIQ Platform.

## 2. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | API endpoints for CRUD operations should respond in <200ms under light load (SQLite, local dev). |
| Availability | The platform must start and serve core retail functionality (catalog/inventory/orders/auth) with zero external API keys or compiled native dependencies. |
| Security | Passwords hashed with bcrypt; JWT bearer tokens with configurable expiry; secrets loaded from environment variables, never hardcoded. |
| Maintainability | Layered architecture (routers → services → repositories → ORM models); SOLID/DRY/KISS/YAGNI; full type hints. |
| Observability | Structured logs (console + rotating file) capturing execution time, errors, and agent-level metrics. |
| Testability | ≥90% intent coverage of service-layer business rules via positive/negative/boundary pytest cases. |
| Portability | SQLite by default; SQLAlchemy models are database-agnostic (PostgreSQL/MySQL swap is a connection-string change). |
| Extensibility | New agents, routers, or repositories can be added without modifying existing modules (Open/Closed via the repository/service pattern and the `AGENT_REGISTRY`). |

## 3. External Interfaces
- **REST API** (FastAPI, OpenAPI 3 docs at `/docs`) — consumed by the Streamlit
  frontend and any external client.
- **Streamlit Web UI** — human-facing interface calling the REST API over HTTP.
- **Vector Store** — ChromaDB (optional) or built-in NumPy store, accessed only by
  the backend's RAG service.
- **LLM Provider** — OpenAI (via `langchain-openai` + CrewAI), optional, configured
  via `OPENAI_API_KEY`.

## 4. Data Requirements
See [Database Design](./Architecture.md#database-design) in the Architecture
document for the entity-relationship overview (Category, Product, Inventory,
Customer, Order/OrderItem, User, RagDocument, FeedbackRecord).

## 5. Constraints
- Windows/PowerShell development environment without a pre-installed C++ build
  toolchain — all mandatory dependencies must ship prebuilt wheels for
  Python 3.12 / win_amd64 (see Architecture doc for the ChromaDB decision).
- No mandatory paid third-party API — CrewAI/LLM-backed generation and
  high-quality embeddings are optional upgrades.

## 6. Acceptance Criteria
Each functional requirement in the FRD is considered accepted when:
1. It is implemented behind a typed Pydantic schema and a service-layer method.
2. It has at least one positive, one negative, and (where applicable) one boundary
   automated test.
3. It is exposed via a documented REST endpoint and reachable from the Streamlit UI
   where relevant to an end user.
