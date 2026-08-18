---
name: deploy-this-server
description: Ship a change to this MCP server and confirm it is really live on foro.sh. Use when the user wants to deploy, redeploy, ship, publish, or go live after editing this repo, when they ask why their change isn't live yet, or when a foro.sh deploy failed and the logs need reading.
---

# Deploy this server to foro.sh

This repo is already a foro.sh project: it was created from the template
gallery, so foro.sh built it once already and it has a live
`https://<slug>.foro.sh` URL. Shipping a change is push plus redeploy, not
project setup. Never scaffold a second project for it.

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

## What this repo specifically gets wrong

- **The deployed filesystem is read only, except `/tmp`.** Anything this server
  writes has to live under `/tmp` or at a path given by the `DATABASE_URL`
  secret. A relative SQLite path fails at import with
  `sqlite3.OperationalError: unable to open database file`, and the container
  dies before the health check.
- **Deployed data does not survive a redeploy.** There are no volumes, so a
  SQLite file under `/tmp` is scratch storage. Say so plainly rather than
  letting the user believe a redeploy keeps their rows.
- **Secrets are set in the dashboard**, Secrets tab, never committed. The code
  reads them with `foro.secret("NAME")` or `os.environ`.

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

`foro-docs.read_doc("logs")` and `foro-docs.read_doc("secrets")` have the
current detail. Use `foro-docs.list_docs()` for the other slugs. If the docs MCP
server is not connected, say what you are unsure about instead of guessing.

## Done when

`foro verify` passes against the real slug URL and the user has been told what,
if anything, about their data is ephemeral.
