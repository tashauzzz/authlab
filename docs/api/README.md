# AuthLab API - README (API branch)

Map of the **API branch** of AuthLab.\
Before manually reproducing any API scenarios, make sure the lab is up and running
according to [SETUP.md](../setup/SETUP.md)

* DB seeded with demo data
* dependencies installed
* Flask app running in **DEV** mode

---

## 1) Key concepts

* **DEV bootstrap:** This is DEV-only bootstrap; in production we’d use OAuth2/OIDC/JWT (out of scope). First request uses `Authorization: Bearer <DEV_API_KEY>` to **create a cookie session** and return a **CSRF token**. After that:

  * **GET endpoints** - typically use the session cookie (tools like Postman may still send the DEV bearer in parallel)
  * **POST** endpoint - session **cookie + `X-CSRF-Token`**

* **Error envelope:** All API errors use one JSON envelope:

```json
  {
    "error": {
      "code": "<short_code>",
      "message": "<readable_message>",
      "details": { /* optional */ }
    }
  }
```
* **Owner-only data:** `/api/v1/notes` and `/api/v1/notes/{id}` are scoped to the current user.
  Foreign/missing IDs return a **masked 404**.
* **Rate-limit (fixed window):**
  Applied where it matters for the demo:

  * **Yes:** `POST /guestbook/messages`, `GET /products`, `GET /notes`, `GET /notes/{id}`
  * **No:** `GET /auth/session`, `GET /guestbook/messages`
    When limited we’ll see `429` and a `Retry-After` header.
* **Pagination:** Lists use `limit/offset`. Some endpoints also emit **RFC 5988** `Link:` headers (`rel="prev"`, `rel="next"`).

---

## 2) Conventions

* **Auth:** `Authorization: Bearer <DEV_API_KEY>` (used to bootstrap in DEV); after that, clients normally rely on the session cookie.
* **Cookies:** Standard Flask session cookie (`Set-Cookie: session=…; HttpOnly; Path=/`).
* **CSRF:** For JSON writes, send `X-CSRF-Token: <token>` from `/auth/session`.
* **Content types:** JSON requests must use `Content-Type: application/json`; otherwise `415 (bad_json)`.
* **Status codes:** Success `200/201`; common errors: `400 invalid_*`, `401 unauthorized`, `404 not_found (masked)`, `415 bad_json`, `429 ratelimited`.
* **Pagination:** `limit` (1-100), `offset` (0-10000). When applicable, the **Link** header exposes navigational URLs.

---

## 3) Endpoint notes

### `GET /api/v1/auth/session`

* **Purpose:** DEV bootstrap; returns `{ user, csrf_token }`.
* **When successful:** Sets the cookie; subsequent calls may reuse the cookie (no bearer needed).
* **Errors:** `401 unauthorized` (missing/invalid DEV key and no valid cookie).

### `GET /api/v1/guestbook/messages`

* **Purpose:** Read guestbook messages (newest first).
* **Params:** `limit`, `offset`.
* **Auth:** DEV session cookie
  (or `Authorization: Bearer <DEV_API_KEY>` in DEV mode)(for each endpoint).
* **Errors:** `401 unauthorized`.

### `POST /api/v1/guestbook/messages`

* **Purpose:** Create a new message.
* **Body:** `{ "message": "…" }` (server truncates over `MAX_MSG_LEN`).
* **Headers:** `X-CSRF-Token` required.
* **Returns:** `201 Created` with `Location` + JSON of created item.
* **Errors:** `400 empty/csrf_bad`, `401 unauthorized`, `415 bad_json`, `429 ratelimited`.

### `GET /api/v1/products`

* **Purpose:** Filtered/sorted product list.
* **Params:** `q` (case-insensitive substring), `min_price`, `max_price`, `limit`, `offset`, `sort_by` (`id|name|price`), `sort_dir` (`asc|desc`).
* **Headers (response):** may include `Link:` with `prev/next`.
* **Errors:** `400 invalid_param|invalid_range|invalid_sort_by|invalid_sort_dir`,
  `401 unauthorized`, `429 ratelimited`.

### `GET /api/v1/notes`

* **Purpose:** **Owner-only** list of notes.
* **Params:** `limit`, `offset`, `sort_by` (`id|title`), `sort_dir`.
* **Headers (response):** may include `Link:` with `prev/next`.
* **Errors:** `400 invalid_sort_by|invalid_sort_dir`,
  `401 unauthorized`, `429 ratelimited`.

### `GET /api/v1/notes/{id}`

* **Purpose:** **Owner-only** detail.
* **Errors:** `404 not_found` (masked for foreign/missing), `401 unauthorized`, `429 ratelimited`.

---

## 4) Code layout (API branch)

* Shared helpers & config: [core.py](../../authlab/core.py)
* API blueprint wiring: [init.py](../../authlab/__init__.py) (`api_bp`)
* Endpoint modules:
  * [auth_api.py](../../authlab/api/auth_api.py) - `/api/v1/auth/session`
  * [guestbook_api.py](../../authlab/api/guestbook_api.py) - `/api/v1/guestbook/`
  * [products_api.py](../../authlab/api/products_api.py) - `/api/v1/products`
  * [notes_api.py](../../authlab/api/notes_api.py) - `/api/v1/notes`, `/api/v1/notes/{id}`

---

## 5) Where to read about security (API branch) 

1. **Contract & tools**

* OpenAPI contract [openapi.yaml](openapi/openapi.yaml)
* cURL Quickstart [README.md](curl/README.md)
* Postman collection [authlab_collection.json](postman_collection/authlab_collection.json)

2. **Security API reports**

* Case-Insensitive Product Search + Name Index (SQLite) & Link Pagination (RFC 5988)
  [REPORT.md](reports/products_nocase_links/REPORT.md)
* API SQLi Negative
  [REPORT.md](reports/api-sqli-negative/REPORT.md)
* Notes API - Owner-Only List & Detail with JSON-404 Masking
  [REPORT.md](reports/notes-owner-check/REPORT.md)

---

## 6) Cross-References

* AuthLab Web - README (HTML branch)
  [README.md](../web/README.md)
* AuthLab Security Assessment - README (Web + API)
  [README.md](../security_assessment/README.md)
