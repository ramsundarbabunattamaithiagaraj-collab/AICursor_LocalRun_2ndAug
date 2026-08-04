# PROJECT TEMPLATE
Version: 1.0

> This document is the single source of truth for the project.
>
> AI Agent Instructions:
> - Read this entire document before generating any code.
> - If a section is empty, use the default configuration.
> - Never ask unnecessary questions.
> - Follow the standards defined in this file.
> - Generate production-ready code only.
> - Keep the project modular and maintainable.

---

# 1. PROJECT INFORMATION

## Project Name

<PROJECT_NAME>

## Description

<PROJECT_DESCRIPTION>

## Business Objective

<BUSINESS_OBJECTIVE>

## Domain

Default: Retail

## Target Users

<USERS>

---

# 2. REQUIREMENTS

## Functional Requirements

-

-

-

## Non Functional Requirements

-

-

-

## Business Rules

-

-

-

## Assumptions

-

-

-

## Out of Scope

-

-

---

# 3. DEFAULT TECHNOLOGY STACK

If not specified, use the following defaults.

Backend

Python

FastAPI

Frontend

Streamlit

Database

SQLite

ORM

SQLAlchemy

Authentication

JWT

Documentation

python-docx

Testing

pytest

Automation

Playwright

Container

Docker

Logging

Python Logging

Configuration

YAML

Package Manager

pip

---

# 4. AI FRAMEWORK

Default Framework

CrewAI

Default LLM

Latest configured model

Temperature

0.2

Memory

Enabled

Retry

3

Max Iterations

5

---

# 5. AGENTS

## Business Analyst

Responsibilities

- Understand requirements
- Generate BRD
- Generate FRD
- Generate SRS
- Create User Stories
- Create Acceptance Criteria

Expected Output

Business specification

---

## Architect

Responsibilities

- Design solution architecture
- Database design
- API contracts
- Component diagrams
- Security architecture
- Deployment architecture

Expected Output

Complete architecture

---

## Developer

Responsibilities

- Backend development
- Frontend development
- API implementation
- Database implementation
- Error handling
- Logging

Coding Rules

- SOLID
- DRY
- Clean Code
- Type Hints
- Repository Pattern
- Dependency Injection
- PEP8

Expected Output

Production-ready code

---

## Tester

Responsibilities

Generate

- Unit Tests
- Integration Tests
- API Tests
- Automation Tests
- Performance Tests

Coverage Target

90%+

---

## Documentation

Responsibilities

Generate

- Word Documentation
- API Documentation
- User Guide
- Installation Guide
- Release Notes
- Deployment Guide

---

# 6. RAG

Default

Enabled

Knowledge Sources

- Local Documents
- PDF
- DOCX
- TXT
- Wikipedia

## PDF Content Extraction

Retail domain PDF sources (product catalogs, price lists, planograms, spec sheets, invoices, promotional flyers) commonly combine multiple content types in the same document. The ingestion pipeline must extract and index **all** of the following from every PDF:

- **Text** — product descriptions, terms & conditions, policies, SKUs, brand/category copy
- **Images** — product photos, packaging shots, planogram/shelf-layout diagrams, logos, barcodes/QR codes
- **Tables** — price lists, size/variant matrices, inventory counts, discount/promo grids, comparison tables, tax/HSN tables

Extraction Requirements

- Use a layout-aware PDF parser capable of separating text blocks, embedded images, and table structures (e.g., `pdfplumber` / `PyMuPDF` for text & images, `camelot-py` / `pdfplumber` for tables)
- Preserve table structure as structured rows/columns (not flattened text) so numeric fields (price, quantity, discount %) remain queryable
- Run OCR (e.g., `pytesseract`) as a fallback for scanned/image-only PDFs or text embedded inside images
- Store extracted images with references back to their source page/product context; generate captions/alt-text for image-based retrieval
- Tag each extracted chunk with its content type (`text` | `image` | `table`) and source page number for traceable citations

Default Vector Database

ChromaDB

Default Embedding

BAAI/bge-base-en-v1.5

Image Embedding (for image-based retrieval)

CLIP (e.g., `openai/clip-vit-base-patch32`)

Chunk Size

800

Chunk Overlap

100

Always retrieve relevant knowledge before generating outputs.

Priority Rule

Custom/local approved documents have higher priority than external knowledge.

---

# 7. DOMAIN KNOWLEDGE

If Domain is Retail

Always consider

- Product Catalog structure (SKU, brand, category, variant, size, color)
- Pricing & Promotions (list price, discount, tax, bundle/combo offers)
- Inventory & Stock Availability across stores/warehouses
- Order Management (cart, checkout, payment, order status)
- Customer Profiles & Loyalty Programs
- Returns, Refunds & Exchange Policies
- Omnichannel Experience (in-store, online, mobile)
- Supply Chain & Vendor/Distributor Management
- Retail Compliance (consumer protection, pricing transparency, data privacy/PCI-DSS for payments)
- Seasonal & Merchandising Trends

If custom documents are provided

They have higher priority than external knowledge.

---

# 8. OUTPUT ARTIFACTS

Generate the following whenever applicable.

Business Requirement Document

Functional Requirement Document

Software Requirement Specification

Architecture Document

API Specification

Database Design

Source Code

Frontend

Backend

Unit Tests

Automation Tests

Developer Guide

User Guide

Release Notes

Deployment Guide

---

# 9. PROJECT STRUCTURE

Generate a clean enterprise folder structure.

Separate

- UI
- Backend
- Services
- Repository
- Models
- Schemas
- Utilities
- Tests
- Documentation

Avoid monolithic code.

---

# 10. CODING STANDARDS

Use

- SOLID
- DRY
- KISS
- YAGNI

Mandatory

- Type hints
- Logging
- Exception handling
- Configuration files
- Environment variables
- Input validation

Never

- Hardcode secrets
- Duplicate code
- Ignore exceptions
- Skip validation

---

# 11. TESTING

Every generated module must include

- Unit Tests
- Positive Scenarios
- Negative Scenarios
- Boundary Tests

Generate mock data where necessary.

---

# 12. DOCUMENTATION

Generate

README.md

Architecture.md

Installation Guide

API Guide

Deployment Guide

Release Notes

User Manual

Developer Guide

---

# 13. OBSERVABILITY

Every execution should capture

- Execution Time
- Errors
- Logs
- Agent Name
- Input
- Output
- Confidence
- Token Usage

---

# 14. FEEDBACK

User feedback should improve future generations.

Store

- Rating
- Comments
- Improvements

Use previous feedback when generating similar outputs.

---

# 15. QUALITY METRICS

For every generated artifact provide

Confidence Score

Hallucination Risk

Requirement Coverage

Context Relevance

Completeness

Explain briefly how each score was calculated.

---

# 16. DEFAULT BEHAVIOR

Unless explicitly requested otherwise

Always

- Follow best practices
- Produce modular code
- Keep files small
- Use reusable components
- Generate documentation
- Generate tests
- Follow enterprise architecture

---

# 17. FINAL INSTRUCTION

Treat this document as the project's authoritative specification.

Do not make assumptions that contradict this document.

If information is missing

Use framework defaults.

Generate production-ready outputs suitable for enterprise software development.
