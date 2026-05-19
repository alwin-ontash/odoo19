# Hermes ↔ Odoo 19 Connector

Connect your Telegram-based Hermes Agent to Odoo 19 running in Docker.
Fetch sales orders, invoices, customers, products, and stock — directly from Telegram.

---

## Prerequisites

- Odoo 19 running in Docker on your host machine (port `8069`)
- Hermes Agent running inside your VM
- A cloud tunnel to expose Odoo publicly (ngrok or Cloudflare Tunnel)
- Python 3.10+ installed in your VM
- A Telegram bot connected to Hermes

---

## Quick Start

### 1. Copy this folder to your Hermes VM

```bash
scp -r hermes-odoo/ user@your-vm-ip:~/hermes-odoo/
```

Or clone/copy however you normally transfer files to the VM.

---

### 2. Install Python dependencies

```bash
cd hermes-odoo
pip install -r requirements.txt
```

---

### 3. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
ODOO_URL=https://your-cloud-tunnel-url
ODOO_DB=odoo
ODOO_API_KEY=your_odoo_api_key
AUTHORIZED_TELEGRAM_USER_ID=your_telegram_user_id
```

> **Never commit `.env` to version control.**

---

### 4. Create a dedicated Odoo API user

Do **not** use the admin account for API access.

1. Log into Odoo at `http://localhost:8069`
2. Go to **Settings → Users & Companies → Users**
3. Click **New** and create a user (e.g. `api@yourcompany.com`)
4. Set the role to **Internal User** and restrict access to read-only where possible
5. Go to **Settings → Technical → API Keys**
6. Click **New**, select your API user, and generate a key
7. Copy the key into `.env` as `ODOO_API_KEY`

---

### 5. Set up a cloud tunnel

#### Option A — ngrok (quick testing)

```bash
ngrok http 8069
```

Copy the HTTPS URL (e.g. `https://abc123.ngrok-free.app`) into `ODOO_URL` in `.env`.

> Free ngrok URLs reset on every restart. Use Cloudflare for a permanent URL.

#### Option B — Cloudflare Tunnel (recommended for stable use)

```bash
# Install cloudflared on your host machine, then:
cloudflared tunnel login
cloudflared tunnel create odoo-tunnel
cloudflared tunnel route dns odoo-tunnel odoo.yourdomain.com
```

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: <your-tunnel-id>
credentials-file: /path/to/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: odoo.yourdomain.com
    service: http://localhost:8069
  - service: http_status:404
```

Start the tunnel:

```bash
cloudflared tunnel run odoo-tunnel
```

Set `ODOO_URL=https://odoo.yourdomain.com` in `.env`.

---

### 6. Verify connectivity from your VM

```bash
curl -I https://your-cloud-tunnel-url/web/login
```

You should see `HTTP/2 200`. If not, check your tunnel and Odoo Docker container.

---

### 7. Test the connector

```bash
python test_odoo.py
```

Expected output (example):

```
=======================================================
  1. Last 5 Sales Orders
=======================================================
*Last 3 Sales Orders:*

• *S00001* | Azure Interior | $1,250.00 | 2026-05-01

=======================================================
  2. Unpaid Invoices
=======================================================
No unpaid invoices found.
...
```

You can also test with specific names:

```bash
python test_odoo.py --customer "ABC Traders" --product "Laptop"
```

---

### 8. Integrate with Hermes

Register each function from `odoo_tools.py` as a Hermes custom tool or skill.

| Telegram message | Hermes calls |
|---|---|
| Show last 5 Odoo sales orders | `show_last_sales_orders(limit=5)` |
| Show unpaid invoices from Odoo | `show_unpaid_invoices(limit=5)` |
| Find customer ABC Traders | `search_customer("ABC Traders")` |
| Show stock for Laptop | `show_product_stock("Laptop")` |
| Search product Keyboard | `search_product("Keyboard")` |

Always verify `AUTHORIZED_TELEGRAM_USER_ID` before calling any tool.

---

## File Structure

```
hermes-odoo/
├── .env                ← Your secrets (never commit)
├── .env.example        ← Template — safe to commit
├── .gitignore          ← Excludes .env
├── requirements.txt    ← Python dependencies
├── odoo_client.py      ← JSON-RPC 2.0 API connector
├── odoo_tools.py       ← Telegram-friendly tool functions
├── test_odoo.py        ← CLI test script
└── README.md           ← This file
```

---

## Security Notes

- Use a **dedicated read-only API user** — never the admin account
- Store all secrets in `.env` only
- Restrict Telegram access to your `AUTHORIZED_TELEGRAM_USER_ID`
- Always use HTTPS tunnel URLs
- Never forward raw Odoo errors to Telegram messages
- Enable **Cloudflare Access** on your tunnel for extra protection

---

## Supported Odoo Models

| Model | Used for |
|---|---|
| `sale.order` | Sales orders |
| `account.move` | Customer invoices |
| `res.partner` | Customers / vendors |
| `product.product` | Products |
| `stock.quant` | Stock quantities |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not reach Odoo` | Check tunnel is running and `ODOO_URL` is correct |
| `Odoo rejected the API key` | Regenerate key in Odoo → Settings → API Keys |
| `Missing environment variables` | Check `.env` exists and all values are filled in |
| `No sales orders found` | Confirm the API user has access to `sale.order` in Odoo |
| HTTP 401 from Odoo | API key is wrong or the user is inactive |
| HTTP 404 from tunnel | Tunnel is not pointing to port 8069 |
