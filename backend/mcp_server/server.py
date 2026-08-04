"""RetailIQ MCP Server.

A small internal MCP (Model Context Protocol) server that exposes the core
RetailIQ platform capabilities - product catalog search, inventory checks,
order placement, the RAG knowledge assistant, and the CrewAI SDLC agents -
as tools that any MCP-compatible client (Cursor, Claude Desktop, etc.) can
call directly.

"Internal" by design: it imports the backend's service layer directly
(app.services.*) and talks straight to the local SQLite database via a
short-lived SQLAlchemy session per call, instead of proxying HTTP requests
to the FastAPI app. This keeps it lightweight and avoids requiring the
FastAPI server to be running at all.

Run standalone (stdio transport, the default MCP transport for local tools):

    cd backend
    python -m mcp_server.server

Configure in Cursor via `.cursor/mcp.json` (see repo root) or in Claude
Desktop's config using the same command/args shape.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Make the 'app' package importable regardless of the caller's working
# directory, since MCP clients typically invoke this script by absolute path.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from app.core.logging_config import get_logger  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.schemas.order import OrderCreate, OrderItemCreate  # noqa: E402
from app.services.agent_orchestration_service import get_agent_orchestration_service  # noqa: E402
from app.services.category_service import CategoryService  # noqa: E402
from app.services.inventory_service import InventoryService  # noqa: E402
from app.services.order_service import OrderService  # noqa: E402
from app.services.product_service import ProductService  # noqa: E402
from app.services.rag_service import get_rag_service  # noqa: E402
from app.utils.exceptions import RetailIQError  # noqa: E402

logger = get_logger(__name__)

mcp = FastMCP("retailiq")


def _product_to_dict(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "brand": product.brand,
        "category_id": product.category_id,
        "variant": product.variant,
        "size": product.size,
        "color": product.color,
        "list_price": product.list_price,
        "discount_percent": product.discount_percent,
        "tax_percent": product.tax_percent,
        "selling_price": product.selling_price,
        "is_active": product.is_active,
    }


@mcp.tool()
def search_products(
    keyword: str = "", category_id: int | None = None, brand: str = "", limit: int = 20
) -> list[dict[str, Any]]:
    """Search the retail product catalog by keyword, category, and/or brand.

    Args:
        keyword: Free-text search across product name, description, and SKU.
        category_id: Restrict results to a specific category ID.
        brand: Case-insensitive substring match on brand name.
        limit: Maximum number of products to return (default 20).
    """
    db = SessionLocal()
    try:
        products = ProductService(db).search(
            keyword=keyword or None, category_id=category_id, brand=brand or None, limit=limit
        )
        return [_product_to_dict(p) for p in products]
    finally:
        db.close()


@mcp.tool()
def get_product_by_sku(sku: str) -> dict[str, Any]:
    """Get full details for a single product by its SKU."""
    db = SessionLocal()
    try:
        product = ProductService(db).get_by_sku(sku)
        return _product_to_dict(product)
    except RetailIQError as exc:
        return {"error": str(exc)}
    finally:
        db.close()


@mcp.tool()
def list_categories() -> list[dict[str, Any]]:
    """List all product categories in the catalog."""
    db = SessionLocal()
    try:
        categories = CategoryService(db).list(limit=500)
        return [{"id": c.id, "name": c.name, "description": c.description} for c in categories]
    finally:
        db.close()


@mcp.tool()
def check_inventory(product_id: int) -> list[dict[str, Any]]:
    """Check stock levels for a product across all store/warehouse locations."""
    db = SessionLocal()
    try:
        records = InventoryService(db).list_for_product(product_id)
        return [
            {
                "id": r.id,
                "location_code": r.location_code,
                "quantity_available": r.quantity_available,
                "reorder_level": r.reorder_level,
                "needs_reorder": r.needs_reorder,
            }
            for r in records
        ]
    finally:
        db.close()


@mcp.tool()
def list_low_stock() -> list[dict[str, Any]]:
    """List every inventory record currently at or below its reorder level."""
    db = SessionLocal()
    try:
        records = InventoryService(db).list_low_stock()
        return [
            {
                "id": r.id,
                "product_id": r.product_id,
                "location_code": r.location_code,
                "quantity_available": r.quantity_available,
                "reorder_level": r.reorder_level,
            }
            for r in records
        ]
    finally:
        db.close()


@mcp.tool()
def place_order(customer_id: int, items: list[dict[str, int]], channel: str = "online") -> dict[str, Any]:
    """Place an order for a customer, reserving inventory automatically.

    Args:
        customer_id: The customer placing the order.
        items: List of line items, each shaped as {"product_id": int, "quantity": int}.
        channel: Sales channel - one of "online", "in-store", or "mobile".
    """
    db = SessionLocal()
    try:
        order_items = [
            OrderItemCreate(product_id=item["product_id"], quantity=item["quantity"]) for item in items
        ]
        order = OrderService(db).create_order(
            OrderCreate(customer_id=customer_id, channel=channel, items=order_items)
        )
        return {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "total_amount": order.total_amount,
        }
    except RetailIQError as exc:
        return {"error": str(exc)}
    finally:
        db.close()


@mcp.tool()
def get_order_status(order_id: int) -> dict[str, Any]:
    """Get the current status and line items for an order."""
    db = SessionLocal()
    try:
        order = OrderService(db).get(order_id)
        return {
            "order_number": order.order_number,
            "status": order.status.value,
            "channel": order.channel,
            "total_amount": order.total_amount,
            "items": [
                {"product_id": i.product_id, "quantity": i.quantity, "unit_price": i.unit_price}
                for i in order.items
            ],
        }
    except RetailIQError as exc:
        return {"error": str(exc)}
    finally:
        db.close()


@mcp.tool()
def query_knowledge_base(question: str, top_k: int = 5) -> dict[str, Any]:
    """Ask a natural-language question against ingested retail documents (RAG).

    Returns an answer with cited sources (document, page, content type, score).
    Ingest documents first via the backend's /api/v1/rag/ingest endpoint or the
    Streamlit RAG Assistant page.
    """
    try:
        result = get_rag_service().query(question, top_k)
        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "context_relevance": result.context_relevance,
            "sources": [source.model_dump() for source in result.sources],
        }
    except RetailIQError as exc:
        return {"error": str(exc)}


@mcp.tool()
def run_sdlc_agent(project_brief: str, target_agent: str = "all") -> dict[str, Any]:
    """Run the CrewAI multi-agent SDLC pipeline against a project brief.

    Args:
        project_brief: Free-text description of the feature/change to analyze.
        target_agent: One of "all", "business_analyst", "architect", "developer",
            "tester", or "documentation".

    Uses a real LLM (Groq preferred, then OpenAI) if configured via
    GROQ_API_KEY/OPENAI_API_KEY in backend/.env; otherwise returns clearly
    labeled deterministic template output.
    """
    try:
        response = get_agent_orchestration_service().run(project_brief, target_agent)
        return response.model_dump()
    except ValueError as exc:
        return {"error": str(exc)}


if __name__ == "__main__":
    logger.info("Starting RetailIQ MCP server (stdio transport)...")
    mcp.run()
