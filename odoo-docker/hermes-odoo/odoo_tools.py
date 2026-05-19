"""
odoo_tools.py — Telegram-friendly Odoo data functions via MCP.

Each function calls odoo_client.call_mcp_tool(), formats the result into
a short readable string, and handles errors gracefully.
Register these as Hermes custom tools or skills.
"""

import json

from odoo_client import call_mcp_tool


# ---------------------------------------------------------------------------
# Sales Orders
# ---------------------------------------------------------------------------


def show_last_sales_orders(limit: int = 5) -> str:
    """Return the most recent confirmed sales orders as a formatted string."""
    try:
        orders = call_mcp_tool("search_read", {
            "model": "sale.order",
            "domain": json.dumps([["state", "in", ["sale", "done"]]]),
            "fields": ["name", "partner_id", "amount_total", "state", "date_order"],
            "limit": limit,
            "order": "date_order desc",
        })
    except RuntimeError as exc:
        return f"Could not fetch sales orders: {exc}"

    if not orders:
        return "No confirmed sales orders found."

    lines = [f"*Last {len(orders)} Sales Orders:*\n"]
    for order in orders:
        customer = order["partner_id"][1] if order.get("partner_id") else "Unknown"
        date = str(order.get("date_order", ""))[:10]
        lines.append(
            f"• *{order['name']}* | {customer} | ${order['amount_total']:,.2f} | {date}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------


def show_unpaid_invoices(limit: int = 5) -> str:
    """Return unpaid or partially paid customer invoices as a formatted string."""
    try:
        invoices = call_mcp_tool("search_read", {
            "model": "account.move",
            "domain": json.dumps([
                ["move_type", "=", "out_invoice"],
                ["payment_state", "in", ["not_paid", "partial"]],
                ["state", "=", "posted"],
            ]),
            "fields": ["name", "partner_id", "amount_residual", "invoice_date_due", "payment_state"],
            "limit": limit,
            "order": "invoice_date_due asc",
        })
    except RuntimeError as exc:
        return f"Could not fetch invoices: {exc}"

    if not invoices:
        return "No unpaid invoices found."

    lines = [f"*Unpaid Invoices ({len(invoices)} shown):*\n"]
    for inv in invoices:
        customer = inv["partner_id"][1] if inv.get("partner_id") else "Unknown"
        due = inv.get("invoice_date_due") or "No due date"
        status = "Partial" if inv["payment_state"] == "partial" else "Unpaid"
        lines.append(
            f"• *{inv['name']}* | {customer} | Due: {due} | Owed: ${inv['amount_residual']:,.2f} | {status}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


def search_customer(name: str) -> str:
    """Search for customers by name and return a formatted summary."""
    name = (name or "").strip()
    if not name:
        return "Please provide a customer name to search."

    try:
        partners = call_mcp_tool("search_read", {
            "model": "res.partner",
            "domain": json.dumps([["name", "ilike", name], ["is_company", "=", True]]),
            "fields": ["name", "email", "phone", "city", "country_id"],
            "limit": 5,
        })
    except RuntimeError as exc:
        return f"Could not search customers: {exc}"

    if not partners:
        return f"No customers found matching '{name}'."

    lines = [f"*Customers matching '{name}':*\n"]
    for p in partners:
        country = p["country_id"][1] if p.get("country_id") else ""
        city = p.get("city") or ""
        location = ", ".join(filter(None, [city, country]))
        detail = f"• *{p['name']}*"
        detail += f" | {p.get('email') or 'No email'}"
        detail += f" | {p.get('phone') or 'No phone'}"
        if location:
            detail += f" | {location}"
        lines.append(detail)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


def search_product(name: str) -> str:
    """Search for active products by name and return a formatted summary."""
    name = (name or "").strip()
    if not name:
        return "Please provide a product name to search."

    try:
        products = call_mcp_tool("search_read", {
            "model": "product.product",
            "domain": json.dumps([["name", "ilike", name], ["active", "=", True]]),
            "fields": ["name", "default_code", "list_price", "type"],
            "limit": 5,
        })
    except RuntimeError as exc:
        return f"Could not search products: {exc}"

    if not products:
        return f"No products found matching '{name}'."

    lines = [f"*Products matching '{name}':*\n"]
    for p in products:
        ref = f"[{p['default_code']}] " if p.get("default_code") else ""
        lines.append(
            f"• {ref}*{p['name']}* | ${p['list_price']:,.2f} | Type: {p['type']}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Stock
# ---------------------------------------------------------------------------


def show_product_stock(product_name: str) -> str:
    """Return current stock levels for products matching the given name."""
    product_name = (product_name or "").strip()
    if not product_name:
        return "Please provide a product name."

    # Step 1: find matching products
    try:
        products = call_mcp_tool("search_read", {
            "model": "product.product",
            "domain": json.dumps([["name", "ilike", product_name], ["active", "=", True]]),
            "fields": ["id", "name", "default_code"],
            "limit": 5,
        })
    except RuntimeError as exc:
        return f"Could not search products: {exc}"

    if not products:
        return f"No products found matching '{product_name}'."

    product_ids = [p["id"] for p in products]

    # Step 2: fetch stock quantities for those products
    try:
        quants = call_mcp_tool("search_read", {
            "model": "stock.quant",
            "domain": json.dumps([
                ["product_id", "in", product_ids],
                ["location_id.usage", "=", "internal"],
            ]),
            "fields": ["product_id", "location_id", "quantity", "reserved_quantity"],
            "limit": 20,
        })
    except RuntimeError as exc:
        return f"Could not fetch stock data: {exc}"

    if not quants:
        names = ", ".join(p["name"] for p in products)
        return f"No internal stock found for: {names}"

    lines = [f"*Stock for '{product_name}':*\n"]
    for q in quants:
        product = q["product_id"][1] if q.get("product_id") else "Unknown"
        location = q["location_id"][1] if q.get("location_id") else "Unknown"
        on_hand = q.get("quantity", 0)
        reserved = q.get("reserved_quantity", 0)
        available = on_hand - reserved
        lines.append(
            f"• *{product}* | {location} | On hand: {on_hand:.0f} | Available: {available:.0f}"
        )
    return "\n".join(lines)
