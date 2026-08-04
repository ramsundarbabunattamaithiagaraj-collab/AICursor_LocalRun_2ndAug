"""Business logic for the product catalog (Section 7: Product Catalog structure)."""
from __future__ import annotations

from app.core.logging_config import get_logger
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.exceptions import DuplicateResourceError, NotFoundError, ValidationError

logger = get_logger(__name__)


class ProductService:
    def __init__(self, db: Session):
        self.repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)

    def create(self, payload: ProductCreate) -> Product:
        if self.repo.get_by_sku(payload.sku):
            raise DuplicateResourceError("Product", "sku", payload.sku)
        if not self.category_repo.get(payload.category_id):
            raise NotFoundError("Category", payload.category_id)

        product = Product(**payload.model_dump())
        created = self.repo.add(product)
        logger.info("Product created: sku=%s id=%s", created.sku, created.id)
        return created

    def get(self, product_id: int) -> Product:
        product = self.repo.get(product_id)
        if not product:
            raise NotFoundError("Product", product_id)
        return product

    def get_by_sku(self, sku: str) -> Product:
        product = self.repo.get_by_sku(sku.strip().upper())
        if not product:
            raise NotFoundError("Product", sku)
        return product

    def search(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        brand: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        return self.repo.search(keyword, category_id, brand, active_only, skip, limit)

    def count(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        brand: str | None = None,
        active_only: bool = True,
    ) -> int:
        return self.repo.count_search(keyword, category_id, brand, active_only)

    def update(self, product_id: int, payload: ProductUpdate) -> Product:
        product = self.get(product_id)
        updates = payload.model_dump(exclude_unset=True)
        if "category_id" in updates and not self.category_repo.get(updates["category_id"]):
            raise NotFoundError("Category", updates["category_id"])
        for field, value in updates.items():
            setattr(product, field, value)
        updated = self.repo.commit_refresh(product)
        logger.info("Product updated: id=%s", product_id)
        return updated

    def deactivate(self, product_id: int) -> Product:
        product = self.get(product_id)
        product.is_active = False
        return self.repo.commit_refresh(product)

    def delete(self, product_id: int) -> None:
        product = self.get(product_id)
        self.repo.delete(product)
        logger.info("Product deleted: id=%s", product_id)
