# Release Notes

## v1.0.0 — Initial Release

### Added
- **Product Catalog** module: categories, products (SKU/brand/variant/size/color),
  pricing (list price, discount %, tax %), search/filter.
- **Inventory** module: multi-location stock tracking, low-stock detection, manual
  adjustments with audit reason.
- **Customers & Loyalty**: customer profiles, cumulative loyalty points, tiered
  loyalty status (Bronze/Silver/Gold/Platinum).
- **Order Management**: cart → placed → paid → shipped → delivered → return →
  refund lifecycle with strict state-machine validation and automatic inventory
  reservation.
- **Authentication**: JWT-based registration/login with role-based access
  (`admin`/`staff`/`customer`).
- **RAG Knowledge Assistant**: PDF ingestion (text, tables, images, OCR fallback),
  chunking/embedding, vector search, cited natural-language answers.
- **AI Agents Studio**: CrewAI-based Business Analyst, Architect, Developer, Tester,
  and Documentation agents with graceful template fallback when no LLM is
  configured; heuristic quality-metric scoring.
- **Feedback** capture for continuous improvement of generated artifacts.
- **Streamlit frontend**: 6 pages (Home, Product Catalog, Inventory, Orders, RAG
  Assistant, AI Agents Studio, Admin Login).
- **Testing**: 52 automated tests (unit + integration) covering positive, negative,
  and boundary scenarios across all core services and key API endpoints.
- **Docs**: BRD, FRD, SRS, Architecture, API Guide, Installation Guide, Deployment
  Guide, User Manual, Developer Guide (this set).
- **Docker**: `Dockerfile`s for backend/frontend + root `docker-compose.yml`.

### Known Limitations
- No payment gateway integration — `paid` is a manual status transition.
- ChromaDB and sentence-transformers/CrewAI+OpenAI are optional installs (see
  `requirements-optional.txt`) due to native-build/API-key constraints; the default
  install uses lightweight, dependency-free fallbacks for both.
- No database migration tool (Alembic) yet — schema changes require manual handling
  for existing databases beyond additive columns.

### Upgrade Path
- Install `backend/requirements-optional.txt` and set `OPENAI_API_KEY` for
  production-grade embeddings and real LLM-backed agent generation.
