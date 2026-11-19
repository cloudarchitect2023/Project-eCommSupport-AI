from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, Customer, Order, Product, StoreService


@pytest.fixture
def store():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions.begin() as session:
        session.add_all(
            [
                Customer(
                    customer_id="customer-1",
                    display_name="Test Customer",
                    email="test@example.invalid",
                ),
                Customer(
                    customer_id="customer-2",
                    display_name="Other Customer",
                    email="other@example.invalid",
                ),
                Product(
                    product_id="LAPTOP-100",
                    name="Laptop",
                    description="Test laptop",
                    price=Decimal("100.00"),
                    inventory=2,
                ),
                Order(
                    order_id="ORD-1",
                    customer_id="customer-1",
                    product_id="LAPTOP-100",
                    quantity=1,
                    status="shipped",
                    created_at=datetime.now(timezone.utc),
                ),
            ]
        )
    yield StoreService(sessions)
    engine.dispose()


def test_product_lookup_returns_only_needed_fields(store):
    product = store.get_product_details("LAPTOP-100")
    assert product["found"] is True
    assert product["price"] == "100.00"
    assert "email" not in product


def test_order_lookup_enforces_customer_ownership(store):
    assert store.check_order_status("ORD-1", "customer-1")["found"] is True
    assert store.check_order_status("ORD-1", "customer-2") == {
        "found": False,
        "order_id": "ORD-1",
    }


def test_order_places_and_decrements_inventory(store):
    result = store.place_order("customer-1", "LAPTOP-100", 2)
    assert result["created"] is True
    assert store.get_product_details("LAPTOP-100")["inventory"] == 0


def test_order_rejects_out_of_stock_and_invalid_quantity(store):
    assert store.place_order("customer-1", "LAPTOP-100", 3)["reason"] == "insufficient_inventory"
    with pytest.raises(ValueError):
        store.place_order("customer-1", "LAPTOP-100", 0)
