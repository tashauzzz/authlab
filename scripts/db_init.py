#!/usr/bin/env python3
"""
Recreate and seed authlab.db for all demos.
Usage (from project root): python scripts/db_init.py
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "authlab.db"
SQL_DIR = BASE_DIR / "scripts"


PRODUCTS = [
    ("Laptop Go 12", 799.0), ("Laptop Air 13", 999.0), ("Laptop Lite 13", 849.0),
    ("Laptop Pro 14", 1299.0), ("Laptop Work 14", 1099.0), ("Laptop Flex 14", 1049.0),
    ("Laptop Gamer 15", 1499.0), ("Laptop Studio 15", 1599.0),
    ("Laptop Ultra 16", 1799.0), ("Laptop Flex 16", 1399.0),
    ("Laptop Neo 13", 929.0), ("Laptop Edge 14", 1149.0),
    ("Phone Max", 899.0), ("Phone Mini", 499.0),
    ("Router AX1800", 119.0), ("Router AX3000", 139.0),
    ('Monitor 27"', 249.0), ("Keyboard Mech", 89.0),
]

NOTES = [
    # admin (3)
    ("Admin note #1", "Seeded note 1 for admin", "admin"),
    ("Admin note #2", "Seeded note 2 for admin", "admin"),
    ("Admin note #3", "Seeded note 3 for admin", "admin"),

    # alice (3)
    ("Alice note #1", "Seeded note 1 for alice", "alice"),
    ("Alice note #2", "Seeded note 2 for alice", "alice"),
    ("Alice note #3", "Seeded note 3 for alice", "alice"),
]

def main():
    # 0) fresh start
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH.as_posix())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) tables
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE notes (
            id    INTEGER PRIMARY KEY,
            title TEXT    NOT NULL,
            body  TEXT    NOT NULL,
            owner TEXT    NOT NULL
        );
    """)

    # 2) seed
    cur.executemany("INSERT INTO products (name, price) VALUES (?,?)", PRODUCTS)
    cur.executemany("INSERT INTO notes (title, body, owner) VALUES (?,?,?)", NOTES)

    # 3) apply NOCASE index via migration script
    idx_file = SQL_DIR / "001_products_nocase_index.sql"
    if idx_file.exists():
        cur.executescript(idx_file.read_text(encoding="utf-8"))

    conn.commit()

    # 4) mini-summary
    cur.execute("SELECT COUNT(*) AS c FROM products;")
    pc = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM notes;")
    nc = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM notes WHERE owner='admin';")
    ac = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM notes WHERE owner='alice';")
    bc = cur.fetchone()["c"]

    conn.close()

    print("authlab.db recreated")
    print(f"products: {pc} rows (NOCASE index applied)")
    print(f"notes: {nc} rows (admin={ac}, alice={bc})")

if __name__ == "__main__":
    main()
