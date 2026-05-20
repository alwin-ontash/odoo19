---
name: odoo
description: "Query Odoo 19 ERP data: sales orders, invoices, customers, products, stock."
version: 2.0.1
author: custom
license: MIT
metadata:
  hermes:
    tags: [Odoo, ERP, Sales, Invoices, Inventory, CRM]
prerequisites:
  env_vars: []
---

# Odoo ERP

Query live Odoo 19 business data. All commands use Python scripts in ~/hermes-odoo/.

## Show Last Sales Orders

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import show_last_sales_orders; print(show_last_sales_orders())"

## Show Unpaid Invoices

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import show_unpaid_invoices; print(show_unpaid_invoices())"

## Search Customer

Replace NAME with the customer name:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import search_customer; print(search_customer('NAME'))"

## Search Product

Replace NAME with the product name:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import search_product; print(search_product('NAME'))"

## Check Product Stock

Replace NAME with the product name:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import show_product_stock; print(show_product_stock('NAME'))"

## Update Product Sales Price

By product name:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import update_product_price; print(update_product_price(search_name='NAME', sales_price=PRICE))"

By template ID:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import update_product_price; print(update_product_price(product_id=ID, sales_price=PRICE))"

To update cost price instead (or both):

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import update_product_price; print(update_product_price(search_name='NAME', sales_price=PRICE, cost_price=COST))"

## Rename Product

By product name:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import rename_product; print(rename_product(search_name='OLD NAME', name='NEW NAME'))"

By template ID:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import rename_product; print(rename_product(product_id=ID, name='NEW NAME'))"

To also update internal reference:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import rename_product; print(rename_product(search_name='OLD NAME', name='NEW NAME', internal_reference='REF'))"

## Update Customer Details

By customer name:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import update_customer; print(update_customer(search_name='NAME', email='EMAIL', phone='PHONE', city='CITY', country='COUNTRY'))"

By partner ID:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import update_customer; print(update_customer(customer_id=ID, email='EMAIL', phone='PHONE', city='CITY', country='COUNTRY'))"

## Update Stock Quantity

By product name:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import update_stock_quantity; print(update_stock_quantity(search_name='NAME', quantity=QTY))"

By variant ID (product.product):

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import update_stock_quantity; print(update_stock_quantity(product_id=ID, quantity=QTY))"

## Create Product

Replace values as needed. Only NAME is required; all other arguments are optional:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import create_product; print(create_product('NAME', sales_price=PRICE, cost_price=COST, internal_reference='SKU', description='DESC'))"

Example — create a product with just a name and price:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import create_product; print(create_product('Wireless Keyboard', sales_price=49.99))"

## Create Customer

Replace values as needed. Only NAME is required; all other arguments are optional:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import create_customer; print(create_customer('NAME', email='EMAIL', phone='PHONE', city='CITY', country='COUNTRY'))"

Example — create a customer with name and email:

    python3 -c "import sys; sys.path.insert(0,'$HOME/hermes-odoo'); from odoo_tools import create_customer; print(create_customer('Acme Corp', email='contact@acme.com', city='New York', country='United States'))"

## Notes

- No setup required. Connection is pre-configured.
- Odoo runs in Docker on the Windows host at 10.0.2.2:8069

## Install

Copy this file to:

    ~/.hermes/skills/erp/odoo/SKILL.md

Then restart Hermes.
