from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(db, Product)

    def get_by_sku(self, sku: str) -> Product | None:
        stmt = select(Product).where(Product.sku == sku)
        return self.db.scalars(stmt).first()

    @staticmethod
    def _apply_search_filters(
        stmt,
        keyword: str | None,
        category_id: int | None,
        brand: str | None,
        active_only: bool,
    ):
        """Applies the shared set of search predicates to any base statement,
        so `search()` and `count_search()` never drift out of sync (DRY)."""
        if active_only:
            stmt = stmt.where(Product.is_active.is_(True))
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if brand:
            stmt = stmt.where(Product.brand.ilike(f"%{brand}%"))
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(Product.name.ilike(like), Product.description.ilike(like), Product.sku.ilike(like))
            )
        return stmt

    def search(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        brand: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        stmt = self._apply_search_filters(select(Product), keyword, category_id, brand, active_only)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_search(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        brand: str | None = None,
        active_only: bool = True,
    ) -> int:
        """Total count of records matching the same filters as `search()`,
        ignoring pagination - used to compute total pages for the UI."""
        stmt = self._apply_search_filters(
            select(func.count()).select_from(Product), keyword, category_id, brand, active_only
        )
        return self.db.scalar(stmt) or 0
