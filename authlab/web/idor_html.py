# authlab/web/idor_html.py

import sqlite3

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort,
)

from authlab import core
from authlab.web import web_bp


@web_bp.get("/notes")
def notes_index():
    """List notes for the current user, with IDOR toggle."""
    user = session.get("user")
    if not user:
        return redirect(url_for("web.login_get"))

    with sqlite3.connect("authlab.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, owner FROM notes WHERE owner = ? ORDER BY id",
            (user,),
        )
        notes = cur.fetchall()

    reason = "index_poc" if core.IDOR_STATE == "poc" else "index_safe"
    core.log_attempt(
        user,
        True,
        "idor_surface",
        reason,
        route=request.path,
        meta={"count": len(notes)},
    )
    return render_template("notes.html", notes=notes, state=core.IDOR_STATE)


@web_bp.get("/note/<int:note_id>")
def note_view(note_id: int):
    """View note detail with optional owner check (IDOR)."""
    user = session.get("user")
    if not user:
        return redirect(url_for("web.login_get"))

    with sqlite3.connect("authlab.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, body, owner FROM notes WHERE id = ?",
            (note_id,),
        )
        note = cur.fetchone()

    if core.IDOR_STATE == "poc":
        reason = "no_owner_check"
        if not note:
            abort(404)
        core.log_attempt(
            user,
            True,
            "idor_surface",
            reason,
            route=request.path,
            meta={"note_id": note_id, "owner": note["owner"]},
        )
        return render_template("note.html", note=note, state=core.IDOR_STATE)

    if not note or note["owner"] != user:
        reason = "blocked_404"
        core.log_attempt(
            user,
            True,
            "idor_surface",
            reason,
            route=request.path,
            meta={"note_id": note_id},
        )
        abort(404)

    reason = "owner_enforced"
    core.log_attempt(
        user,
        True,
        "idor_surface",
        reason,
        route=request.path,
        meta={"note_id": note_id, "owner": note["owner"] if note else None},
    )
    return render_template("note.html", note=note, state=core.IDOR_STATE)
