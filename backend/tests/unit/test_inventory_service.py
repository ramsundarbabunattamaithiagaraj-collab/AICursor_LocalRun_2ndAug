from __future__ import annotations

import pytest

from app.schemas.category import CategoryCreate
from app.schemas.inventory import InventoryAdjust, InventoryCreate
from app.schemas.product import ProductCreate
from app.services.category_service import CategoryService
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.utils.exceptions import InsufficientStockError, NotFoundError


@pytest.fixture()
def product_id(db_session) -> int:
    category = CategoryService(db_session).create(CategoryCreate(name="Electronics"))
    product = ProductService(db_session).create(
        ProductCreate(sku="ELE-001", name="Earbuds", brand="AudioMax", category_id=category.id, list_price=59.99)
    )
    return product.id


class TestInventoryCreate:
    def test_create_inventory_success(self, db_session, product_id):
        record = InventoryService(db_session).create(
            InventoryCreate(product_id=product_id, location_code="STORE-1", quantity_available=50)
        )
        assert record.quantity_available == 50
        assert record.needs_reorder is False

    def test_create_inventory_missing_product_raises(self, db_session):
        with pytest.raises(NotFoundError):
            InventoryService(db_session).create(
                InventoryCreate(product_id=999, location_code="STORE-1", quantity_available=10)
            )

    def test_low_stock_flagged_at_or_below_reorder_level(self, db_session, product_id):
        record = InventoryService(db_session).create(
            InventoryCreate(product_id=product_id, location_code="STORE-1", quantity_available=5, reorder_level=10)
        )
        assert record.needs_reorder is True


class TestInventoryAdjust:
    def test_adjust_increases_stock(self, db_session, product_id):
        service = InventoryService(db_session)
        record = service.create(InventoryCreate(product_id=product_id, location_code="STORE-1", quantity_available=10))
        updated = service.adjust_stock(record.id, InventoryAdjust(delta=5, reason="Restock"))
        assert updated.quantity_available == 15

    def test_adjust_below_zero_raises_insufficient_stock(self, db_session, product_id):
        service = InventoryService(db_session)
        record = service.create(InventoryCreate(product_id=product_id, location_code="STORE-1", quantity_available=3))
        with pytest.raises(InsufficientStockError):
            service.adjust_stock(record.id, InventoryAdjust(delta=-10, reason="Sale"))

    def test_adjust_to_exactly_zero_is_allowed(self, db_session, product_id):
        service = InventoryService(db_session)
        record = service.create(InventoryCreate(product_id=product_id, location_code="STORE-1", quantity_available=5))
        updated = service.adjust_stock(record.id, InventoryAdjust(delta=-5, reason="Sale"))
        assert updated.quantity_available == 0

    def test_reserve_stock_across_locations(self, db_session, product_id):
        service = InventoryService(db_session)
        service.create(InventoryCreate(product_id=product_id, location_code="STORE-1", quantity_available=3))
        service.create(InventoryCreate(product_id=product_id, location_code="WAREHOUSE-1", quantity_available=10))

        service.reserve_stock(product_id, 5)

        remaining = sum(r.quantity_available for r in service.list_for_product(product_id))
        assert remaining == 8

    def test_reserve_stock_insufficient_raises(self, db_session, product_id):
        service = InventoryService(db_session)
        service.create(InventoryCreate(product_id=product_id, location_code="STORE-1", quantity_available=2))
        with pytest.raises(InsufficientStockError):
            service.reserve_stock(product_id, 5)
