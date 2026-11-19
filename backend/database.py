from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from backend.settings import DATABASE_URL, ensure_data_directory


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    inventory: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


def _engine_url() -> str:
    if DATABASE_URL.startswith("sqlite:///"):
        ensure_data_directory()
    return DATABASE_URL


engine = create_engine(_engine_url(), pool_pre_ping=True)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database() -> None:
    Base.metadata.create_all(engine)


def seed_demo_data() -> None:
    initialize_database()
    with SessionFactory.begin() as session:
        if session.scalar(select(Product.product_id).limit(1)) is not None:
            return
        session.add_all(
            [
                Product(
                    product_id="LAPTOP-100",
                    name="Everyday laptop",
                    description="14-inch laptop with a one-year limited warranty.",
                    price=Decimal("799.00"),
                    inventory=12,
                ),
                Product(
                    product_id="PHONE-200",
                    name="Smartphone",
                    description="Unlocked smartphone with a one-year limited warranty.",
                    price=Decimal("599.00"),
                    inventory=20,
                ),
                Customer(
                    customer_id="demo-customer",
                    display_name="Demo Customer",
                    email="demo@example.invalid",
                ),
            ]
        )
        session.add(
            Order(
                order_id="ORD-DEMO-001",
                customer_id="demo-customer",
                product_id="LAPTOP-100",
                quantity=1,
                status="shipped",
                created_at=datetime.now(timezone.utc),
            )
        )


class StoreService:
    """Fixed, parameterized operations exposed to the agent through MCP."""

    def __init__(self, sessions: sessionmaker[Session] = SessionFactory):
        self.sessions = sessions

    def get_product_details(self, product_id: str) -> dict[str, Any]:
        normalized = product_id.strip()
        if not normalized or len(normalized) > 40:
            raise ValueError("Provide a valid product ID.")
        with self.sessions() as session:
            product = session.get(Product, normalized)
            if product is None:
                return {"found": False, "product_id": normalized}
            return {
                "found": True,
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "price": str(product.price),
                "in_stock": product.inventory > 0,
                "inventory": product.inventory,
            }

    def check_order_status(self, order_id: str, customer_id: str) -> dict[str, Any]:
        order_key, customer_key = order_id.strip(), customer_id.strip()
        if not order_key or len(order_key) > 40 or not customer_key:
            raise ValueError("Provide valid order and customer IDs.")
        with self.sessions() as session:
            order = session.scalar(
                select(Order).where(
                    Order.order_id == order_key,
                    Order.customer_id == customer_key,
                )
            )
            if order is None:
                return {"found": False, "order_id": order_key}
            product = session.get(Product, order.product_id)
            return {
                "found": True,
                "order_id": order.order_id,
                "status": order.status,
                "product": product.name if product else order.product_id,
                "quantity": order.quantity,
                "created_at": order.created_at.isoformat(),
            }

    def place_order(
        self, customer_id: str, product_id: str, quantity: int
    ) -> dict[str, Any]:
        customer_key, product_key = customer_id.strip(), product_id.strip()
        if not customer_key or len(customer_key) > 40:
            raise ValueError("Provide a valid customer ID.")
        if not product_key or len(product_key) > 40:
            raise ValueError("Provide a valid product ID.")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity <= 10:
            raise ValueError("Quantity must be an integer from 1 to 10.")

        with self.sessions.begin() as session:
            customer = session.get(Customer, customer_key)
            product = session.get(Product, product_key, with_for_update=True)
            if customer is None:
                return {"created": False, "reason": "customer_not_found"}
            if product is None:
                return {"created": False, "reason": "product_not_found"}
            if product.inventory < quantity:
                return {
                    "created": False,
                    "reason": "insufficient_inventory",
                    "available": product.inventory,
                }
            product.inventory -= quantity
            order_id = f"ORD-{datetime.now(timezone.utc):%Y%m%d%H%M%S%f}"
            session.add(
                Order(
                    order_id=order_id,
                    customer_id=customer_key,
                    product_id=product_key,
                    quantity=quantity,
                    status="processing",
                    created_at=datetime.now(timezone.utc),
                )
            )
        return {"created": True, "order_id": order_id, "status": "processing"}


def database_location() -> str:
    if DATABASE_URL.startswith("sqlite:///"):
        return str(Path(DATABASE_URL.removeprefix("sqlite:///")))
    return "configured MySQL database"
