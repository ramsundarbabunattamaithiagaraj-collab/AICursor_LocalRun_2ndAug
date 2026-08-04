# Functional Requirement Document (FRD)

## FR-1 Product Catalog
- FR-1.1 Create/read/update/(soft-)deactivate/delete products with SKU, brand,
  category, variant, size, color, list price, discount %, tax %.
- FR-1.2 Search products by keyword, category, brand, and active status.
- FR-1.3 Compute selling price from list price, discount %, and tax %.
- FR-1.4 Enforce unique SKUs (case-normalized).

## FR-2 Categories
- FR-2.1 Create and list product categories.
- FR-2.2 Prevent duplicate category names.

## FR-3 Inventory
- FR-3.1 Track stock quantity per product per location (store/warehouse).
- FR-3.2 Flag records at or below their reorder level as needing reorder.
- FR-3.3 Adjust stock by a signed delta with a mandatory reason; reject adjustments
  that would drive quantity below zero.
- FR-3.4 Reserve stock across multiple locations when an order is placed.

## FR-4 Customers & Loyalty
- FR-4.1 Create customer profiles (name, email, phone) with unique email.
- FR-4.2 Track loyalty points and compute loyalty tier from cumulative points.

## FR-5 Orders
- FR-5.1 Place an order for a customer with one or more line items; compute total
  from each product's selling price at order time.
- FR-5.2 Reserve inventory atomically per item; fail the whole order if any item has
  insufficient stock.
- FR-5.3 Enforce a strict status state machine: `cart → placed → paid → shipped →
  delivered → return_requested → returned → refunded`, plus `cancelled` from
  `cart`/`placed`/`paid`.
- FR-5.4 List orders for a given customer.

## FR-6 Authentication & Authorization
- FR-6.1 Register a user with a hashed password (bcrypt) and a role
  (`admin` | `staff` | `customer`).
- FR-6.2 Authenticate via username/password and issue a JWT access token.
- FR-6.3 Protect endpoints requiring authentication via bearer token; support
  role-based restriction via a reusable dependency.

## FR-7 RAG Knowledge Assistant
- FR-7.1 Ingest a PDF: extract text, tables (as structured rows/columns), and images
  (with page-referenced captions), tagging each chunk's content type and source page.
- FR-7.2 Fall back to OCR when a PDF/page has no extractable embedded text.
- FR-7.3 Chunk text content (configurable chunk size/overlap) and embed it.
- FR-7.4 Store embeddings in a vector index (ChromaDB if available, otherwise a
  built-in NumPy vector store) and persist ingested-document metadata.
- FR-7.5 Answer natural-language questions by retrieving the top-k most relevant
  chunks, returning cited sources (document, page, content type, snippet, score),
  a confidence score, and a context-relevance score.

## FR-8 AI Agents Studio (CrewAI)
- FR-8.1 Run one or all of: Business Analyst, Architect, Developer, Tester,
  Documentation agents against a free-text project brief.
- FR-8.2 When an LLM provider is configured, generate real LLM-backed output via
  CrewAI; otherwise return clearly-labeled deterministic template output.
- FR-8.3 Report per-agent execution time and quality metrics (confidence,
  hallucination risk, requirement coverage, context relevance, completeness) with a
  textual explanation of how each was derived.

## FR-9 Feedback
- FR-9.1 Submit a rating (1-5), comments, and improvement suggestions for a given
  artifact type.
- FR-9.2 Compute the average rating, optionally filtered by artifact type.

## FR-10 Observability
- FR-10.1 Log every HTTP request with method, path, status code, and latency.
- FR-10.2 Log every agent execution with agent name, input/output size, execution
  time, and confidence.
- FR-10.3 Rotate log files and retain a configurable number of backups.
