# Business Requirement Document (BRD)

## 1. Project
**Name:** RetailIQ Platform
**Domain:** Retail
**Prepared per:** `retail_agend.md` (Section 1)

## 2. Business Objective
Provide a unified retail operations platform that lets a retail business manage its
product catalog, inventory, orders, and customer relationships, while giving staff
and stakeholders an AI-assisted knowledge assistant (RAG over retail documents) and
an AI-assisted software delivery toolkit (CrewAI multi-agent SDLC generation) to
accelerate both retail operations and the platform's own evolution.

> Note: `retail_agend.md` left `<PROJECT_NAME>`, `<PROJECT_DESCRIPTION>`,
> `<BUSINESS_OBJECTIVE>`, and `<USERS>` as empty placeholders. Per the document's own
> instructions ("If a section is empty, use the default configuration... Never ask
> unnecessary questions... Use framework defaults"), reasonable retail-domain defaults
> were assumed and are documented here for traceability.

## 3. Target Users
- **Store/Ops staff** — manage catalog, inventory, and order fulfillment.
- **Customers** — browse products, place orders, track status, earn loyalty points.
- **Business analysts / product managers** — use the RAG assistant to query retail
  documents (catalogs, price lists, policies) and the AI Agents Studio to generate
  specs for new features.
- **Administrators** — manage users, roles, and platform configuration.

## 4. Business Rules
- Product SKUs are unique and case-normalized (stored uppercase).
- Selling price = list price, discounted, then taxed: `list_price * (1 - discount%) * (1 + tax%)`.
- Orders reserve inventory at creation time; insufficient stock blocks order placement.
- Orders follow a strict status lifecycle (see FRD) — invalid transitions are rejected.
- Loyalty tiers are computed from cumulative points: Bronze (0+), Silver (500+),
  Gold (2000+), Platinum (5000+).
- Locally ingested retail documents take priority over any external/generic knowledge
  when answering RAG queries (Priority Rule, Section 6).

## 5. Assumptions
- Single-tenant deployment (one retailer, not a multi-tenant SaaS) for this version.
- SQLite is sufficient for the target deployment scale; PostgreSQL migration is a
  documented future upgrade path (same SQLAlchemy models apply).
- Real LLM-backed generation (CrewAI agents, high-quality embeddings) is optional and
  gated behind explicit configuration (`OPENAI_API_KEY`, optional dependencies) —
  the platform must remain fully functional without any paid API access.

## 6. Out of Scope (v1.0)
- Payment gateway integration (order `paid` status is a manual/simulated transition).
- Multi-currency / multi-language support.
- Real-time inventory sync with external POS/ERP systems.
- Mobile native apps (web-responsive Streamlit UI only).

## 7. Success Criteria
- All functional requirements in the [FRD](./FRD.md) are implemented and covered by
  automated tests (unit + integration).
- The platform runs end-to-end (backend + frontend) with a single documented setup
  procedure and no mandatory paid API keys.
