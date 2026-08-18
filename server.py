"""mcp-db-wrapper-example — the foro.sh database starter.

A small SQL database wrapped in MCP tools: list_tables, query, insert. Ships
with one seeded table (`notes`) so there's something to call on the first
request. State lives in a local SQLite file, which is ephemeral — see README.
"""

import os
import re
import sqlite3
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP(
    "mcp-db-wrapper-example",
    instructions=(
        "A SQL database this server owns. Use list_tables to see what's "
        "there, query to read (SELECT only), insert to write. Ships with a "
        "demo `notes` table — ask the user what tables and tools they "
        "actually need and add those."
    ),
)

# DATABASE_URL lets a deployer point this at a SQLite file on a volume they
# control instead of the default ephemeral one — see README's Storage
# section. Not a general connection string: this stays SQLite-only by design.
DB_PATH = os.environ.get("DATABASE_URL", "db.sqlite3").removeprefix("sqlite:///")

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _seed(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS notes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL)"
    )
    if conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO notes (title, body) VALUES (?, ?)",
            ("Welcome", "Ask your coding agent to replace this table with your own."),
        )
        conn.commit()


with _connect() as _conn:
    _seed(_conn)


def _check_identifier(name: str, kind: str) -> None:
    if not _IDENTIFIER.match(name):
        raise ValueError(f"invalid {kind} name: {name!r}")


TableName = Annotated[str, Field(examples=["notes"])]
SqlQuery = Annotated[str, Field(examples=["SELECT * FROM notes"])]
RowValues = Annotated[dict[str, Any], Field(examples=[{"title": "Milk", "body": "2%, one carton"}])]


@mcp.tool()
def list_tables() -> list[str]:
    """List every table in the database."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    return [row["name"] for row in rows]


@mcp.tool()
def query(sql: SqlQuery, params: list[Any] | None = None) -> list[dict[str, Any]]:
    """Run a read-only SQL query (SELECT only) and return the matching rows."""
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("query only runs SELECT statements — use insert to write")
    with _connect() as conn:
        rows = conn.execute(sql, params or []).fetchall()
    return [dict(row) for row in rows]


@mcp.tool()
def insert(table: TableName, values: RowValues) -> int:
    """Insert one row into a table and return its new rowid."""
    _check_identifier(table, "table")
    for column in values:
        _check_identifier(column, "column")
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    with _connect() as conn:
        cursor = conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            list(values.values()),
        )
        conn.commit()
        return cursor.lastrowid


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        # Behind foro.sh's reverse proxy, requests arrive with the public
        # hostname — FastMCP's DNS-rebinding Host check would reject them.
        # Access control is the platform's bearer token instead.
        host_origin_protection=False,
    )
