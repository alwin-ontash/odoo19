# Hermes Agent ↔ Odoo 19 Integration Plan

---

## 1. Project Overview

This project connects your **Telegram chat** to your **Odoo 19 ERP system** through an intelligent agent called **Hermes**, running inside a VM.

### How it works, step by step:

1. You send a message to your Telegram bot (e.g. _"Show last 5 sales orders"_).
2. Telegram delivers the message to **Hermes Agent** running inside your VM.
3. Hermes recognises the intent and calls the appropriate **Odoo Python Connector** function.
4. The connector sends an API request through a **Cloud Tunnel URL** (ngrok or Cloudflare Tunnel) that points to your host machine.
5. The request reaches **Odoo 19 running in Docker** on port `8069`.
6. Odoo queries its **PostgreSQL database** and returns the result.
7. The connector formats the data and returns it to Hermes.
8. Hermes sends a clean, readable reply back to you in **Telegram**.

---

## 2. Architecture Diagram

```
Telegram Chat
    │
    ▼
Hermes Agent (inside VM)
    │
    ▼
Odoo Python Connector (odoo_client.py / odoo_tools.py)
    │
    ▼
Cloud Tunnel URL (ngrok / Cloudflare Tunnel)
    │
    ▼
Odoo 19 Docker Container (host machine, port 8069)
    │
    ▼
Odoo PostgreSQL Database
```

---

## 3. Requirements

### Infrastructure
- [ ] Odoo 19 running in Docker on your host machine
- [ ] Odoo accessible on port `8069` (confirmed working)
- [ ] Cloud tunnel — **Cloudflare Tunnel** (stable) or **ngrok** (quick testing)
- [ ] Hermes Agent running inside your VM

### Odoo Configuration
- [ ] Odoo API key generated for a dedicated API user
- [ ] Odoo database name (currently: `odoo`)
- [ ] Dedicated Odoo API user with read-only access (do **not** use admin)

### Hermes / VM Setup
- [ ] Telegram bot connected to Hermes
- [ ] Python 3.10+ available in the VM
- [ ] `requests` library installed
- [ ] `python-dotenv` library installed
- [ ] Authorized Telegram user ID restriction configured

### Python Dependencies
```
requests
python-dotenv
```

---

## 4. Environment Variables

Create a `.env` file in your project directory. **Never commit this file.**

```env
# .env.example — copy to .env and fill in your values

ODOO_URL=https://your-cloud-tunnel-url
ODOO_DB=your_odoo_database_name
ODOO_API_KEY=your_odoo_api_key
AUTHORIZED_TELEGRAM_USER_ID=your_telegram_user_id
```

> **Tip:** Add `.env` to your `.gitignore` immediately.

---

## 5. Cloud Tunnel Plan

You need a publicly accessible URL so your VM can reach Odoo running on your host machine. Choose one option:

---

### Option A — ngrok (Quick Testing)

1. Download and install ngrok: https://ngrok.com/download
2. Authenticate: `ngrok config add-authtoken <your_token>`
3. Start the tunnel:
   ```bash
   ngrok http 8069
   ```
4. Copy the HTTPS URL shown (e.g. `https://abc123.ngrok-free.app`)
5. Set it as your `ODOO_URL` in `.env`

> **Note:** Free ngrok URLs change every time you restart. Use Cloudflare for a stable URL.

---

### Option B — Cloudflare Tunnel (Stable, Recommended)

1. Install `cloudflared` on your host machine:
   - Windows: Download from https://github.com/cloudflare/cloudflared/releases
2. Log in:
   ```bash
   cloudflared tunnel login
   ```
3. Create a tunnel:
   ```bash
   cloudflared tunnel create odoo-tunnel
   ```
4. Route DNS to a subdomain (requires a domain on Cloudflare):
   ```bash
   cloudflared tunnel route dns odoo-tunnel odoo.yourdomain.com
   ```
5. Create a config file `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: <your-tunnel-id>
   credentials-file: /path/to/.cloudflared/<tunnel-id>.json
   ingress:
     - hostname: odoo.yourdomain.com
       service: http://localhost:8069
     - service: http_status:404
   ```
6. Run the tunnel:
   ```bash
   cloudflared tunnel run odoo-tunnel
   ```
7. Set `ODOO_URL=https://odoo.yourdomain.com` in `.env`

> **Bonus:** Enable **Cloudflare Access** on this tunnel for an extra layer of security.

---

## 6. Odoo API Plan

### Authentication Method
- Odoo 19 supports the **External JSON-RPC 2 API**
- Authenticate requests using:
  ```
  Authorization: Bearer <ODOO_API_KEY>
  ```
- If required by your setup, also send:
  ```
  X-Odoo-Database: your_odoo_database_name
  ```

### Setup Steps
1. Log into Odoo as admin
2. Go to **Settings → Users & Companies → Users**
3. Create a new user: `api_readonly@yourdomain.com`
4. Set their role to **Internal User** with minimal permissions
5. Go to **Settings → Technical → API Keys**
6. Generate an API key for this user
7. Copy the key into your `.env` as `ODOO_API_KEY`

### Design Principles
- Start with **read-only** data fetching only
- Do not add write actions until read is fully tested
- Never log or expose API keys in any output

---

## 7. Odoo Models to Support

| Model | Purpose |
|---|---|
| `sale.order` | Sales orders |
| `account.move` | Invoices (filter by payment_state) |
| `res.partner` | Customers and vendors |
| `product.product` | Products |
| `stock.quant` | Stock quantities per location |
| `crm.lead` | CRM leads _(optional, add later)_ |

---

## 8. Initial Features

Implement these functions first before adding anything more complex:

| Function | Description |
|---|---|
| `show_last_sales_orders(limit=5)` | Fetch the 5 most recent sales orders |
| `show_unpaid_invoices(limit=5)` | Fetch unpaid/overdue invoices |
| `search_customer(name)` | Search for a customer by name |
| `search_product(name)` | Search for a product by name |
| `show_product_stock(product_name)` | Get current stock level for a product |

---

## 9. Suggested File Structure

```
hermes-odoo/
├── plan.md              ← This file
├── .env                 ← Your secrets (never commit)
├── .env.example         ← Template for others
├── .gitignore           ← Must include .env
├── requirements.txt     ← Python dependencies
├── odoo_client.py       ← Low-level API connector
├── odoo_tools.py        ← Formatted Telegram-ready functions
├── test_odoo.py         ← CLI test script
└── README.md            ← Setup guide
```

---

## 10. Python Connector Plan

### `odoo_client.py` — Low-Level API Connector

**Responsibilities:**
- Load environment variables from `.env` using `python-dotenv`
- Implement a central `call_odoo(model, method, payload)` function
- Set proper headers: `Authorization: Bearer`, `Content-Type: application/json`
- Handle HTTP timeouts (set `timeout=10` seconds minimum)
- Catch and handle HTTP errors gracefully
- **Never** print or log API keys, even in debug mode
- Return raw JSON results for `odoo_tools.py` to format

### `odoo_tools.py` — Telegram-Friendly Formatter

**Responsibilities:**
- Call functions from `odoo_client.py`
- Format results as short, readable Telegram messages
- Truncate long lists (max 5 items by default)
- Return plain text or Markdown formatted strings
- Handle empty results gracefully (e.g. _"No unpaid invoices found."_)

### `test_odoo.py` — Local CLI Tester

**Responsibilities:**
- Import and call all functions from `odoo_tools.py`
- Allow running from the command line: `python test_odoo.py`
- Print results to terminal for verification
- Test every function before connecting Hermes
- Must work independently of Hermes and Telegram

---

## 11. Hermes Integration Plan

### Registering Odoo as Hermes Tools

Register each Odoo function as a **custom tool or skill** in Hermes, so it can call them based on natural language intent.

### Intent → Function Mapping

| Telegram Message Intent | Hermes Calls |
|---|---|
| "Show last 5 sales orders" | `show_last_sales_orders(limit=5)` |
| "Show unpaid invoices" | `show_unpaid_invoices(limit=5)` |
| "Find customer ABC Traders" | `search_customer("ABC Traders")` |
| "Show stock for Laptop" | `show_product_stock("Laptop")` |
| "Search product Keyboard" | `search_product("Keyboard")` |

### Security in Hermes
- Always check `AUTHORIZED_TELEGRAM_USER_ID` before executing any Odoo tool
- Reject all requests from unauthorized user IDs silently or with a generic message
- Never expose raw Odoo error messages in Telegram replies
- Log only safe metadata (e.g. function name called, timestamp) — never log data content

### Response Format
- Keep responses short and Telegram-friendly
- Use plain text or simple Markdown (`*bold*`, `_italic_`)
- Limit lists to 5 items maximum
- Include a summary line (e.g. _"Found 3 unpaid invoices:"_)

---

## 12. Telegram Test Messages

Use these messages to test the full integration end-to-end:

```
Show last 5 Odoo sales orders
Show unpaid invoices from Odoo
Find customer ABC Traders
Show stock for Product Name
Search product Laptop
```

---

## 13. Security Checklist

- [ ] Do **not** use the Odoo `admin` user for the API
- [ ] Create a dedicated API user with minimal permissions
- [ ] Start with read-only access only
- [ ] Store all secrets in `.env`, never hardcoded in source files
- [ ] Add `.env` to `.gitignore` — never commit it
- [ ] Restrict Telegram access to `AUTHORIZED_TELEGRAM_USER_ID` only
- [ ] Always use an HTTPS tunnel URL (never plain HTTP)
- [ ] Enable **Cloudflare Access** if using Cloudflare Tunnel
- [ ] Log only safe metadata — never log Odoo data or API responses
- [ ] Never expose raw Odoo error messages to Telegram users
- [ ] Set API request timeouts to prevent hanging connections
- [ ] Rotate API keys periodically

---

## 14. Testing Checklist

Work through these in order — each step depends on the previous:

- [ ] Odoo opens locally at http://localhost:8069 ✅ (confirmed working)
- [ ] Cloud tunnel URL opens Odoo in browser
- [ ] Hermes VM can `curl` the tunnel URL successfully
- [ ] Odoo API key is valid (test with a simple API call)
- [ ] `test_odoo.py` can fetch sales orders from terminal
- [ ] `test_odoo.py` can fetch unpaid invoices from terminal
- [ ] `test_odoo.py` can search for a customer from terminal
- [ ] `test_odoo.py` can fetch product stock from terminal
- [ ] Telegram can send a message to Hermes bot
- [ ] Hermes receives the message and calls the correct Odoo tool
- [ ] Telegram receives a formatted Odoo data response

---

## 15. Future Enhancements

Once the read-only integration is stable, consider adding:

- [ ] **Create sales order** from Telegram
- [ ] **Update customer info** (name, phone, email)
- [ ] **Create CRM lead** from Telegram conversation
- [ ] **Send invoice status** (paid / overdue / draft)
- [ ] **Daily sales summary** — scheduled morning report via Telegram
- [ ] **Low stock alerts** — notify when stock falls below threshold
- [ ] **Role-based Telegram permissions** — different users see different data
- [ ] **Audit logging** — track every Odoo action taken via Telegram

---

> **Start simple. Get read-only working first. Then expand.**
