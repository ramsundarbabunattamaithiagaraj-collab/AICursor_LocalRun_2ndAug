"""Seeds the database with realistic retail demo data.

Run with: python seed_data.py
Safe to re-run - skips seeding if categories already exist.
"""
from __future__ import annotations

from app.core.logging_config import get_logger
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.category import Category
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.user import User, UserRole
from app.core.security import hash_password

logger = get_logger(__name__)

CATEGORIES = ["Apparel", "Footwear", "Electronics", "Groceries", "Home & Kitchen"]

PRODUCTS = [
    dict(sku="APP-TSHIRT-BLK-M", name="Classic Crew T-Shirt", brand="UrbanThread", category="Apparel",
         variant="Crew Neck", size="M", color="Black", list_price=19.99, discount_percent=10, tax_percent=5),
    dict(sku="APP-JEANS-BLU-32", name="Slim Fit Jeans", brand="DenimCo", category="Apparel",
         variant="Slim Fit", size="32", color="Blue", list_price=49.99, discount_percent=15, tax_percent=5),
    dict(sku="SHO-RUN-WHT-9", name="AirRun Running Shoes", brand="Stridex", category="Footwear",
         variant="Running", size="9", color="White", list_price=79.99, discount_percent=20, tax_percent=8),
    dict(sku="ELE-EARBUD-BLK", name="SoundPods Wireless Earbuds", brand="AudioMax", category="Electronics",
         variant="Wireless", size=None, color="Black", list_price=59.99, discount_percent=5, tax_percent=12),
    dict(sku="ELE-SMARTWATCH-01", name="PulseFit Smartwatch", brand="AudioMax", category="Electronics",
         variant="Fitness", size=None, color="Graphite", list_price=129.99, discount_percent=10, tax_percent=12),
    dict(sku="GRO-COFFEE-1KG", name="Arabica Ground Coffee 1kg", brand="BrewHouse", category="Groceries",
         variant="Ground", size="1kg", color=None, list_price=14.99, discount_percent=0, tax_percent=2),
    dict(sku="HOM-BLENDER-01", name="PowerBlend Countertop Blender", brand="KitchenPro", category="Home & Kitchen",
         variant="700W", size=None, color="Silver", list_price=44.99, discount_percent=12, tax_percent=8),
]

CUSTOMERS = [
    dict(full_name="Asha Rao", email="asha.rao@example.com", phone="+1-555-0101"),
    dict(full_name="Miguel Santos", email="miguel.santos@example.com", phone="+1-555-0102"),
    dict(full_name="Priya Nair", email="priya.nair@example.com", phone="+1-555-0103"),
]


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(Category).count() > 0:
            logger.info("Database already seeded - skipping.")
            return

        category_map: dict[str, Category] = {}
        for name in CATEGORIES:
            category = Category(name=name, description=f"{name} products")
            db.add(category)
            db.flush()
            category_map[name] = category

        for spec in PRODUCTS:
            category = category_map[spec.pop("category")]
            product = Product(category_id=category.id, **spec)
            db.add(product)
            db.flush()
            db.add(
                Inventory(
                    product_id=product.id, location_code="STORE-001",
                    quantity_available=50, reorder_level=10,
                )
            )
            db.add(
                Inventory(
                    product_id=product.id, location_code="WAREHOUSE-CENTRAL",
                    quantity_available=200, reorder_level=25,
                )
            )

        for spec in CUSTOMERS:
            db.add(Customer(**spec))

        admin_exists = db.query(User).filter(User.username == "admin").first()
        if not admin_exists:
            db.add(
                User(
                    username="admin",
                    email="admin@retailiq.local",
                    hashed_password=hash_password("Admin@123"),
                    role=UserRole.ADMIN,
                )
            )

        db.commit()
        logger.info(
            "Seeded %s categories, %s products, %s customers, and a default admin user "
            "(username=admin, password=Admin@123 - change this immediately in production).",
            len(CATEGORIES), len(PRODUCTS), len(CUSTOMERS),
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
