from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.repositories.base_repository import BaseRepository


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self, db: Session):
        super().__init__(db, Inventory)

    def get_by_product_and_location(self, product_id: int, location_code: str) -> Inventory | None:
        stmt = select(Inventory).where(
            Inventory.product_id == product_id, Inventory.location_code == location_code
        )
        return self.db.scalars(stmt).first()

    def list_for_product(self, product_id: int) -> list[Inventory]:
        stmt = select(Inventory).where(Inventory.product_id == product_id)
        return list(self.db.scalars(stmt).all())

    def list_low_stock(self) -> list[Inventory]:
        stmt = select(Inventory)
        return [inv for inv in self.db.scalars(stmt).all() if inv.needs_reorder]
