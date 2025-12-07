# authlab/api/auth_api.py

from flask import request, session

import authlab.core as core
from . import api_bp

@api_bp.get("/auth/session")
def api_session():
    """
    Create or reuse an API session.

    If the user is already authenticated via cookie session, or DEV_MODE +
    valid DEV_API_KEY is used, return a JSON envelope:

        { "user": "...", "csrf_token": "..." }
    """
    user, resp = core.require_auth_json()
    if resp:
        return resp
    
    session["user"] = user
    token = core.ensure_csrf_token()
    data = {"user": user, "csrf_token": token}

    core.log_attempt(user, True, "api_session", "ok", route=request.path, meta=None)
    return core.json_ok(data)


