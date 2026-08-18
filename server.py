"""mcp-db-wrapper-example — the foro.sh database starter.

A small SQL database wrapped in MCP tools: list_tables, query, insert. Ships
with one seeded table (`notes`) so there's something to call on the first
request. State lives in a local SQLite file, which is ephemeral — see README.
"""

import os
import re
import sqlite3
import tomllib
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote

import foro
from fastmcp import FastMCP
from pydantic import Field

# [tool.mcp-db-wrapper] in pyproject.toml, not [tool.foro] - that table is
# foro.sh's own closed allowlist (see platform:apps/api/src/services/manifest.ts),
# this is application config the platform never looks at.
_CONFIG = tomllib.loads(Path(__file__).with_name("pyproject.toml").read_text())
DATABASE_TYPE = _CONFIG.get("tool", {}).get("mcp-db-wrapper", {}).get("database", "sqlite")

_SQLITE_URL_PREFIX = "sqlite:///"
_EPHEMERAL_DB_PATH = "/tmp/db.sqlite3"  # deployed containers run a read-only rootfs; /tmp is the one writable path


def _resolve_db_path() -> tuple[str, bool]:
    """The sqlite file to open, and whether it's the ephemeral default.

    Never infers the database type from DATABASE_URL - it must agree with
    the type declared in pyproject.toml, so swapping databases is a config
    edit plus a driver, not a URL scheme an agent has to know matters.
    """
    if DATABASE_TYPE != "sqlite":
        raise RuntimeError(
            f"[tool.mcp-db-wrapper].database is {DATABASE_TYPE!r}, but this "
            "starter only ships a sqlite driver. Ask your coding agent to "
            "add one for it (see README's Storage section)."
        )

    url = os.environ.get("DATABASE_URL")
    if url is None:
        return _EPHEMERAL_DB_PATH, True
    if not url.startswith(_SQLITE_URL_PREFIX):
        raise RuntimeError(
            f"DATABASE_URL is set but isn't a {_SQLITE_URL_PREFIX!r} URL, which is "
            f"what [tool.mcp-db-wrapper].database = {DATABASE_TYPE!r} expects. Fix the "
            "secret in your project's Secrets tab, or update the declared "
            "database type to match."
        )
    return url.removeprefix(_SQLITE_URL_PREFIX), False


DB_PATH, _USING_EPHEMERAL_DB = _resolve_db_path()

mcp = FastMCP(
    "mcp-db-wrapper-example",
    instructions=(
        "A SQL database this server owns. Use list_tables to see what's "
        "there, query to read (SELECT only), insert to write. Ships with a "
        "demo `notes` table — ask the user what tables and tools they "
        "actually need and add those. "
        + (
            "No DATABASE_URL secret is set, so this is running on scratch "
            "storage that's wiped on every restart and redeploy - tell the "
            "user before they rely on anything written here."
            if _USING_EPHEMERAL_DB
            else "Backed by the DATABASE_URL secret."
        )
    ),
)

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _connect(readonly: bool = False) -> sqlite3.Connection:
    # SQLite itself enforces read-only, via the `mode=ro` URI. That is what
    # makes `query` safe, rather than inspecting the SQL for a SELECT: a
    # keyword check rejects perfectly good `WITH ... SELECT` queries and has to
    # keep pace with every other statement form to be worth anything.
    dsn = f"file:{quote(DB_PATH)}?mode=ro" if readonly else DB_PATH
    conn = sqlite3.connect(dsn, uri=readonly)
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
    with _connect(readonly=True) as conn:
        try:
            rows = conn.execute(sql, params or []).fetchall()
        except sqlite3.OperationalError as err:
            if "readonly" in str(err):
                raise ValueError("query only reads. Use insert to write.") from err
            raise
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
    foro.run(mcp)
