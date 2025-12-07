# AuthLab Security Assessment - README

Short map of the **security assessment layer** in AuthLab.

---

## 1) What this layer is for

**This layer collects security assessment artifacts around the main Web and API lab.**

Main goals:

* Run **schema-based fuzzing** of the REST API (`/api/v1/*`) against the OpenAPI document.
* Capture a **micro-STRIDE** threat model for Web + API in a table.
* Make it explicit which risks **are already mitigated in AuthLab**, and which **belong to a real production environment** and are out of scope for the lab.


---

## 2) Documents in this folder

1.  **API Fuzzing - Schemathesis vs OpenAPI (AuthLab)**
    [REPORT.md](api_fuzzing/REPORT.md)  
    One Schemathesis run against all AuthLab API operations from `openapi.yaml`.  
    Checks that malformed input does **not** cause `5xx` / tracebacks and shows a few places where runtime behaviour is different from the strict OpenAPI contract.

2.  **AuthLab - Threat Model (Web + API)** 
    [REPORT.md](threat_modeling/REPORT.md)  
    A micro-STRIDE table that covers HTML auth & guestbook plus the main REST API endpoints.  
    Summarises which threats are handled inside the lab and which things are intentionally left out for production.

---

## 3) Cross-References

* AuthLab Web - README (HTML branch)
  [README.md](../web/README.md)

* AuthLab API - README (API branch)
  [README.md](../api/README.md)
