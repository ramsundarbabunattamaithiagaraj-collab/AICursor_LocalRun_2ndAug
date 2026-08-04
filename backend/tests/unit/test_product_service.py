from __future__ import annotations

import pytest

from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.category_service import CategoryService
from app.services.product_service import ProductService
from app.utils.exceptions import DuplicateResourceError, NotFoundError


def _make_category(db_session) -> int:
    category = CategoryService(db_session).create(CategoryCreate(name="Apparel"))
    return category.id


def _make_product_payload(category_id: int, sku: str = "APP-001") -> ProductCreate:
    return ProductCreate(
        sku=sku, name="Test Shirt", brand="TestBrand", category_id=category_id,
        list_price=20.0, discount_percent=10, tax_percent=5,
    )


class TestProductServiceCreate:
    def test_create_product_success(self, db_session):
        category_id = _make_category(db_session)
        service = ProductService(db_session)

        product = service.create(_make_product_payload(category_id))

        assert product.id is not None
        assert product.sku == "APP-001"
        assert product.selling_price == pytest.approx(18.9)  # 20 * 0.9 * 1.05

    def test_create_product_normalizes_sku_case(self, db_session):
        category_id = _make_category(db_session)
        payload = _make_product_payload(category_id, sku="app-lower")
        product = ProductService(db_session).create(payload)
        assert product.sku == "APP-LOWER"

    def test_create_duplicate_sku_raises(self, db_session):
        category_id = _make_category(db_session)
        service = ProductService(db_session)
        service.create(_make_product_payload(category_id))

        with pytest.raises(DuplicateResourceError):
            service.create(_make_product_payload(category_id))

    def test_create_with_missing_category_raises(self, db_session):
        service = ProductService(db_session)
        with pytest.raises(NotFoundError):
            service.create(_make_product_payload(category_id=999))


class TestProductServiceRetrieval:
    def test_get_missing_product_raises(self, db_session):
        with pytest.raises(NotFoundError):
            ProductService(db_session).get(999)

    def test_get_by_sku_is_case_insensitive_on_input(self, db_session):
        category_id = _make_category(db_session)
        ProductService(db_session).create(_make_product_payload(category_id))
        found = ProductService(db_session).get_by_sku("app-001")
        assert found.sku == "APP-001"

    def test_search_filters_by_keyword(self, db_session):
        category_id = _make_category(db_session)
        service = ProductService(db_session)
        service.create(_make_product_payload(category_id, sku="APP-001"))
        service.create(ProductCreate(
            sku="APP-002", name="Blue Jeans", brand="DenimCo", category_id=category_id, list_price=40,
        ))

        results = service.search(keyword="Shirt")
        assert len(results) == 1
        assert results[0].sku == "APP-001"


class TestProductServicePagination:
    def _seed_products(self, db_session, count: int) -> int:
        category_id = _make_category(db_session)
        service = ProductService(db_session)
        for i in range(count):
            service.create(ProductCreate(
                sku=f"APP-{i:03d}", name=f"Item {i}", brand="TestBrand", category_id=category_id, list_price=10,
            ))
        return category_id

    def test_count_matches_total_regardless_of_page_size(self, db_session):
        self._seed_products(db_session, 7)
        service = ProductService(db_session)
        assert service.count() == 7

    def test_search_returns_requested_page_size(self, db_session):
        self._seed_products(db_session, 7)
        service = ProductService(db_session)
        page = service.search(skip=0, limit=5)
        assert len(page) == 5

    def test_search_last_page_returns_remainder(self, db_session):
        self._seed_products(db_session, 7)
        service = ProductService(db_session)
        last_page = service.search(skip=5, limit=5)
        assert len(last_page) == 2

    def test_count_respects_filters(self, db_session):
        category_id = self._seed_products(db_session, 3)
        service = ProductService(db_session)
        service.create(ProductCreate(
            sku="SHO-001", name="Sneaker", brand="Stridex", category_id=category_id, list_price=50,
        ))
        assert service.count(keyword="Sneaker") == 1

    def test_search_beyond_last_page_returns_empty(self, db_session):
        self._seed_products(db_session, 3)
        service = ProductService(db_session)
        assert service.search(skip=100, limit=10) == []


class TestProductServiceUpdate:
    def test_update_changes_fields(self, db_session):
        category_id = _make_category(db_session)
        product = ProductService(db_session).create(_make_product_payload(category_id))

        updated = ProductService(db_session).update(product.id, ProductUpdate(list_price=99.99))
        assert updated.list_price == 99.99

    def test_deactivate_sets_inactive(self, db_session):
        category_id = _make_category(db_session)
        product = ProductService(db_session).create(_make_product_payload(category_id))

        deactivated = ProductService(db_session).deactivate(product.id)
        assert deactivated.is_active is False
