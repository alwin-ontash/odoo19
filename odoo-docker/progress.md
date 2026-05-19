# Project Progress — Hermes ↔ Odoo 19 Integration

**Last updated:** May 6, 2026  
**Status:** In progress — API connector working, VM file sync pending

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

### 4. Odoo API Key Generated
- API key generated via Odoo shell in correct user context
- **API Key:** `710933fdf0f75ff013581b6684404073a6353531`
- Belongs to user: `admin@gmail.com` (uid = 2)
- Verified working — `authenticate` returns uid `2`

### 5. ngrok Tunnel Created
- ngrok installed via winget
- Auth token configured: `3DLdWSOpujZDDQu7DzapEU2wXkS_6Fq5N3cfo2YP94Q9uNbeZ`
- **Current tunnel URL:** `https://poem-coagulant-trilogy.ngrok-free.dev`
- ⚠️ **This URL changes every time ngrok restarts** (free plan)
- To restart tunnel: open new PowerShell and run `ngrok http 8069`
- Tunnel terminal must stay open while in use

### 6. API Verified Working from Windows Host
Confirmed with curl — returns real Odoo data:
```json
{"result": [{"id": 1, "name": "My Company", "email": "admin@gmail.com"}]}
```

### 7. hermes-odoo/ Project Files Created
All files created at: `C:\Users\ontash\Downloads\odoo-docker\odoo-docker\hermes-odoo\`

| File | Status |
|---|---|
| `.env.example` | Done |
| `.gitignore` | Done |
| `requirements.txt` | Done |
| `odoo_client.py` | Done (v3 — uses `/jsonrpc` + `requests.Session()`) |
| `odoo_tools.py` | Done |
| `test_odoo.py` | Done |
| `README.md` | Done |
| `plan.md` | Done |

### 8. odoo_client.py — Key Architecture Decision
- Uses `/jsonrpc` endpoint (NOT `/web/dataset/call_kw`)
- Authenticates via `common.authenticate` with login + API key
- Uses `requests.Session()` to persist the session cookie
- Calls `object.execute_kw` with uid + API key for every model call
- This is the correct approach for Odoo 19 JSON-RPC 2.0

---

## What Is NOT Done Yet

### VM File Sync — CRITICAL BLOCKER
The VM still has the **old version** of `odoo_client.py` which uses Bearer token and `/web/dataset/call_kw`. This causes "Session expired" on every call.

**The new `odoo_client.py` must be copied to the VM.**

---

## What To Do Tomorrow

### Step 1 — Start ngrok tunnel on Windows host
```powershell
ngrok http 8069
```
Copy the new HTTPS URL and update `.env` on the VM if it changed.

### Step 2 — Start Odoo containers
```powershell
cd C:\Users\ontash\Downloads\odoo-docker\odoo-docker
docker compose up -d
```

### Step 3 — Copy new odoo_client.py to VM

**Option A — SCP (recommended):**
```powershell
scp "C:\Users\ontash\Downloads\odoo-docker\odoo-docker\hermes-odoo\odoo_client.py" ubuntu@YOUR_VM_IP:~/hermes-odoo/odoo_client.py
```

**Option B — Manual paste on VM:**
```bash
nano ~/hermes-odoo/odoo_client.py
# Select all (Ctrl+K to delete lines), paste new content, Ctrl+O, Enter, Ctrl+X
```

The new file content is in: `C:\Users\ontash\Downloads\odoo-docker\odoo-docker\hermes-odoo\odoo_client.py`

### Step 4 — Ensure .env on VM is correct
```bash
cat ~/hermes-odoo/.env
```
Must contain all 5 lines:
```env
ODOO_URL=https://poem-coagulant-trilogy.ngrok-free.dev
ODOO_DB=odoo
ODOO_LOGIN=admin@gmail.com
ODOO_API_KEY=710933fdf0f75ff013581b6684404073a6353531
AUTHORIZED_TELEGRAM_USER_ID=your_telegram_user_id
```
> If ngrok URL changed, update ODOO_URL with the new one.

### Step 5 — Run test on VM
```bash
cd ~/hermes-odoo
python3 test_odoo.py
```

Expected output when working:
- Sales orders: empty list (no demo data) — shows "No confirmed sales orders found."
- Invoices: empty — shows "No unpaid invoices found."
- Customer search: returns "My Company"
- Product search: returns matching products
- Stock: returns stock data

### Step 6 — After test passes, integrate with Hermes
- Register functions from `odoo_tools.py` as Hermes tools/skills
- Map Telegram intents to functions (see plan.md Section 11)
- Add `AUTHORIZED_TELEGRAM_USER_ID` check before any tool execution

---

## Credentials Summary

| Item | Value |
|---|---|
| Odoo local URL | http://localhost:8069 |
| Odoo ngrok URL | https://poem-coagulant-trilogy.ngrok-free.dev ⚠️ changes on restart |
| Odoo DB | `odoo` |
| Odoo login | `admin@gmail.com` |
| Odoo password | `admin1234` |
| Odoo API key | `710933fdf0f75ff013581b6684404073a6353531` |
| Odoo user ID | `2` |
| ngrok auth token | `3DLdWSOpujZDDQu7DzapEU2wXkS_6Fq5N3cfo2YP94Q9uNbeZ` |

---

## Key Technical Notes

- **Never install modules while the web container is running** — causes serialization errors. Always stop web first, install, then restart.
- The API key was generated using Odoo shell with `env(user=user.id)['res.users.apikeys']._generate(None, 'hermes-agent', None)`
- `customer_rank` field only exists when `sale` module is installed — `odoo_tools.py` now uses `is_company=True` instead
- `requests.Session()` is essential — without it, each call gets a fresh session and "Session expired" errors occur
- The `/jsonrpc` endpoint requires: db, uid (int), password/apikey, model, method, args, kwargs — in that exact order

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
