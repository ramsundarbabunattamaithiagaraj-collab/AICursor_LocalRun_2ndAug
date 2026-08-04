"""Business logic for customer profiles & loyalty programs (Section 7)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate
from app.utils.exceptions import DuplicateResourceError, NotFoundError

LOYALTY_TIERS = [
    (0, "Bronze"),
    (500, "Silver"),
    (2000, "Gold"),
    (5000, "Platinum"),
]


class CustomerService:
    def __init__(self, db: Session):
        self.repo = CustomerRepository(db)

    def create(self, payload: CustomerCreate) -> Customer:
        if self.repo.get_by_email(payload.email):
            raise DuplicateResourceError("Customer", "email", payload.email)
        return self.repo.add(Customer(**payload.model_dump()))

    def get(self, customer_id: int) -> Customer:
        customer = self.repo.get(customer_id)
        if not customer:
            raise NotFoundError("Customer", customer_id)
        return customer

    def list(self, skip: int = 0, limit: int = 100) -> list[Customer]:
        return self.repo.list(skip, limit)

    def add_loyalty_points(self, customer_id: int, points: float) -> Customer:
        customer = self.get(customer_id)
        customer.loyalty_points += points
        customer.loyalty_tier = self._compute_tier(customer.loyalty_points)
        return self.repo.commit_refresh(customer)

    @staticmethod
    def _compute_tier(points: float) -> str:
        tier = LOYALTY_TIERS[0][1]
        for threshold, name in LOYALTY_TIERS:
            if points >= threshold:
                tier = name
        return tier
