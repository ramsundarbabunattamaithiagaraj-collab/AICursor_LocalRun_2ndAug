from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate
from app.utils.exceptions import DuplicateResourceError, NotFoundError


class CategoryService:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def create(self, payload: CategoryCreate) -> Category:
        if self.repo.get_by_name(payload.name):
            raise DuplicateResourceError("Category", "name", payload.name)
        return self.repo.add(Category(**payload.model_dump()))

    def get(self, category_id: int) -> Category:
        category = self.repo.get(category_id)
        if not category:
            raise NotFoundError("Category", category_id)
        return category

    def list(self, skip: int = 0, limit: int = 100) -> list[Category]:
        return self.repo.list(skip, limit)
