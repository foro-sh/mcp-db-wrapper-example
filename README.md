# mcp-db-wrapper-example

The [foro.sh](https://foro.sh) database starter: an MCP server that wraps a
small SQL database. It comes with one demo table (`notes`) so there's
something to query straight away, and tools your AI coding agent can use to
read and write it.

> **Opening this in Claude Code?** Nothing to install. The repo ships the
> skills your agent needs in `.claude/skills/`: how to deploy this server, and
> how to add tools that are worth what they cost a model to carry.

## Before you deploy

Without any setup, this runs on a local SQLite file that's wiped on every
restart and redeploy - fine for trying it out, not for data you care about.

To keep data around, set **`DATABASE_URL`** as a secret in your project's
**Secrets** tab (a `sqlite:///` URL pointing at a file on a volume you
control). For a different kind of database entirely, see Storage below.

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

The database type is declared in `pyproject.toml`:

```toml
[tool.mcp-db-wrapper]
database = "sqlite"
```

`server.py` reads this and refuses to boot if `DATABASE_URL` doesn't match it
(e.g. a non-`sqlite:///` URL while `database = "sqlite"`), since the type is
config, not something inferred from whatever URL happens to be set.

By default, with no `DATABASE_URL` secret, this runs on `/tmp/db.sqlite3`,
created automatically, no setup required, and **wiped on every restart and
redeploy** (the platform mounts no persistent volumes). Set `DATABASE_URL` to
a `sqlite:///` path on a volume you control to keep data around. For a
different kind of database entirely (e.g. Postgres), ask your coding agent to
swap in the matching driver and update `database` above to match.

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
