# authlab/api/notes_api.py

import sqlite3
from urllib.parse import urlencode

from flask import request

import authlab.core as core
from . import api_bp


@api_bp.get("/notes")
def api_notes():
    """
    Return only the current user's notes with:
    - offset-based pagination,
    - whitelist sort (id|title),
    - RFC 5988 Link header (prev/next).
    """
    user, resp = core.require_auth_json()
    if resp:
        return resp

    rate_key = f"{core.API_NOTES_BUCKET}:{core.client_ip()}|{user.lower()}"
    allowed, retry_after = core.rl_check_and_hit(
        rate_key, core.WINDOW_SEC, core.MAX_ATTEMPTS
    )
    if not allowed:
        core.log_attempt(
            user, True, "api_notes", "ratelimited",
            route=request.path, meta={"retry_after": retry_after},
        )
        err = core.api_error("ratelimited")
        err.headers["Retry-After"] = str(retry_after)
        return err

    owner = user.lower()

    limit = core.parse_int(
        request.args.get("limit"), default=20, min_v=1, max_v=100
    )
    offset = core.parse_int(
        request.args.get("offset"), default=0, min_v=0, max_v=10_000
    )

    cols = {"id": "id", "title": "title"}
    dirs = {"asc": "ASC", "desc": "DESC"}

    sort_by_raw = (request.args.get("sort_by") or "title").lower()
    sort_dir_raw = (request.args.get("sort_dir") or "asc").lower()

    sort_col = cols.get(sort_by_raw)
    if not sort_col:
        return core.api_error("invalid_sort_by")

    sort_dir = dirs.get(sort_dir_raw)
    if not sort_dir:
        return core.api_error("invalid_sort_dir")

    order_sql = f" ORDER BY {sort_col} {sort_dir}, id ASC"
    where_sql = " WHERE owner = ?"
    where_params = (owner,)

    with sqlite3.connect("authlab.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        count_sql = "SELECT COUNT(*) AS c FROM notes" + where_sql + ";"
        cur.execute(count_sql, where_params)
        row_count = cur.fetchone()
        total = int(row_count["c"]) if row_count else 0

        page_sql = (
            "SELECT id, title FROM notes"
            + where_sql
            + order_sql
            + " LIMIT ? OFFSET ?;"
        )
        page_params = where_params + (limit, offset)
        cur.execute(page_sql, page_params)
        items = [dict(r) for r in cur.fetchall()]

        qp = {
            "limit": limit,
            "sort_by": sort_by_raw,
            "sort_dir": sort_dir_raw,
        }
        links = []
        if offset > 0:
            prev_qp = dict(qp)
            prev_qp["offset"] = max(0, offset - limit)
            prev_url = f"/api/v1/notes?{urlencode(prev_qp)}"
            links.append(f'<{prev_url}>; rel="prev"')
        if offset + limit < total:
            next_qp = dict(qp)
            next_qp["offset"] = offset + limit
            next_url = f"/api/v1/notes?{urlencode(next_qp)}"
            links.append(f'<{next_url}>; rel="next"')

        resp_headers = {}
        if links:
            resp_headers["Link"] = ", ".join(links)

    core.log_attempt(
        user,
        True,
        "api_notes",
        "list",
        route=request.path,
        meta={
            "user": owner,
            "sort": f"{sort_by_raw}:{sort_dir_raw}",
            "limit": limit,
            "offset": offset,
            "count": len(items),
            "total": total,
        },
    )

    return core.json_ok(
        {
            "items": items,
            "count": len(items),
            "total": total,
            "offset": offset,
            "limit": limit,
        },
        headers=resp_headers,
    )


@api_bp.get("/notes/<int:note_id>")
def api_notes_detail(note_id: int):
    """
    Return a single note owned by the current user.
    Non-existent or foreign notes are masked behind the same JSON 404.
    """
    user, resp = core.require_auth_json()
    if resp:
        return resp

    rate_key = f"{core.API_NOTES_BUCKET}:{core.client_ip()}|{user.lower()}"
    allowed, retry_after = core.rl_check_and_hit(
        rate_key, core.WINDOW_SEC, core.MAX_ATTEMPTS
    )
    if not allowed:
        core.log_attempt(
            user, True, "api_notes", "ratelimited_detail",
            route=request.path, meta={"retry_after": retry_after},
        )
        err = core.api_error("ratelimited")
        err.headers["Retry-After"] = str(retry_after)
        return err

    owner = user.lower()

    with sqlite3.connect("authlab.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        query = (
            "SELECT id, title, body FROM notes "
            "WHERE id = ? AND owner = ? LIMIT 1;"
        )
        params = (note_id, owner)
        cur.execute(query, params)
        row = cur.fetchone()

    if not row:
        core.log_attempt(
            user, True, "api_notes", "detail_masked_404",
            route=request.path, meta={"note_id": note_id},
        )
        return core.api_error("not_found")

    data = {"id": row["id"], "title": row["title"], "body": row["body"]}
    core.log_attempt(
        user, True, "api_notes", "detail_ok",
        route=request.path, meta={"note_id": note_id},
    )
    return core.json_ok(data)
