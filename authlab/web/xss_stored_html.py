# authlab/web/xss_stored_html.py

import secrets

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from authlab import core
from authlab.web import web_bp

@web_bp.get("/guestbook")
def guestbook_get():
    """Render guestbook with stored XSS surface."""
    user = session.get("user")
    if not user:
        return redirect(url_for("web.login_get"))

    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["csrf_token"] = token

    reason = "stored_poc" if core.XSS_S_STATE == "poc" else "stored_safe"
    core.log_attempt(
        user,
        True,
        "xss_surface",
        reason,
        route=request.path,
        meta={"count": len(core.GUESTBOOK)},
    )
    return render_template(
        "guestbook.html",
        messages=core.GUESTBOOK,
        csrf_token=token,
        state=core.XSS_S_STATE,
        max_len=core.MAX_MSG_LEN,
    )

@web_bp.post("/guestbook")
def guestbook_post():
    """Handle guestbook POST, intentionally storing raw input."""
    user = session.get("user")
    if not user:
        return redirect(url_for("web.login_get"))

    form_csrf = request.form.get("csrf_token")
    sess_csrf = session.get("csrf_token")
    if not form_csrf or not sess_csrf or sess_csrf != form_csrf:
        core.log_attempt(user, True, "invalid", "csrf_bad", route=request.path)
        new_token = secrets.token_hex(32)
        session["csrf_token"] = new_token
        return (
            render_template(
                "guestbook.html",
                messages=core.GUESTBOOK,
                csrf_token=new_token,
                state=core.XSS_S_STATE,
                error="Invalid session",
                max_len=core.MAX_MSG_LEN,
            ),
            400,
        )

    message = (request.form.get("message") or "").strip()
    if not message:
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_hex(32)
            session["csrf_token"] = token
        return (
            render_template(
                "guestbook.html",
                messages=core.GUESTBOOK,
                csrf_token=token,
                state=core.XSS_S_STATE,
                error="Message required",
                max_len=core.MAX_MSG_LEN,
            ),
            400,
        )

    if len(message) > core.MAX_MSG_LEN:
        message = message[: core.MAX_MSG_LEN]

    core.GUESTBOOK.append(
        {
            "ts": core.now_utc_iso(),
            "user": user,
            "message": message,
        }
    )
    core.log_attempt(
        user,
        True,
        "xss_surface",
        "stored_raw",
        route=request.path,
        meta={"len": len(message)},
    )

    # PRG
    return redirect(url_for("web.guestbook_get"))