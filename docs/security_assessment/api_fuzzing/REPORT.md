# API Fuzzing - Schemathesis vs OpenAPI (AuthLab)

* **Status:** Adopted  
* **Tool:** Schemathesis v4.6.4    
* **Environment:** Local lab (Flask DEV server, OpenAPI 3.0.3, DEV bootstrap via `DEV_API_KEY`)  
* **Artifact:** Full CLI output - [run.txt](run.txt)

---

## 1) Summary

This report captures **schema-based fuzzing** of the AuthLab REST API using **Schemathesis** and the current OpenAPI definition for AuthLab - [openapi.yaml](../../api/openapi/openapi.yaml)

In this Schemathesis run (see `run.txt`), the tool:

* generated **237** test cases
* exercised **11** failing requests, yielding **12 unique failures**
* **skipped 66** cases as out-of-scope / not applicable


**Objectives:**

1. Confirm that malformed inputs do **not** cause `5xx` / tracebacks.
2. See where **runtime behavior** diverges from the OpenAPI contract.
3. Stress-test auth / CSRF / rate-limit logic.

## 2) Scope & Preconditions

* **Lab:** running locally as per [SETUP.md](../../setup/SETUP.md) (DB seeded, app in DEV mode). 
* **API under test:**
    * `GET /api/v1/auth/session`
    * `GET /api/v1/guestbook/messages`
    * `POST /api/v1/guestbook/messages`
    * `GET /api/v1/products`
    * `GET /api/v1/notes`
    * `GET /api/v1/notes/{id}`

---

## 3) Tool & Command

**Schemathesis was executed from the repo root:**

```bash
 schemathesis run docs/api/openapi/openapi.yaml \
  --url=http://127.0.0.1:5000 \
  -H "Authorization: Bearer <DEV_API_KEY>" \
  --max-examples=20
```
---

## 4) Key Findings (from `run.txt`)

### 4.1 No unhandled errors

Across all phases (**Examples / Coverage / Fuzzing / Stateful**):

* All responses were in **`2xx / 4xx / 429`**.
* **No `5xx`** responses, stack traces or server crashes were observed.

This confirms that malformed input is handled by normal error paths rather than blowing up the app.

---

### 4.2 “API accepts invalid authentication”

**Schemathesis reports several cases like:**

Expected 401, got 200 (generated auth likely invalid)

**Context:**

* AuthLab uses a **DEV bootstrap** model:

  * `GET /api/v1/auth/session` with `Authorization: Bearer dev-123` creates a cookie-based session.
  * After that, the **cookie** is the primary auth mechanism.
* In Stateful tests, Schemathesis first obtains a valid session, then mutates headers while the cookie remains valid.

The header looks “invalid”, but the request is still authorized via the existing session cookie - which is intentional in this lab.

---

### 4.3 “API accepted schema-violating request”

**AuthLab behavior:**

* Extra query parameters are **ignored**, not rejected.
* `GET /api/v1/auth/session` allows bootstrap with a valid DEV bearer even without a cookie.  
 This is intentional in the lab: the cookie is issued by this endpoint, so requiring an existing cookie for bootstrap would not make sense.

---

### 4.4 CSRF & POST `/api/v1/guestbook/messages`

**Schemathesis flags:**

* Missing `X-CSRF-Token` - `400 csrf_bad` instead of an expected `406`.
* Some “schema-compliant” cases that still hit `400 csrf_bad` due to invalid token or session state.

**Observations:**

* All CSRF failures are **cleanly mapped** to:

  ```json
  {
    "error": {
      "code": "csrf_bad",
      "message": "Invalid CSRF token"
    }
  }
  ```

* No crashes or inconsistent formats.

---

### 4.5 Notes endpoints & rate limiting

For `GET /api/v1/notes` and `GET /api/v1/notes/{id}` Schemathesis reports:

* Additional “invalid auth” findings (same root cause: valid cookie session).
* **Stateful** tests that hit `429 ratelimited` and are treated as failures.

**Observations:**

* Rate limiting is **actively triggered** under fuzzing load:

  ```json
  {
    "error": {
      "code": "ratelimited",
      "message": "Too many requests"
    }
  }
  ```

* Owner checks and masked 404 behavior are preserved even for unusual inputs; no leakage of foreign notes.

This is exactly the behavior we want to demonstrate for brute-force / abuse scenarios.

---

## 5) Results

**From this run:**

* The API is **resilient to malformed inputs**: no `5xx`, no tracebacks.
* Error handling is **consistent** via the JSON envelope (`error.code`, `error.message`).
* DEV bootstrap and cookie-based sessions behave as designed, even if fuzzing tools treat some flows as “invalid auth”.
* Rate limiting provides a real brake under aggressive automated traffic.