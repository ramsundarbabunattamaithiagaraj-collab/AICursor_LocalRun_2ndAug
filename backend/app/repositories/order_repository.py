from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(db, Order)

    def get_by_order_number(self, order_number: str) -> Order | None:
        stmt = select(Order).where(Order.order_number == order_number)
        return self.db.scalars(stmt).first()

    def list_for_customer(self, customer_id: int) -> list[Order]:
        stmt = select(Order).where(Order.customer_id == customer_id)
        return list(self.db.scalars(stmt).all())
