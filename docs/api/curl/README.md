# AuthLab API - cURL Quickstart README

**Goal:** run the API locally and exercise the core endpoints with `curl`, using cookies and CSRF correctly.\
**Scope covered:** `/api/v1/auth/session`, `/api/v1/guestbook/messages`, `/api/v1/products`, `/api/v1/notes`, `/api/v1/notes/{id}`.

## Prerequisites

* [SETUP.md](../../setup/SETUP.md) (DB seeded, app in DEV mode).
* `.env` contains a valid `DEV_API_KEY`.
* `curl` and `jq` CLI tools are available in shell.

## 0) One-time shell setup

```bash
export BASE="http://127.0.0.1:5000"     # API base URL
export DEV_API_KEY="YOUR_DEV_KEY"        # copy from .env
export COOKIE_JAR="./cookies.txt"        # where curl will store cookies
rm -f "$COOKIE_JAR"                      # clean start
```

---

## 1) Bootstrap session **and capture CSRF in one command**

```bash
export CSRF="$(
  curl -s -c "$COOKIE_JAR" \
       -H "Authorization: Bearer $DEV_API_KEY" \
       "$BASE/api/v1/auth/session" | jq -r .csrf_token
)"
echo "CSRF=$CSRF"
```

Now we have:

* a **session cookie** saved in `cookies.txt`
* a **CSRF token** in `$CSRF`

---

## 2) Read endpoints (cookie-only)

**Guestbook list**

```bash
curl -i -b "$COOKIE_JAR" \
  "$BASE/api/v1/guestbook/messages?limit=5&offset=0"
```

**Products list (filters, sort, Link header)**

```bash
curl -i -b "$COOKIE_JAR" \
  "$BASE/api/v1/products?limit=4&offset=0&sort_by=name&sort_dir=asc&q=lap"
# Tip: look at the `Link:` header for RFC 5988 pagination (prev/next)
```

**Notes list (owner-only)**

```bash
curl -i -b "$COOKIE_JAR" \
  "$BASE/api/v1/notes?limit=20&offset=0&sort_by=title&sort_dir=asc"
```

**Notes detail (owner-only)**

```bash
curl -i -b "$COOKIE_JAR" \
  "$BASE/api/v1/notes/1"
```

---

## 3) Write endpoint (needs cookie **and** CSRF)

**Guestbook create**

```bash
curl -i -b "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{"message":"hello from curl"}' \
  "$BASE/api/v1/guestbook/messages"
# On success: HTTP/1.1 201 Created + Location header
```

---

## 4) Reset session quickly

```bash
rm -f "$COOKIE_JAR"
unset CSRF
```

## Notes

* **Security model (DEV):** we bootstrap with `Authorization: Bearer <DEV_API_KEY>`, the server sets a cookie and returns a CSRF token. After that, **GETs** work with cookie; **POSTs** require cookie **and** `X-CSRF-Token: <token>`.
