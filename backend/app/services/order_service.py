"""Order management: cart, checkout, payment, order status (Section 7)."""
from __future__ import annotations

import uuid

from app.core.logging_config import get_logger
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus
from app.repositories.customer_repository import CustomerRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import OrderCreate
from app.services.inventory_service import InventoryService
from app.utils.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)

_VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CART: {OrderStatus.PLACED, OrderStatus.CANCELLED},
    OrderStatus.PLACED: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: {OrderStatus.RETURN_REQUESTED},
    OrderStatus.RETURN_REQUESTED: {OrderStatus.RETURNED},
    OrderStatus.RETURNED: {OrderStatus.REFUNDED},
    OrderStatus.REFUNDED: set(),
    OrderStatus.CANCELLED: set(),
}


class OrderService:
    def __init__(self, db: Session):
        self.repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.inventory_service = InventoryService(db)

    def create_order(self, payload: OrderCreate) -> Order:
        if not self.customer_repo.get(payload.customer_id):
            raise NotFoundError("Customer", payload.customer_id)

        items: list[OrderItem] = []
        total = 0.0
        for item in payload.items:
            product = self.product_repo.get(item.product_id)
            if not product:
                raise NotFoundError("Product", item.product_id)
            self.inventory_service.reserve_stock(item.product_id, item.quantity)
            unit_price = product.selling_price
            total += unit_price * item.quantity
            items.append(
                OrderItem(product_id=item.product_id, quantity=item.quantity, unit_price=unit_price)
            )

        order = Order(
            order_number=f"ORD-{uuid.uuid4().hex[:10].upper()}",
            customer_id=payload.customer_id,
            channel=payload.channel,
            status=OrderStatus.PLACED,
            total_amount=round(total, 2),
            items=items,
        )
        created = self.repo.add(order)
        logger.info("Order placed: order_number=%s total=%.2f", created.order_number, created.total_amount)
        return created

    def get(self, order_id: int) -> Order:
        order = self.repo.get(order_id)
        if not order:
            raise NotFoundError("Order", order_id)
        return order

    def list_for_customer(self, customer_id: int) -> list[Order]:
        return self.repo.list_for_customer(customer_id)

    def update_status(self, order_id: int, new_status: OrderStatus) -> Order:
        order = self.get(order_id)
        allowed = _VALID_TRANSITIONS.get(order.status, set())
        if new_status not in allowed:
            raise ValidationError(
                f"Cannot transition order from '{order.status.value}' to '{new_status.value}'."
            )
        order.status = new_status
        updated = self.repo.commit_refresh(order)
        logger.info("Order %s transitioned to %s", order.order_number, new_status.value)
        return updated
