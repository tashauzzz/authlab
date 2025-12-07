# AuthLab - Project README

AuthLab is a Flask + SQLite application built from scratch as a training lab.

The project collects a mini secure SDLC for both the web UI and the REST API:  
* **on the HTML side:** deliberately vulnerable web examples (XSS, SQLi, IDOR) with PoC → Fix → Verify reports, plus a “current secure model” for the login / MFA / guestbook flow (sessions, CSRF, rate-limits, MFA);  
* **on the API side:** reports that focus on safer patterns and checks, including parameterized search with SQLi-negative verification, owner-only notes with masked 404, pagination, logging, and a consistent JSON error envelope;  
* **on top of that:** a separate security assessment layer with contract-based fuzzing (Schemathesis vs OpenAPI) and a micro-STRIDE threat model for Web + API.

All reports are tied to a single codebase: every PoC and fix maps to specific handlers and queries in the `authlab.web` and `authlab.api` modules.

---

## How to navigate this repo

### For documentation, start from one of these overview docs:

* AuthLab Web - README (HTML branch)
    [README.md](docs/web/README.md)  
    *Short entry point into the HTML branch*

* AuthLab API - README (API branch)
    [README.md](docs/api/README.md)  
    *Entry point into the REST API under `/api/v1/`*

* AuthLab Security Assessment - README (Web + API)
    [README.md](docs/security_assessment/README.md)   
    *Entry point into contract-based fuzzing and the micro-STRIDE threat model.*

### Code & support files:

- Main Flask package for both Web & API (HTML handlers, API handlers, shared helpers) - [authlab/](authlab)
- Single place with all steps to run the lab locally - [SETUP.md](docs/setup/SETUP.md)