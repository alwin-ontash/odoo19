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

## Notes

- No setup required. Connection is pre-configured.
- Odoo runs in Docker on the Windows host at 10.0.2.2:8069

## Install

Copy this file to:

    ~/.hermes/skills/erp/odoo/SKILL.md

Then restart Hermes.
