from __future__ import annotations

import pytest

from app.models.order import OrderStatus
from app.schemas.category import CategoryCreate
from app.schemas.customer import CustomerCreate
from app.schemas.inventory import InventoryCreate
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.product import ProductCreate
from app.services.category_service import CategoryService
from app.services.customer_service import CustomerService
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.utils.exceptions import InsufficientStockError, NotFoundError, ValidationError


@pytest.fixture()
def setup(db_session):
    category = CategoryService(db_session).create(CategoryCreate(name="Footwear"))
    product = ProductService(db_session).create(
        ProductCreate(sku="SHO-001", name="Sneaker", brand="Stridex", category_id=category.id, list_price=100.0)
    )
    InventoryService(db_session).create(
        InventoryCreate(product_id=product.id, location_code="STORE-1", quantity_available=10)
    )
    customer = CustomerService(db_session).create(CustomerCreate(full_name="Jane Doe", email="jane@example.com"))
    return {"product_id": product.id, "customer_id": customer.id}


class TestOrderCreation:
    def test_create_order_success(self, db_session, setup):
        order = OrderService(db_session).create_order(
            OrderCreate(customer_id=setup["customer_id"], items=[OrderItemCreate(product_id=setup["product_id"], quantity=2)])
        )
        assert order.status == OrderStatus.PLACED
        assert order.total_amount == pytest.approx(200.0)
        assert order.order_number.startswith("ORD-")

    def test_create_order_reduces_inventory(self, db_session, setup):
        OrderService(db_session).create_order(
            OrderCreate(customer_id=setup["customer_id"], items=[OrderItemCreate(product_id=setup["product_id"], quantity=3)])
        )
        remaining = InventoryService(db_session).list_for_product(setup["product_id"])[0]
        assert remaining.quantity_available == 7

    def test_create_order_missing_customer_raises(self, db_session, setup):
        with pytest.raises(NotFoundError):
            OrderService(db_session).create_order(
                OrderCreate(customer_id=999, items=[OrderItemCreate(product_id=setup["product_id"], quantity=1)])
            )

    def test_create_order_insufficient_stock_raises(self, db_session, setup):
        with pytest.raises(InsufficientStockError):
            OrderService(db_session).create_order(
                OrderCreate(customer_id=setup["customer_id"], items=[OrderItemCreate(product_id=setup["product_id"], quantity=999)])
            )


class TestOrderStatusTransitions:
    def test_valid_transition_succeeds(self, db_session, setup):
        service = OrderService(db_session)
        order = service.create_order(
            OrderCreate(customer_id=setup["customer_id"], items=[OrderItemCreate(product_id=setup["product_id"], quantity=1)])
        )
        updated = service.update_status(order.id, OrderStatus.PAID)
        assert updated.status == OrderStatus.PAID

    def test_invalid_transition_raises(self, db_session, setup):
        service = OrderService(db_session)
        order = service.create_order(
            OrderCreate(customer_id=setup["customer_id"], items=[OrderItemCreate(product_id=setup["product_id"], quantity=1)])
        )
        with pytest.raises(ValidationError):
            service.update_status(order.id, OrderStatus.DELIVERED)
