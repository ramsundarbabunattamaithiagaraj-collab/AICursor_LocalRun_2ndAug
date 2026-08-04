from __future__ import annotations

import pytest

from app.schemas.customer import CustomerCreate
from app.services.customer_service import CustomerService
from app.utils.exceptions import DuplicateResourceError, NotFoundError


class TestCustomerService:
    def test_create_customer_success(self, db_session):
        customer = CustomerService(db_session).create(
            CustomerCreate(full_name="Jane Doe", email="jane@example.com")
        )
        assert customer.loyalty_tier == "Bronze"
        assert customer.loyalty_points == 0.0

    def test_create_duplicate_email_raises(self, db_session):
        service = CustomerService(db_session)
        service.create(CustomerCreate(full_name="Jane Doe", email="jane@example.com"))
        with pytest.raises(DuplicateResourceError):
            service.create(CustomerCreate(full_name="Jane D.", email="jane@example.com"))

    def test_get_missing_customer_raises(self, db_session):
        with pytest.raises(NotFoundError):
            CustomerService(db_session).get(999)

    @pytest.mark.parametrize(
        "points,expected_tier",
        [(0, "Bronze"), (499, "Bronze"), (500, "Silver"), (2000, "Gold"), (5000, "Platinum"), (10000, "Platinum")],
    )
    def test_loyalty_tier_boundaries(self, db_session, points, expected_tier):
        service = CustomerService(db_session)
        customer = service.create(CustomerCreate(full_name="Jane Doe", email="jane@example.com"))
        updated = service.add_loyalty_points(customer.id, points)
        assert updated.loyalty_tier == expected_tier
