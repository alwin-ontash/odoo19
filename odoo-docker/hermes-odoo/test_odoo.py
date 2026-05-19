#!/usr/bin/env python3
"""
test_odoo.py — CLI test script for the Odoo MCP connector.

Run this BEFORE connecting Hermes to verify every function works.
Requires a valid .env file in the same directory with MCP_URL and MCP_KEY.

Usage:
    python test_odoo.py
    python test_odoo.py --customer "ABC Traders"
    python test_odoo.py --product "Laptop"
"""

import argparse
import sys

from odoo_tools import (
    search_customer,
    search_product,
    show_last_sales_orders,
    show_product_stock,
    show_unpaid_invoices,
)


def divider(title: str) -> None:
    width = 55
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print("=" * width)


def run_all_tests(customer_name: str = "Admin", product_name: str = "product") -> None:
    """Run every Odoo tool function and print the results."""

    divider("1. Last 5 Sales Orders")
    print(show_last_sales_orders(limit=5))

    divider("2. Unpaid Invoices")
    print(show_unpaid_invoices(limit=5))

    divider(f"3. Search Customer: '{customer_name}'")
    print(search_customer(customer_name))

    divider(f"4. Search Product: '{product_name}'")
    print(search_product(product_name))

    divider(f"5. Stock for: '{product_name}'")
    print(show_product_stock(product_name))

    print(f"\n{'=' * 55}")
    print("  All tests complete.")
    print("=" * 55)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the Odoo connector from the command line."
    )
    parser.add_argument(
        "--customer",
        default="Admin",
        help="Customer name to search (default: Admin)",
    )
    parser.add_argument(
        "--product",
        default="product",
        help="Product name to search and check stock for (default: product)",
    )
    args = parser.parse_args()

    print("Odoo Connector — CLI Test")
    print("Make sure your .env file is configured before running this.\n")

    try:
        run_all_tests(customer_name=args.customer, product_name=args.product)
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
