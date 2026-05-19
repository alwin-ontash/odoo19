# Project Progress — Hermes ↔ Odoo 19 Integration

**Last updated:** May 14, 2026  
**Status:** COMPLETE — Read + Write operations fully working via Telegram ↔ Hermes ↔ Odoo

---

## What Has Been Completed

### 1. Odoo 19 Running in Docker
- Docker Compose file located at: `C:\Users\ontash\Downloads\odoo-docker\odoo-docker\docker-compose.yml`
- Two containers running: `odoo-docker-web-1` (port 8069) and `odoo-docker-db-1` (PostgreSQL)
- To start: `cd C:\Users\ontash\Downloads\odoo-docker\odoo-docker; docker compose up -d`
- Odoo accessible locally at: http://localhost:8069

### 2. Admin Login Reset
- Login: `admin@gmail.com`
- Password reset to: `admin1234`
- Reset was done via Odoo shell inside the container

### 3. Business Modules Installed
The following modules were installed via a temporary Docker container (to avoid concurrency conflict):
- `sale` — Sales orders
- `account` — Invoices / accounting
- `stock` — Inventory / stock
- `purchase` — Purchase orders
- Plus ~49 dependencies (53 total modules installed)

Install command used:
```powershell
docker run --rm --network odoo-docker_default `
  -v odoo-docker_odoo-web-data:/var/lib/odoo `
  -v "C:\Users\ontash\Downloads\odoo-docker\odoo-docker\config:/etc/odoo" `
  -v "C:\Users\ontash\Downloads\odoo-docker\odoo-docker\addons:/mnt/extra-addons" `
  -e HOST=db -e USER=odoo -e PASSWORD=odoo `
  odoo:19 odoo -d odoo -i sale,account,stock,purchase --stop-after-init
```

### 4. Odoo MCP Key Generated
- MCP key generated via Odoo → Settings → Users → Preferences → Account Security → API Keys
- **MCP Key:** `qm6Sev4YKV6cl_kXfGfeCkXB-OAVA0ZK00LWAX1yk9A`
- Scope: Read Only
- Used as Bearer token in MCP requests (NOT used for JSON-RPC authenticate)

### 5. API Verified Working from Windows Host
Confirmed with curl — returns real Odoo data:
```json
{"result": [{"id": 1, "name": "My Company", "email": "admin@gmail.com"}]}
```

### 6. hermes-odoo/ Project Files Created
All files created at: `C:\Users\ontash\Downloads\odoo-docker\odoo-docker\hermes-odoo\`

| File | Status |
|---|---|
| `.env` | Done (MCP_URL + MCP_KEY) |
| `.gitignore` | Done |
| `requirements.txt` | Done |
| `odoo_client.py` | Done (MCP protocol — `/mcp` endpoint + Bearer token) |
| `odoo_tools.py` | Done (plain-text output for Telegram) |
| `test_odoo.py` | Done |
| `README.md` | Done |
| `plan.md` | Done |
| `hermes-skill/SKILL.md` | Done — installed on VM |

### 8. odoo_client.py — Architecture: MCP Protocol
- Uses Odoo's `/mcp` endpoint (Streamable HTTP, NOT `/jsonrpc`)
- Authenticates via `Authorization: Bearer <MCP_KEY>` header
- Two-step init: `initialize` → get `Mcp-Session-Id` → `notifications/initialized`
- All data queries use `tools/call` with `search_read` tool
- Session ID cached in memory and reused across calls
- `muk_mcp` addon must be installed in Odoo for the `/mcp` endpoint to exist

### 9. VM File Sync — COMPLETE (May 8, 2026)
- New `odoo_client.py` (MCP protocol) copied to VM
- `.env` on VM set to `MCP_URL=http://10.0.2.2:8069` + `MCP_KEY`
- `SKILL.md` installed at `~/.hermes/skills/erp/odoo/SKILL.md`
- `test_odoo.py` passed on VM
- **Telegram → Hermes → Odoo queries confirmed working**

---

### 10. Write MCP Tools Added (May 14, 2026)
Four new write tools added to `addons/muk_mcp/data/tool.xml` and loaded into the database:

| Tool | Purpose |
|---|---|
| `update_product_price` | Update sales price and/or cost price on a product template |
| `rename_product` | Rename product, update internal reference, sales description |
| `update_customer` | Edit customer name, email, phone, address, country |
| `update_stock_quantity` | Set on-hand inventory quantity at any warehouse location |

**Key lessons:**
- `< 0` comparisons in Python code inside XML `<field>` tags must be escaped as `&lt; 0`
- After editing `tool.xml`, the module must be upgraded: `docker exec odoo-docker-web-1 odoo -u muk_mcp -d odoo --stop-after-init`
- MCP API key scope changed from `read` to `write` via direct DB update: `UPDATE muk_mcp_key SET scope = 'write' WHERE id = 1`
- Write tool responses return a plain `dict`, read tools return a `list` — `odoo_client.py` handles both

### 11. VM Files Updated (May 14, 2026)
- `odoo_client.py` — fixed response parser to handle dict (write) and list (read) returns
- `odoo_tools.py` — added 4 write functions: `update_product_price`, `rename_product`, `update_customer`, `update_stock_quantity`
- `hermes-skill/SKILL.md` — added write command examples for each new function

---

## What Is NOT Done Yet

Nothing. Read + write integration is fully working.

---

## Daily Startup (when resuming)

### Step 1 — Start Odoo containers (Windows)
```powershell
cd C:\Users\ontash\Downloads\odoo-docker\odoo-docker
docker compose up -d
```

### Step 2 — Ensure VM .env is correct
```bash
cat ~/hermes-odoo/.env
```

### Step 3 — Upgrade muk_mcp (only needed after editing tool.xml)
```powershell
docker exec odoo-docker-web-1 odoo -u muk_mcp -d odoo --stop-after-init
docker compose restart web
```
Must contain:
```env
MCP_URL=http://10.0.2.2:8069
MCP_KEY=qm6Sev4YKV6cl_kXfGfeCkXB-OAVA0ZK00LWAX1yk9A
```

---

## Credentials Summary

| Item | Value |
|---|---|
| Odoo local URL | http://localhost:8069 |
| Odoo login | `admin@gmail.com` |
| Odoo password | `admin1234` |
| MCP Key | `qm6Sev4YKV6cl_kXfGfeCkXB-OAVA0ZK00LWAX1yk9A` |
| MCP URL (from VM) | `http://10.0.2.2:8069` |

---

## Key Technical Notes

- **Never install modules while the web container is running** — causes serialization errors. Always stop web first, install, then restart.
- `muk_mcp` addon must be installed in Odoo — provides the `/mcp` Streamable HTTP endpoint
- MCP key is generated via Odoo UI: Settings → Users → Preferences → Account Security → API Keys
- `odoo_client.py` uses MCP protocol: Bearer token auth + `Mcp-Session-Id` header, NOT JSON-RPC
- `customer_rank` field only exists when `sale` module is installed — `odoo_tools.py` uses `is_company=True` instead
- From the VM, the Windows host is reachable at `10.0.2.2` (VirtualBox default gateway)

---

## Files Reference

| Path | Description |
|---|---|
| `odoo-docker/docker-compose.yml` | Docker config |
| `odoo-docker/config/odoo.conf` | Odoo config |
| `odoo-docker/hermes-odoo/.env.example` | Env template |
| `odoo-docker/hermes-odoo/odoo_client.py` | API connector |
| `odoo-docker/hermes-odoo/odoo_tools.py` | Telegram tools |
| `odoo-docker/hermes-odoo/test_odoo.py` | CLI test script |
| `odoo-docker/hermes-odoo/plan.md` | Full integration plan |
| `odoo-docker/progress.md` | This file |
