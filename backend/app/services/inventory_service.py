"""Business logic for inventory & stock availability (Section 7)."""
from __future__ import annotations

from app.core.logging_config import get_logger
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import InventoryAdjust, InventoryCreate
from app.utils.exceptions import DuplicateResourceError, InsufficientStockError, NotFoundError

logger = get_logger(__name__)


class InventoryService:
    def __init__(self, db: Session):
        self.repo = InventoryRepository(db)
        self.product_repo = ProductRepository(db)

    def create(self, payload: InventoryCreate) -> Inventory:
        if not self.product_repo.get(payload.product_id):
            raise NotFoundError("Product", payload.product_id)
        if self.repo.get_by_product_and_location(payload.product_id, payload.location_code):
            raise DuplicateResourceError(
                "Inventory", "product_id/location_code", f"{payload.product_id}/{payload.location_code}"
            )
        return self.repo.add(Inventory(**payload.model_dump()))

    def get(self, inventory_id: int) -> Inventory:
        record = self.repo.get(inventory_id)
        if not record:
            raise NotFoundError("Inventory", inventory_id)
        return record

    def list_for_product(self, product_id: int) -> list[Inventory]:
        return self.repo.list_for_product(product_id)

    def list_low_stock(self) -> list[Inventory]:
        return self.repo.list_low_stock()

    def adjust_stock(self, inventory_id: int, payload: InventoryAdjust) -> Inventory:
        record = self.get(inventory_id)
        new_quantity = record.quantity_available + payload.delta
        if new_quantity < 0:
            product = self.product_repo.get(record.product_id)
            sku = product.sku if product else str(record.product_id)
            raise InsufficientStockError(sku, abs(payload.delta), record.quantity_available)
        record.quantity_available = new_quantity
        updated = self.repo.commit_refresh(record)
        logger.info(
            "Stock adjusted: inventory_id=%s delta=%s reason=%s new_qty=%s",
            inventory_id, payload.delta, payload.reason, new_quantity,
        )
        return updated

    def reserve_stock(self, product_id: int, quantity: int) -> None:
        """Deducts stock across the first location(s) that have enough quantity."""
        records = self.repo.list_for_product(product_id)
        total_available = sum(r.quantity_available for r in records)
        if total_available < quantity:
            raise InsufficientStockError(str(product_id), quantity, total_available)

        remaining = quantity
        for record in records:
            if remaining <= 0:
                break
            take = min(record.quantity_available, remaining)
            record.quantity_available -= take
            remaining -= take
            self.repo.commit_refresh(record)
