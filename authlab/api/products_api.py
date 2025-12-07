# authlab/api/products_api.py

import sqlite3
from urllib.parse import urlencode

from flask import request

import authlab.core as core
from . import api_bp


@api_bp.get("/products")
def api_products_list():
    """
    Case-insensitive search, price range filters, whitelisted sort, pagination,
    and RFC 5988 Link headers.
    """
    user, resp = core.require_auth_json()
    if resp:
        return resp

    rate_key = f"{core.API_PRODUCTS_BUCKET}:{core.client_ip()}|{user.lower()}"
    allowed, retry_after = core.rl_check_and_hit(
        rate_key, core.WINDOW_SEC, core.MAX_ATTEMPTS
    )
    if not allowed:
        core.log_attempt(
            user, True, "api_products", "ratelimited",
            route=request.path, meta={"retry_after": retry_after},
        )
        err = core.api_error("ratelimited")
        err.headers["Retry-After"] = str(retry_after)
        return err

    q = (request.args.get("q") or "").strip()

    min_price_raw = request.args.get("min_price")
    max_price_raw = request.args.get("max_price")
    min_price = core.parse_float_or_none(min_price_raw)
    max_price = core.parse_float_or_none(max_price_raw)

    if (min_price_raw not in (None, "") and min_price is None) or (
        max_price_raw not in (None, "") and max_price is None
    ):
        return core.api_error("invalid_param")

    if (
        min_price is not None
        and max_price is not None
        and max_price < min_price
    ):
        return core.api_error("invalid_range")

    limit = core.parse_int(
        request.args.get("limit"), default=20, min_v=1, max_v=100
    )
    offset = core.parse_int(
        request.args.get("offset"), default=0, min_v=0, max_v=10_000
    )

    cols = {"id": "id", "name": "name", "price": "price"}
    dirs = {"asc": "ASC", "desc": "DESC"}

    sort_by_raw = (request.args.get("sort_by") or "name").lower()
    sort_dir_raw = (request.args.get("sort_dir") or "asc").lower()

    sort_col = cols.get(sort_by_raw)
    if not sort_col:
        return core.api_error("invalid_sort_by")

    sort_dir = dirs.get(sort_dir_raw)
    if not sort_dir:
        return core.api_error("invalid_sort_dir")

    order_sql = f" ORDER BY {sort_col} {sort_dir}, id ASC"

    where_parts = []
    params = []

    if q:
        where_parts.append("name LIKE ? COLLATE NOCASE")
        params.append(f"%{q}%")

    if min_price is not None:
        where_parts.append("price >= ?")
        params.append(min_price)

    if max_price is not None:
        where_parts.append("price <= ?")
        params.append(max_price)

    where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

    with sqlite3.connect("authlab.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(
            f"SELECT COUNT(*) AS c FROM products{where_sql};", tuple(params)
        )
        row = cur.fetchone()
        total = int(row["c"]) if row else 0

        page_sql = (
            f"SELECT id, name, price FROM products"
            f"{where_sql}{order_sql} LIMIT ? OFFSET ?;"
        )
        page_params = tuple(params) + (limit, offset)
        cur.execute(page_sql, page_params)
        items = [dict(r) for r in cur.fetchall()]

        qp = {"limit": limit}
        if q:
            qp["q"] = q
        if min_price is not None:
            qp["min_price"] = min_price
        if max_price is not None:
            qp["max_price"] = max_price
        qp["sort_by"] = sort_by_raw
        qp["sort_dir"] = sort_dir_raw

        links = []
        if offset > 0:
            prev_qp = dict(qp)
            prev_qp["offset"] = max(0, offset - limit)
            prev_url = f"/api/v1/products?{urlencode(prev_qp)}"
            links.append(f'<{prev_url}>; rel="prev"')

        if offset + limit < total:
            next_qp = dict(qp)
            next_qp["offset"] = offset + limit
            next_url = f"/api/v1/products?{urlencode(next_qp)}"
            links.append(f'<{next_url}>; rel="next"')

        resp_headers = {}
        if links:
            resp_headers["Link"] = ", ".join(links)

    core.log_attempt(
        user, True, "sqli_surface", "param_safe",
        route=request.path, meta={"q": q},
    )
    core.log_attempt(
        user,
        True,
        "api_products",
        "list",
        route=request.path,
        meta={
            "q": q,
            "min": min_price,
            "max": max_price,
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
