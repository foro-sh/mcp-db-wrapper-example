---
name: deploy-this-server
description: Ship a change to this MCP server and confirm it is really live on foro.sh. Use when the user wants to deploy, redeploy, ship, publish, or go live after editing this repo, when they ask why their change isn't live yet, or when a foro.sh deploy failed and the logs need reading.
---

# Deploy this server to foro.sh

Created from the foro.sh template gallery, this repo is already a foro.sh
project: the platform built it once and it has a live `https://<slug>.foro.sh`
URL. Shipping a change is push plus redeploy, not project setup, so never
scaffold a second project or a second repo for it.

If the dashboard shows no project for this repo, it was cloned rather than
created from the gallery. Then it is an ordinary new project: create it in the
dashboard against this repo, and the rest of this skill applies unchanged.

## 1. Prove it locally before pushing

```bash
uvx foro check
```

Fast, exits on its own, and it is the same validation foro.sh runs at deploy
time. It has to pass. Warnings do not block a deploy but they name what will be
slow or non-reproducible about it.

```bash
uvx foro dev
```

Runs the server exactly the way the platform will and completes a real MCP
handshake. If it says it would pass the health check, the deploy will too. It
then keeps running until interrupted, so run it in the background or with a
timeout rather than waiting on it.

## 2. Push

foro.sh builds from this repo's branch on GitHub, so a change that is only on
disk is not a change the platform can see:

```bash
git add -A && git commit -m "..." && git push
```

## 3. Redeploy

- **Auto-deploy on push** is a Starter plan feature and off by default. If it is
  on, the push in step 2 is the deploy.
- Otherwise open the project in the foro.sh dashboard and press **Redeploy**.

There is no `foro deploy` command yet. Do not claim a command shipped the code.

## 4. Verify, do not assume

A green deploy only means the container answered a probe. Prove it serves MCP:

```bash
uvx foro verify https://<slug>.foro.sh
```

Read the real slug off the dashboard. It is randomly generated
(`adjective-noun-4char`) and immutable, never derived from the project name, so
never predict one.

## Constraints this server runs under

- **The deployed filesystem is read-only, except `/tmp`.** `server.py` already
  defaults its SQLite file to `/tmp/db.sqlite3` for this reason. Anything
  *else* you make it write, a cache, an export, a log file, has the same
  constraint: a relative path fails with
  `sqlite3.OperationalError: unable to open database file` or its equivalent,
  and the container dies before the health check.
- **Deployed data does not survive a redeploy.** There are no volumes, so
  `/tmp` is scratch storage. Say so plainly rather than letting the user
  believe a redeploy keeps their rows.
- **Secrets are set in the dashboard**, Secrets tab, never committed. The code
  reads them with `foro.secret("NAME")` or `os.environ`.
- **The database type lives in `[tool.mcp-db-wrapper]` in `pyproject.toml`**,
  and `server.py` refuses to boot when `DATABASE_URL` disagrees with it. Switch
  database by editing that key and adding the driver, not by setting a
  different URL. Never move application config into `[tool.foro]`: that table
  is foro.sh's own closed allowlist and an unknown key fails the deploy.
- **This repo ships no `uv.lock`**, so foro.sh installs unlocked. Adding one
  makes builds reproducible and switches the platform to a frozen install, so
  from then on a lockfile that drifts from `pyproject.toml` fails the build
  outright. If you add a dependency after that, run `uv lock` and commit it.

## When a deploy fails

Two separate log streams in the dashboard, and picking the wrong one wastes the
session:

- **Build log**: raw `docker build` output. Dependency and lockfile problems
  live here.
- **Deploy log**: clone, config validation, container start, health check, and
  the failure reason. A bad entrypoint, an unset secret, a server that never
  bound its port, or a boot crash lives here.

Most failures reproduce locally with `uvx foro dev` in seconds instead of as a
60 second cloud health check timeout.

https://foro.sh/docs/logs and https://foro.sh/docs/secrets have the current
detail, and https://foro.sh/docs indexes the rest. Read the page rather than
recalling it: this file ships with the repo, so it ages, and the docs do not.

## Done when

`foro verify` passes against the real slug URL and the user has been told what,
if anything, about their data is ephemeral.
