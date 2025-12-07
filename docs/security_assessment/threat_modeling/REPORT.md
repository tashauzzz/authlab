# AuthLab - Threat Model (Web + API)

* **Status:** Adopted  
* **Method:** Micro-STRIDE review (Web + API)  
* **Scope:** HTML auth & guestbook, REST API (`/api/v1/*`) 
* **Environment:** Local lab (Flask DEV server, OpenAPI 3.0.3, DEV bootstrap via `DEV_API_KEY`)

---

## 1) Summary

This document captures a **high-level threat model** for AuthLab as a combined system:

- HTML branch: login / MFA / logout, guestbook & demo SQLi / XSS surfaces  
- API branch: `/api/v1/auth/session`, `/api/v1/guestbook/messages`, `/api/v1/products`, `/api/v1/notes*`  
- Cross-cutting controls: sessions, CSRF, rate-limits, JSON error envelope, structured logs

Goal: show **which threats are mitigated inside the lab** and which risks are **deliberately left out of scope** for a DEV-only training project.

--- 
 
## 2) Threat matrix (micro-STRIDE)

| Asset | Threat (STRIDE) | Mitigation (in AuthLab) | Residual risk / Out of scope | References |
|-------|-----------------|-------------------------|------------------------------|------------|
| HTML login / MFA / logout | **Spoofing / Brute-force** against `/login` & `/mfa` | Password hash in env, fixed-window rate-limit, optional TOTP MFA, JSON logs for attempts | No adaptive controls, no IP reputation, no account lockout workflow or user notifications; designed as a minimal demo, not a full IAM system | Web Auth - Sessions, CSRF, Rate-Limit, MFA (HTML) - [REPORT.md](../../web/auth/REPORT.md) |
| HTML login / guestbook form | **CSRF** on state-changing actions | Hidden `csrf_token` on login, MFA, guestbook, logout; server compares against session; CSRF failures mapped to consistent HTML/JSON responses | No SameSite tuning, no CSRF tokens bound to device / UA; no global CSRF middleware |Guestbook handler in the Web Auth report|
| Guestbook messages (HTML) | **XSS / content injection** via user-controlled message body | Templates escape output by default; SQLi & XSS PoC are documented and then fixed; logs capture payloads for analysis | No CSP, no HTML sanitizer library, no content security headers; in a real product, additional browser-side hardening would be expected | XSS & SQLi HTML reports in [docs/web/](../../web/reports)  |
| API session (`/api/v1/auth/session`) & `DEV_API_KEY` | **Spoofing / misuse** of static dev key | DEV-only key in `.env` (`DEV_MODE=true`, `APP_ENV=dev`), described as lab-only bootstrap; once session is created, cookie becomes the main auth mechanism | Static long-lived key would be unacceptable in production; no rotation, no scoping, no audit of key usage; real systems should use OAuth2/OIDC/JWT and proper secrets management | AuthLab API - Overview (API branch) [OVERVIEW.md](../../api/OVERVIEW.md), OpenAPI contract - [openapi.yaml](../../api/openapi/openapi.yaml)  |
| Session cookie (`session`) | **Session theft / fixation** (Web + API) | Server-side Flask session, HttpOnly cookie, no credentials stored in the cookie itself | No explicit `Secure` / `SameSite` settings for HTTPS, no session rotation on privilege changes, no idle timeout demonstration; these are intentionally out of scope for the lab | Web Auth report, Flask config in [`authlab/__init__.py`](../../../authlab/__init__.py) |
| Products API (`/api/v1/products`) | **Tampering / DoS / Injection** via query params | Parameterized SQL queries, `COLLATE NOCASE` index, strict validation for `limit`, `offset`, `sort_by`, `sort_dir`; rate-limit on the endpoint; consistent JSON error envelope | Lab focuses on query safety & basic throttling, not full-scale performance hardening | Case-Insensitive Product Search + Name Index (SQLite) & Link Pagination (RFC 5988) - [REPORT.md](../../api/reports/products_nocase_links/REPORT.md) |
| Notes API (`/api/v1/notes*`) | **IDOR / data leakage / enumeration** | Owner check at DB query level; non-existing and foreign IDs both return the same JSON 404; list endpoint is owner-scoped; rate-limit under load | No fine-grained roles / sharing model; no anomaly detection for unusual access patterns; lab intentionally focuses on the basic “no foreign notes, masked 404” pattern |  Notes API - Owner-Only List & Detail with JSON-404 Masking - [REPORT.md](../../api/reports/notes_owner_check/REPORT.md) |
| Structured logs (`authlab.log`) | **Information disclosure / log tampering** | Logs use concise JSON entries (no passwords or CSRF token values), focus on high-level actions & reasons | No log signing or integrity checks, no central log storage, no rotation / retention policy; brute-force detection would live in a separate project | Logging helpers in [authlab/core.py](../../../authlab/core.py); planned follow-up: separate `brute_detection_from_logs` project |
| Transport & deployment (HTTP dev server) | **Information disclosure / MiTM / DoS** on network level | Lab is expected to run locally over HTTP on `127.0.0.1` only; no public exposure; simple single-process Flask setup for learning | No TLS, no reverse proxy/WAF, no network segmentation or HA; in production this API would sit behind HTTPS termination, WAF, and hardened infrastructure; out of scope for this lab | AuthLab - Local Setup (Web & API) - [SETUP.md](../../setup/SETUP.md) |
| Rate-limit & CSRF under fuzzing | **Abuse / automation** (brute-force, fuzzing) | Fixed-window rate-limits on sensitive endpoints; CSRF validation for JSON writes; Schemathesis fuzzing shows only `2xx/4xx/429`, no `5xx` / crashes; errors always wrapped in JSON envelope | Limits are simple and global; no per-user/IP tuning, no dedicated blocking lists; real environments would combine these controls with alerting and SOC monitoring | API Fuzzing - Schemathesis vs OpenAPI (AuthLab) - [REPORT.md](../api_fuzzing/REPORT.md) |