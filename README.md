# mcp-db-wrapper-example

The [foro.sh](https://foro.sh) database starter: an MCP server that wraps a
small SQL database. It comes with one demo table (`notes`) so there's
something to query straight away, and tools your AI coding agent can use to
read and write it.

## Tools

| Tool | What it does |
| --- | --- |
| `list_tables()` | See every table in the database |
| `query(sql, params)` | Run a read query (`SELECT ...`) and get the rows back |
| `insert(table, values)` | Add one row to a table |

## Make it yours

This is a starting point, not a finished product. Open this repo in Claude
Code (or another AI coding agent) and ask it to:

- add the tables your project actually needs
- add tools for the specific things you want to do with your data — not just
  raw `query`/`insert` — e.g. `find_customer(email)`, `log_event(...)`
- point it at a real database once you have one (see Storage below)

You don't need to know FastMCP or the Model Context Protocol to do any of
this — describe what you want in plain language and let the agent write the
code.

## Storage

By default this runs on a local SQLite file (`db.sqlite3`) that's created
automatically — no setup required. It resets whenever the server restarts or
redeploys, which is fine for trying things out but not for data you care
about.

To use a different SQLite file — for example one on a persistent volume you
mount yourself — set the `DATABASE_URL` environment variable (as a secret in
your foro.sh project) to its path. For a different kind of database
entirely (e.g. Postgres), ask your coding agent to swap in the matching
driver.

## Run it locally

```sh
uv run server.py
```

The server speaks MCP over streamable HTTP at `http://localhost:8000/mcp`
(set `PORT` to change the port — the same name foro injects when it deploys
you).

## Deploy it

Its `pyproject.toml` is all foro.sh needs, so this repo deploys as-is: sign
in, pick this repo, deploy.
