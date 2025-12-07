# AuthLab Web - README (HTML branch)

Quick map of the **HTML branch** of AuthLab.

Before manually reproducing any WEB scenarios, make sure the lab is up and running
according to [SETUP.md](../setup/SETUP.md)

* DB seeded with demo data
* dependencies installed
* Flask app running in **DEV** mode

---

## 1) Code layout (HTML branch)

* Shared helpers & config: [core.py](../../authlab/core.py)
* Web blueprint wiring: [init.py](../../authlab/__init__.py) (`web_bp`)
* HTML modules:
  * [auth_html.py](../../authlab/web/auth_html.py) - `/login`, `/mfa`, `/dashboard`, `/logout`, `/`
  * [xss_reflected_html.py](../../authlab/web/xss_reflected_html.py)  - `/search`
  * [xss_stored_html.py](../../authlab/web/xss_stored_html.py) - `/guestbook` (GET/POST)
  * [sqli_html.py](../../authlab/web/sqli_html.py) - `/products`
  * [idor_html.py](../../authlab/web/idor_html.py) - `/notes`, `/note/<id>`

## 2) Where to read about security (HTML branch) 

1. **Authentication & protections (current secure model)**

* Web Auth - Sessions, CSRF, Rate-Limit, MFA (HTML)
  [REPORT.md](auth/REPORT.md)  
  This document describes the *overall secure flow*:
  cookie-based session, CSRF on all state-changing POSTs, rate-limits on critical steps,
  optional MFA, and behavior of logout / guestbook in the auth context.

2. **Concrete web vulnerabilities reports (before / after fix)**  

* Reflected XSS - `/search` (PoC → Fix → Verify)
  [REPORT.md](reports/xss_reflected/REPORT.md)
* Stored XSS - `/guestbook` (PoC → Fix → Verify)
  [REPORT.md](reports/xss_stored/REPORT.md)  
* SQL Injection - `/products` (PoC → Fix → Verify)
  [REPORT.md](reports/sqli/REPORT.md)
* IDOR - `/note/<note_id>` (+ `/notes`) - (PoC → Fix → Verify)
  [REPORT.md](reports/idor/REPORT.md)

---

## 3) Cross-References

* AuthLab API - README (API branch)
  [README.md](../api/README.md)
* AuthLab Security Assessment - README (Web + API)
  [README.md](../security_assessment/README.md)


