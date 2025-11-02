# Railway Deployment Guide

This document describes how to deploy the portfolio project to [Railway](https://railway.app/) using either the Railway dashboard/CLI or the provided GitHub Actions workflow.

## Prerequisites

- Railway account connected to GitHub
- Railway CLI (`npm i -g @railway/cli`) or access to the Railway dashboard
- Provisioned PostgreSQL database (can be created from the Railway templates)
- Secrets ready for production (see the list below)

## Required Environment Variables

Set these variables inside the Railway project (Project → Variables). Most values can be copied from `.env.example`.

| Variable | Description | Notes |
|----------|-------------|-------|
| `SECRET_KEY` | Django secret key | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DATABASE_URL` | PostgreSQL connection string | Automatically created when you add a PostgreSQL template |
| `DEBUG` | Should be `False` in production | |
| `ALLOWED_HOSTS` | Comma-separated list of hostnames | Include Railway domain, e.g. `your-app.up.railway.app` |
| `DJANGO_SETTINGS_MODULE` | Django settings module | Set to `project.settings.production` |
| `REDIS_URL` | Optional Redis cache URL | Only if you provision Redis |

The startup script (`scripts/railway-start.sh`) validates that `SECRET_KEY` and `DATABASE_URL` exist before starting Gunicorn.

## One-Time Railway Setup

1. **Create Project** – From the Railway dashboard create a new project and connect it to your GitHub repository (or plan to deploy via CLI).
2. **Add Services** – Provision the following services from the Railway templates:
   - **PostgreSQL** (required)
   - **Redis** (optional, but the project can use it if available)
3. **Configure Environment Variables** – Add the required variables listed above. The Postgres template populates `DATABASE_URL` automatically.
4. **Set Build/Start Commands** – Railway reads `railway.toml` / `railway.json` in the repo, so no manual command configuration is necessary.

## Deploying with the CLI

```bash
railway login              # authenticate (opens browser)
railway init                # link local repo to the Railway project
railway up                  # build and deploy using Nixpacks
```

During deployment, Nixpacks runs `npm run build:all`, collects static files, performs migrations, and finally executes `scripts/railway-start.sh` (Gunicorn).

## Deploying with GitHub Actions

A workflow named **Deploy to Railway** is included at `.github/workflows/railway-deploy.yml`.

1. Create a Railway API token (Railway dashboard → Account → API Tokens).
2. Add the token as a secret called `RAILWAY_TOKEN` in the GitHub repository.
3. Push to the `main` branch or trigger the workflow manually from the Actions tab.

The action runs the official [`railwayapp/railway-action`](https://github.com/railwayapp/railway-action) which calls `railway up` for the `portfolio-prod` service in the `production` environment.

## Post-Deployment Checklist

- Confirm that the Railway deployment logs show migrations and static collection succeeded.
- Visit the Railway-provided domain (e.g. `https://your-app.up.railway.app/`).
- Hit the `/health/` endpoint to confirm the application responds with HTTP 200.
- Update DNS to point a custom domain at the Railway service if desired.

## Troubleshooting

| Symptom | Possible Cause | Fix |
|---------|----------------|-----|
| Deploy fails during build | Missing Node dependencies or build toolkit | Ensure `npm install` completed locally and commit compiled assets when necessary. |
| `SECRET_KEY` / `DATABASE_URL` error on startup | Environment variables not set | Add them under Railway → Variables or verify service templates provisioned correctly. |
| Static files return 404 | `collectstatic` failed | Re-run deployment and inspect build logs for errors; ensure `npm run build:all` succeeds. |

For additional automation tasks see `prompt_railway.yml` which documents the end-to-end provisioning workflow for automation agents.
