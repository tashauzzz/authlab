# AuthLab - Local Setup (Web & API)

* **Scope:** Bring the lab up locally so that **both HTML and API** branches run on a single Flask app (entrypoint: `app.py`).
* **Outcome:** Seed the DB, **run the server**, obtain an API session (**Postman is canonical**).
* **Order of operations:** 
1) Install deps
2) Create `.env`
3) Seed the DB
4) **Start the server**
5) Use Web / Postman / cURL
* **Restart policy:** if you change `.env` or reseed the DB, **stop the server, make the change, start it again**.

---

## 1) Prerequisites

* Python **3.13+**
* `pip install -r requirements.txt`
* `sqlite3` CLI (optional, for quick checks)

## 1) Prerequisites

* Python **3.13+**  
* Virtualenv for the project (recommended)

Install runtime dependencies (app only):

```bash
python -m venv venv       
source venv/bin/activate     # on Windows: venv\Scripts\activate
pip install -r requirements.txt
sqlite3 CLI (optional, for quick checks)
```
---

## 2) Environment (`.env`)

Use **[.env.example](../../.env.example)** as a template: copy it to **`.env`** in the project root and **fill the placeholders** with generated values.
`.env` is **not committed**; only `.env.example` is tracked in Git.

```bash
cp .env.example .env
```

**Lab mode:** lab is intended to run with `APP_ENV=dev` (dev-only).
**APP_ENV=prod** exists only as a guard rail for potential reuse of the codebase outside the lab.

### Generate required values

**SECRET_KEY** - Flask session signing key *(32 bytes - 64 hex chars)*:

```bash
python - <<'PY'
import secrets; print(secrets.token_hex(32))
PY
```

**ADMIN_PWHASH** - admin password hash *(scrypt)*:

```bash
python - <<'PY'
from werkzeug.security import generate_password_hash
import getpass
pwd = getpass.getpass('Admin password (hidden): ')
print(generate_password_hash(pwd, method='scrypt'))
PY
```

**ADMIN_MFA_SECRET** - base32 secret for TOTP app:

```bash
python - <<'PY'
import pyotp; print(pyotp.random_base32())
PY
```

**DEV_API_KEY** - dev-only session bootstrap *(requires `APP_ENV=dev` and `DEV_MODE=true`)*:

```bash
python - <<'PY'
import secrets, string
alphabet = string.ascii_letters + string.digits
print('dev-' + ''.join(secrets.choice(alphabet) for _ in range(24)))
PY
```

---

## 3) Database init

**DB setup:** Create DB with demo data (fresh seed; same dataset across reports).

**Additional migration (auto-applied):** the NOCASE index on product names is applied by `db_init.py`
via the `scripts/001_products_nocase_index.sql` migration.


**Scripts:** [db_init.py](../../scripts/db_init.py),
             [001_products_nocase_index.sql](../../scripts/001_products_nocase_index.sql)

**Repro (commands and quick checks):**
```bash
# Create DB with demo data and auto-apply NOCASE index
python scripts/db_init.py
# Verify that the tables exists
sqlite3 authlab.db ".tables"
sqlite3 authlab.db ".schema notes" 
# (Optional) Verify that the index exists
sqlite3 authlab.db ".indexes products"
# expect: idx_products_name_nocase
```             

---

## 4) Run the server

From the project root:

```bash
# http://127.0.0.1:5000 (Flask dev server, debug=True)
python app.py

```
**`app.py` starts a single Flask app that serves both the HTML branch and the REST API.**

--- 

## 5) Web Auth - condition: database is filled and server is running

* Web login: `http://127.0.0.1:5000/login`

---

## 6) Canonical API auth flow (Postman) - condition: database is filled and server is running

**A) Recommended - use the collection**

1. Import `docs/postman/authlab_collection.json`.
2. Run **Auth - GET /api/v1/auth/session** with header `Authorization: Bearer {{devApiKey}}` (from `.env`).
3. Postman will store the session cookie. Continue with requests from the collection.

**B) Minimal - manual request (Postman)**

1. **GET** `http://127.0.0.1:5000/api/v1/auth/session` + header `Authorization: Bearer <devApiKey>`.
   Response: **Set-Cookie** (session) + JSON with **`csrf_token`**.
    cURL exists as a fallback - see the link in **Cross-References**
2. Use the stored cookie for subsequent requests.
   The full contract and parameters are defined in **OpenAPI** (see **Cross-References**).

---

## 7) Quick verification checklist

* **Env loaded:** no startup errors about `SECRET_KEY` or `ADMIN_PWHASH`.
* **DB seeded:** `authlab.db` exists; the NOCASE index is present.
* **API session:** `/api/v1/auth/session` returns a cookie and a `csrf_token`.
* **Logs written:** `logs/authlab.log` contains events.

---

## 8) Cross-References

* OpenAPI contract - [openapi.yaml](../api/openapi/openapi.yaml)
* cURL Quickstart - [README.md](../api/curl/README.md)
* Postman collection - [authlab_collection.json](../api/postman_collection/authlab_collection.json)

* AuthLab Web - README (HTML branch)
  [README.md](../web/README.md)
* AuthLab API - README (API branch)
  [README.md](../api/README.md)
* AuthLab Security Assessment - README (Web + API)
  [README.md](../security_assessment/OVERVIEW.md)
