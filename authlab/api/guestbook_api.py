# authlab/api/guestbook_api.py

from flask import request

import authlab.core as core
from . import api_bp


@api_bp.get("/guestbook/messages")
def api_guestbook_list():
    """
    Return guestbook messages as JSON (newest first) with basic pagination.
    """
    user, resp = core.require_auth_json()
    if resp:
        return resp

    limit = core.parse_int(request.args.get("limit"), default=20, min_v=1, max_v=100)
    offset = core.parse_int(request.args.get("offset"), default=0, min_v=0, max_v=10_000)

    total = len(core.GUESTBOOK)
    msgs = list(reversed(core.GUESTBOOK))  # newest first, как в HTML
    items = msgs[offset: offset + limit]

    payload = {
        "items": items,
        "count": len(items),
        "total": total,
        "offset": offset,
        "limit": limit,
    }
    core.log_attempt(
        user, True, "api_guestbook", "list",
        route=request.path, meta={"count": len(items), "total": total},
    )
    return core.json_ok(payload)


@api_bp.post("/guestbook/messages")
def api_guestbook_create():
    """
    Create a guestbook entry via JSON body, protected with:
    - cookie auth (require_auth_json),
    - X-CSRF-Token header,
    - per-user rate-limit.
    """
    user, resp = core.require_auth_json()
    if resp:
        return resp

    if not core.require_csrf_header():
        core.log_attempt(user, True, "api_guestbook", "csrf_bad", route=request.path)
        return core.api_error("csrf_bad")

    rate_key = f"api_gb:{core.client_ip()}|{user.lower()}"
    allowed, retry_after = core.rl_check_and_hit(
        rate_key, core.WINDOW_SEC, core.MAX_ATTEMPTS
    )
    if not allowed:
        core.log_attempt(
            user,
            True,
            "api_guestbook",
            "ratelimited",
            route=request.path,
            meta={"retry_after": retry_after},
        )
        err = core.api_error("ratelimited")
        err.headers["Retry-After"] = str(retry_after)
        return err

    if not request.is_json:
        core.log_attempt(user, True, "api_guestbook", "bad_json", route=request.path)
        return core.api_error("bad_json")

    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        core.log_attempt(user, True, "api_guestbook", "empty", route=request.path)
        return core.api_error("empty")

    if len(message) > core.MAX_MSG_LEN:
        message = message[: core.MAX_MSG_LEN]

    rec = {
        "ts": core.now_utc_iso(),
        "user": user,
        "message": message,
        "id": core.NEXT_MSG_ID,
    }
    core.GUESTBOOK.append(rec)
    core.NEXT_MSG_ID += 1

    core.log_attempt(
        user, True, "api_guestbook", "created",
        route=request.path, meta={"len": len(message)},
    )
    resp = core.json_ok(rec, status=201)
    resp.headers["Location"] = f"/api/v1/guestbook/messages/{rec['id']}"
    return resp
