"""
odoo_tools.py — Telegram-friendly Odoo data functions via MCP.

Each function calls odoo_client.call_mcp_tool(), formats the result into
a short readable string, and handles errors gracefully.
Register these as Hermes custom tools or skills.
"""

import json

from odoo_client import call_mcp_tool


# ---------------------------------------------------------------------------
# Internal helpers — name-to-ID resolution
# ---------------------------------------------------------------------------


def _resolve_product_template(search_name: str):
    """Return (template_id, None) or (None, error_str)."""
    try:
        matches = call_mcp_tool("search_read", {
            "model": "product.template",
            "domain": json.dumps([["name", "ilike", search_name], ["active", "=", True]]),
            "fields": ["id", "name"],
            "limit": 6,
        })
    except RuntimeError as exc:
        return None, f"Could not search products: {exc}"
    if not matches:
        return None, f"No product found matching '{search_name}'."
    if len(matches) > 1:
        lines = [f"Multiple products match '{search_name}'. Be more specific or use product_id:\n"]
        for m in matches[:5]:
            lines.append(f"• ID {m['id']}: {m['name']}")
        return None, "\n".join(lines)
    return matches[0]["id"], None


def _resolve_product_variant(search_name: str):
    """Return (variant_id, None) or (None, error_str)."""
    try:
        matches = call_mcp_tool("search_read", {
            "model": "product.product",
            "domain": json.dumps([["name", "ilike", search_name], ["active", "=", True]]),
            "fields": ["id", "name"],
            "limit": 6,
        })
    except RuntimeError as exc:
        return None, f"Could not search products: {exc}"
    if not matches:
        return None, f"No product found matching '{search_name}'."
    if len(matches) > 1:
        lines = [f"Multiple products match '{search_name}'. Be more specific or use product_id:\n"]
        for m in matches[:5]:
            lines.append(f"• ID {m['id']}: {m['name']}")
        return None, "\n".join(lines)
    return matches[0]["id"], None


def _resolve_partner(search_name: str):
    """Return (partner_id, None) or (None, error_str)."""
    try:
        matches = call_mcp_tool("search_read", {
            "model": "res.partner",
            "domain": json.dumps([["name", "ilike", search_name]]),
            "fields": ["id", "name"],
            "limit": 6,
        })
    except RuntimeError as exc:
        return None, f"Could not search customers: {exc}"
    if not matches:
        return None, f"No customer found matching '{search_name}'."
    if len(matches) > 1:
        lines = [f"Multiple customers match '{search_name}'. Be more specific or use customer_id:\n"]
        for m in matches[:5]:
            lines.append(f"• ID {m['id']}: {m['name']}")
        return None, "\n".join(lines)
    return matches[0]["id"], None


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
            "fields": ["id", "name", "email", "phone", "city", "country_id"],
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
        detail = f"• *{p['name']}* (ID: {p['id']})"
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
            "fields": ["id", "name", "default_code", "list_price", "type", "product_tmpl_id"],
            "limit": 5,
        })
    except RuntimeError as exc:
        return f"Could not search products: {exc}"

    if not products:
        return f"No products found matching '{name}'."

    lines = [f"*Products matching '{name}':*\n"]
    for p in products:
        ref = f"[{p['default_code']}] " if p.get("default_code") else ""
        tmpl_id = p["product_tmpl_id"][0] if p.get("product_tmpl_id") else "?"
        variant_id = p.get("id", "?")
        lines.append(
            f"• {ref}*{p['name']}* | ${p['list_price']:,.2f} | Type: {p['type']}\n"
            f"  Template ID: {tmpl_id} (rename/price) | Variant ID: {variant_id} (stock)"
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


# ---------------------------------------------------------------------------
# Write — Products
# ---------------------------------------------------------------------------


def update_product_price(product_id: int = None, sales_price: float = None, cost_price: float = None, search_name: str = None) -> str:
    """Update the sales price and/or cost price of a product template."""
    if sales_price is None and cost_price is None:
        return "Provide at least one of: sales_price or cost_price."

    if product_id is None:
        if not search_name:
            return "Provide either product_id or search_name."
        product_id, err = _resolve_product_template(search_name)
        if err:
            return err

    args = {"id": product_id}
    if sales_price is not None:
        args["sales_price"] = sales_price
    if cost_price is not None:
        args["cost_price"] = cost_price

    try:
        result = call_mcp_tool("update_product_price", args)
    except RuntimeError as exc:
        return f"Could not update product price: {exc}"

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result['error']}"

    name = result.get("name", f"ID {product_id}")
    lines = [f"*Product updated: {name}*\n"]
    if "sales_price" in result:
        lines.append(f"• Sales price: ${result['sales_price']:,.2f}")
    if "cost_price" in result:
        lines.append(f"• Cost price: ${result['cost_price']:,.2f}")
    return "\n".join(lines)


def rename_product(product_id: int = None, name: str = None, internal_reference: str = None, description: str = None, search_name: str = None) -> str:
    """Rename a product and/or update its internal reference and sales description."""
    if not name and internal_reference is None and description is None:
        return "Provide at least one of: name, internal_reference, description."

    if product_id is None:
        if not search_name:
            return "Provide either product_id or search_name."
        product_id, err = _resolve_product_template(search_name)
        if err:
            return err

    args = {"id": product_id}
    if name:
        args["name"] = name
    if internal_reference is not None:
        args["internal_reference"] = internal_reference
    if description is not None:
        args["description"] = description

    try:
        result = call_mcp_tool("rename_product", args)
    except RuntimeError as exc:
        return f"Could not rename product: {exc}"

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result['error']}"

    updated = result.get("updated", [])
    lines = [f"*Product updated (ID {product_id}):*\n"]
    lines.append(f"• Name: {result.get('name', '')}")
    if "default_code" in updated or internal_reference is not None:
        lines.append(f"• Internal ref: {result.get('internal_reference') or '(cleared)'}")
    if "description_sale" in updated or description is not None:
        lines.append(f"• Description: {result.get('description') or '(cleared)'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Write — Customers
# ---------------------------------------------------------------------------


def update_customer(
    customer_id: int = None,
    name: str = None,
    email: str = None,
    phone: str = None,
    mobile: str = None,
    street: str = None,
    street2: str = None,
    city: str = None,
    zip_code: str = None,
    country: str = None,
    search_name: str = None,
) -> str:
    """Update a customer or contact's details in Odoo."""
    if customer_id is None:
        if not search_name:
            return "Provide either customer_id or search_name."
        customer_id, err = _resolve_partner(search_name)
        if err:
            return err

    args = {"id": customer_id}
    if name is not None:
        args["name"] = name
    if email is not None:
        args["email"] = email
    if phone is not None:
        args["phone"] = phone
    if mobile is not None:
        args["mobile"] = mobile
    if street is not None:
        args["street"] = street
    if street2 is not None:
        args["street2"] = street2
    if city is not None:
        args["city"] = city
    if zip_code is not None:
        args["zip"] = zip_code
    if country is not None:
        args["country"] = country

    if len(args) == 1:
        return "Provide at least one field to update."

    try:
        result = call_mcp_tool("update_customer", args)
    except RuntimeError as exc:
        return f"Could not update customer: {exc}"

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result['error']}"

    lines = [f"*Customer updated: {result.get('name', f'ID {customer_id}')}*\n"]
    if result.get("email"):
        lines.append(f"• Email: {result['email']}")
    if result.get("phone"):
        lines.append(f"• Phone: {result['phone']}")
    if result.get("mobile"):
        lines.append(f"• Mobile: {result['mobile']}")
    address_parts = filter(None, [result.get("street"), result.get("city"), result.get("zip"), result.get("country")])
    address = ", ".join(address_parts)
    if address:
        lines.append(f"• Address: {address}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Write — Stock
# ---------------------------------------------------------------------------


def update_stock_quantity(product_id: int = None, quantity: float = None, location_id: int = None, search_name: str = None) -> str:
    """Set the on-hand stock quantity for a product variant via inventory adjustment."""
    if quantity is None:
        return "Provide quantity."

    if product_id is None:
        if not search_name:
            return "Provide either product_id or search_name."
        product_id, err = _resolve_product_variant(search_name)
        if err:
            return err

    args = {"product_id": product_id, "quantity": quantity}
    if location_id is not None:
        args["location_id"] = location_id

    try:
        result = call_mcp_tool("update_stock_quantity", args)
    except RuntimeError as exc:
        return f"Could not update stock: {exc}"

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result['error']}"

    product_name = result.get("product_name", f"ID {product_id}")
    location = result.get("location", "")
    new_qty = result.get("new_quantity", quantity)
    return (
        f"*Stock updated: {product_name}*\n"
        f"• Location: {location}\n"
        f"• New on-hand quantity: {new_qty:.0f}"
    )


# ---------------------------------------------------------------------------
# Create — Products & Customers
# ---------------------------------------------------------------------------


def create_product(
    name: str,
    sales_price: float = None,
    cost_price: float = None,
    internal_reference: str = None,
    description: str = None,
) -> str:
    """Create a new product in Odoo."""
    if not name or not name.strip():
        return "Product name is required."

    args = {"name": name.strip()}
    if sales_price is not None:
        args["sales_price"] = sales_price
    if cost_price is not None:
        args["cost_price"] = cost_price
    if internal_reference:
        args["internal_reference"] = internal_reference
    if description:
        args["description"] = description

    try:
        result = call_mcp_tool("create_product", args)
    except RuntimeError as exc:
        return f"Could not create product: {exc}"

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result['error']}"

    pid = result.get("id", "?")
    pname = result.get("name", name)
    lines = [f"*Product created: {pname}* (ID: {pid})\n"]
    if "sales_price" in result:
        lines.append(f"• Sales price: ${result['sales_price']:,.2f}")
    if "cost_price" in result:
        lines.append(f"• Cost price: ${result['cost_price']:,.2f}")
    if result.get("internal_reference"):
        lines.append(f"• Internal ref: {result['internal_reference']}")
    return "\n".join(lines)


def create_customer(
    name: str,
    email: str = None,
    phone: str = None,
    street: str = None,
    city: str = None,
    zip_code: str = None,
    country: str = None,
) -> str:
    """Create a new customer in Odoo."""
    if not name or not name.strip():
        return "Customer name is required."

    args = {"name": name.strip()}
    if email:
        args["email"] = email
    if phone:
        args["phone"] = phone
    if street:
        args["street"] = street
    if city:
        args["city"] = city
    if zip_code:
        args["zip"] = zip_code
    if country:
        args["country"] = country

    try:
        result = call_mcp_tool("create_customer", args)
    except RuntimeError as exc:
        return f"Could not create customer: {exc}"

    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result['error']}"

    cid = result.get("id", "?")
    cname = result.get("name", name)
    lines = [f"*Customer created: {cname}* (ID: {cid})\n"]
    if result.get("email"):
        lines.append(f"• Email: {result['email']}")
    if result.get("phone"):
        lines.append(f"• Phone: {result['phone']}")
    addr_parts = [result.get("street", ""), result.get("city", ""), result.get("zip", ""), result.get("country", "")]
    addr = ", ".join(p for p in addr_parts if p)
    if addr:
        lines.append(f"• Address: {addr}")
    return "\n".join(lines)


def prompt_for_customer_details() -> str:
    return (
        "Please provide the customer details in this format:\n"
        "\n"
        "Name (required):\n"
        "Email (optional):\n"
        "Phone (optional):\n"
        "Street (optional):\n"
        "City (optional):\n"
        "ZIP code (optional):\n"
        "Country (optional):\n"
        "\nExample:\n"
        "Name: John Doe\n"
        "Email: john.doe@example.com\n"
        "Phone: +1 555-123-4567\n"
        "City: New York\n"
        "Country: United States"
    )

def prompt_for_product_details() -> str:
    return (
        "Please provide the product details in this format:\n"
        "\n"
        "Name (required):\n"
        "Sales Price (optional):\n"
        "Cost Price (optional):\n"
        "Internal Reference (optional):\n"
        "Description (optional):\n"
        "\nExample:\n"
        "Name: Wireless Keyboard\n"
        "Sales Price: 49.99\n"
        "Cost Price: 30.00\n"
        "Internal Reference: KB-001\n"
        "Description: Compact wireless keyboard with Bluetooth"
    )
