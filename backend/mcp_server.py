from __future__ import annotations

from backend.database import StoreService

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise RuntimeError("Install requirements.txt to run the MCP server.") from exc

mcp = FastMCP("ecomm-support-store")
store = StoreService()


@mcp.tool()
def get_product_details(product_id: str) -> dict:
    """Return a product's description, price, and stock status by product ID."""
    return store.get_product_details(product_id)


@mcp.tool()
def check_order_status(order_id: str, customer_id: str) -> dict:
    """Return order status only when the order belongs to the supplied customer."""
    return store.check_order_status(order_id, customer_id)


@mcp.tool()
def place_order(customer_id: str, product_id: str, quantity: int) -> dict:
    """Place an order for one to ten units of an in-stock product."""
    return store.place_order(customer_id, product_id, quantity)


if __name__ == "__main__":
    mcp.run(transport="stdio")
