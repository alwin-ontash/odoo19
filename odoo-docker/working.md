# Working Guide — Hermes ↔ Odoo 19 via MCP

**Date Completed:** May 14, 2026  
**Status:** Fully working — Read + Write operations via Telegram

---

## Section 1: Docker Setup

### Step 1 — Create docker-compose.yml
File created at: `C:\Users\ontash\Downloads\odoo-docker\odoo-docker\docker-compose.yml`

```yaml
services:
  web:
    image: odoo:19
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - ./addons:/mnt/extra-addons
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo
    volumes:
      - odoo-db-data:/var/lib/postgresql/data

volumes:
  odoo-web-data:
  odoo-db-data:
```

### Step 2 — Start the containers
```powershell
cd C:\Users\ontash\Downloads\odoo-docker\odoo-docker
docker compose up -d
```

Two containers start:
- `odoo-docker-web-1` — Odoo 19 on port `8069`
- `odoo-docker-db-1` — PostgreSQL 15

### Step 3 — Access Odoo
Open browser: **http://localhost:8069**

- Login: `admin@gmail.com`
- Password: `admin1234`

---

## Section 2: Install Business Modules

### Step 1 — Why stop the web container first
Installing modules while the web container is running causes database serialization errors. Always stop web first.

```powershell
docker compose stop web
```

### Step 2 — Install modules via temporary container
```powershell
docker run --rm --network odoo-docker_default `
  -v odoo-docker_odoo-web-data:/var/lib/odoo `
  -v "C:\Users\ontash\Downloads\odoo-docker\odoo-docker\config:/etc/odoo" `
  -v "C:\Users\ontash\Downloads\odoo-docker\odoo-docker\addons:/mnt/extra-addons" `
  -e HOST=db -e USER=odoo -e PASSWORD=odoo `
  odoo:19 odoo -d odoo -i sale,account,stock,purchase --stop-after-init
```

### Step 3 — Restart web container
```powershell
docker compose start web
```

Modules installed:
- `sale` — Sales orders
- `account` — Invoices / accounting
- `stock` — Inventory / stock
- `purchase` — Purchase orders
- ~49 dependency modules (53 total)

---

## Section 3: Install MCP Addon in Odoo

### Step 1 — What is MCP
MCP (Model Context Protocol) is the communication protocol used by Hermes to query Odoo. The `muk_mcp` addon adds a `/mcp` HTTP endpoint to Odoo that accepts MCP requests.

### Step 2 — Install muk_mcp
The `addons/` folder (mounted at `/mnt/extra-addons`) contains `muk_mcp`.

In Odoo:
1. Go to **Apps** → remove the "Apps" filter → search **MCP**
2. Click **Install** on the `muk_mcp` addon

### Step 3 — Verify endpoint exists
After install, the MCP endpoint is available at:
```
http://localhost:8069/mcp
```

---

## Section 4: Generate MCP Key in Odoo

### Step 1 — Open API Key settings
In Odoo: **Settings → Users → [your user] → Preferences → Account Security → API Keys**

### Step 2 — Generate a key
- Click **Add a Key**
- Set scope to **Read Only**
- Copy the generated key

**MCP Key:** `qm6Sev4YKV6cl_kXfGfeCkXB-OAVA0ZK00LWAX1yk9A`

Scope: **Write** (changed from Read-Only — the UI does not allow editing scope after creation; change via DB: `UPDATE muk_mcp_key SET scope = 'write' WHERE id = 1`)

This key is used as a Bearer token in all MCP requests. It never expires unless manually deleted.

---

## Section 5a: Add Write Tools to muk_mcp (May 14, 2026)

Write tools are defined in `addons/muk_mcp/data/tool.xml`. After editing:

```powershell
# Upgrade module to load new tool records into DB
docker exec odoo-docker-web-1 odoo -u muk_mcp -d odoo --stop-after-init
# Restart web service
docker compose restart web
```

**Important XML rule:** Any `<` character in Python code inside a `<field>` tag must be escaped as `&lt;`.  
Example: `float(x) &lt; 0` not `float(x) < 0`

**Tools added:**

| Tool name | Category | What it does |
|---|---|---|
| `update_product_price` | write | Update `lst_price` / `standard_price` on `product.template` |
| `rename_product` | write | Update name, internal reference, sales description |
| `update_customer` | write | Edit any field on `res.partner` |
| `update_stock_quantity` | write | Set `inventory_quantity` on `stock.quant` and apply |

---

## Section 5: New Files Created (hermes-odoo/)

All files live at: `C:\Users\ontash\Downloads\odoo-docker\odoo-docker\hermes-odoo\`

### File 1 — `.env`
Stores credentials. Never committed to git.
```env
MCP_URL=http://localhost:8069
MCP_KEY=qm6Sev4YKV6cl_kXfGfeCkXB-OAVA0ZK00LWAX1yk9A
```

### File 2 — `odoo_client.py`
The MCP protocol client. Handles:
- Loading credentials from `.env`
- Opening an MCP session with Odoo
- Sending `search_read` queries and returning results

### File 3 — `odoo_tools.py`
Higher-level functions that call `odoo_client.py` and format results as plain text for Telegram:

**Read functions:**
- `show_last_sales_orders()`
- `show_unpaid_invoices()`
- `search_customer(name)`
- `search_product(name)`
- `show_product_stock(name)`

**Write functions (added May 14, 2026):**
- `update_product_price(product_id, sales_price, cost_price)`
- `rename_product(product_id, name, internal_reference, description)`
- `update_customer(customer_id, name, email, phone, mobile, street, street2, city, zip_code, country)`
- `update_stock_quantity(product_id, quantity, location_id)`

### File 4 — `test_odoo.py`
CLI test script. Run this to verify the connection works before using Telegram.
```bash
python3 test_odoo.py
```

### File 5 — `hermes-skill/SKILL.md`
The Hermes skill definition. Tells Hermes what commands to run when you ask Odoo questions in Telegram.

### File 6 — `requirements.txt`
Python dependencies:
- `requests`
- `python-dotenv`

---

## Section 6: How MCP Connection Works

### Step 1 — Client loads credentials
`odoo_client.py` reads `MCP_URL` and `MCP_KEY` from `.env` on startup.

### Step 2 — Initialize MCP session
Client sends a POST to `http://<MCP_URL>/mcp`:
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {"name": "hermes-odoo", "version": "2.0"},
    "capabilities": {}
  }
}
```
Header: `Authorization: Bearer <MCP_KEY>`

Odoo responds with a `Mcp-Session-Id` header (e.g. `abc123`).

### Step 3 — Confirm initialization
Client sends:
```json
{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
```
Header: `Mcp-Session-Id: abc123`

### Step 4 — Query data
Every data query calls `tools/call` with the `search_read` tool:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_read",
    "arguments": {
      "model": "sale.order",
      "domain": "[['state','in',['sale','done']]]",
      "fields": ["name", "partner_id", "amount_total"],
      "limit": 5
    }
  }
}
```

Odoo returns matching records as a JSON list.

### Step 5 — Session reuse
The `Mcp-Session-Id` is cached in memory. All subsequent calls reuse it — no re-authentication needed until the session expires.

---

## Section 7: VM Setup and Connection

### Step 1 — What is the VM
Hermes (the Telegram bot) runs inside a Linux virtual machine (VirtualBox). Odoo runs in Docker on the Windows host.

### Step 2 — How the VM reaches Odoo
VirtualBox exposes the Windows host to the VM at IP `10.0.2.2`. So from inside the VM:
```
http://10.0.2.2:8069  →  Odoo running on Windows host
```
No tunnel or port forwarding needed.

### Step 3 — Copy files to VM
```bash
scp -r hermes-odoo/ ubuntu@<VM_IP>:~/hermes-odoo/
```
Or copy files manually via nano/paste.

### Step 4 — Install Python dependencies on VM
```bash
cd ~/hermes-odoo
pip install -r requirements.txt
```

### Step 5 — Create .env on VM
```bash
nano ~/hermes-odoo/.env
```
Content:
```env
MCP_URL=http://10.0.2.2:8069
MCP_KEY=qm6Sev4YKV6cl_kXfGfeCkXB-OAVA0ZK00LWAX1yk9A
```

### Step 6 — Test connection from VM
```bash
cd ~/hermes-odoo
python3 test_odoo.py
```
Expected: sales orders, invoices, customer and product search results printed to terminal.

### Step 7 — Install Hermes skill
```bash
mkdir -p ~/.hermes/skills/erp/odoo
cp ~/hermes-odoo/hermes-skill/SKILL.md ~/.hermes/skills/erp/odoo/SKILL.md
```
Then restart Hermes.

---

## Section 8: How Telegram Queries Work (End-to-End)

```
You (Telegram)
    ↓  "show last sales orders"
Hermes Agent (VM)
    ↓  reads SKILL.md → runs python3 command
odoo_tools.py → show_last_sales_orders()
    ↓
odoo_client.py → MCP request to http://10.0.2.2:8069/mcp
    ↓
Odoo 19 (Docker on Windows) → returns records
    ↓
Formatted plain-text response
    ↓
Hermes → Telegram message back to you
```

---

## Section 9: Daily Startup

### Step 1 — Start Odoo on Windows
```powershell
cd C:\Users\ontash\Downloads\odoo-docker\odoo-docker
docker compose up -d
```

### Step 2 — Verify containers are running
```powershell
docker compose ps
```
Both `odoo-docker-web-1` and `odoo-docker-db-1` should show `Up`.

### Step 3 — Start Hermes on VM
Start the Hermes agent however it is configured (e.g. `systemctl start hermes` or run manually).

### Step 4 — Test via Telegram
Send a message to your Telegram bot, e.g.:
- "show last sales orders"
- "unpaid invoices"
- "search customer Admin"

---

## Credentials Reference

| Item | Value |
|---|---|
| Odoo URL (Windows) | `http://localhost:8069` |
| Odoo URL (from VM) | `http://10.0.2.2:8069` |
| Odoo login | `admin@gmail.com` |
| Odoo password | `admin1234` |
| MCP Key | `qm6Sev4YKV6cl_kXfGfeCkXB-OAVA0ZK00LWAX1yk9A` |
