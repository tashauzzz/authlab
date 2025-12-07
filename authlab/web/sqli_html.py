# authlab/web/sqli_html.py

import sqlite3

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from authlab import core
from authlab.web import web_bp


@web_bp.get("/products")
def products():
    """Products listing with SQLi PoC or safe mode."""
    user = session.get("user")
    if not user:
        return redirect(url_for("web.login_get"))

    q = request.args.get("q", "")
    reason = "concat_raw" if core.SQLI_STATE == "poc" else "param_safe"

    with sqlite3.connect("authlab.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if core.SQLI_STATE == "poc":
            sql = f"SELECT id, name, price FROM products WHERE name LIKE '%{q}%';"
            cur.execute(sql)
            results = cur.fetchall()
        else:
            search = f"%{q}%"
            cur.execute(
                "SELECT id, name, price FROM products WHERE name LIKE ?;",
                (search,),
            )
            results = cur.fetchall()

    core.log_attempt(
        user,
        True,
        "sqli_surface",
        reason,
        route=request.path,
        meta={"q": q},
    )
    return render_template("products.html", q=q, results=results, state=core.SQLI_STATE)
