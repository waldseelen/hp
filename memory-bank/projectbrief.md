# Project Brief

Purpose
- Establish a durable source of truth for scope and goals.
- Ensure the agent can reliably resume work after resets.

Evidence-Based Snapshot
- Backend: Django project under `project/` with feature apps (e.g., `blog`, `main`, `tools`, `contact`, `chat`).
- Frontend: Node/Next.js present (`frontend/`, `.next/`), Tailwind pipeline configured (`tailwind.config.js`, `postcss.config.js`).
- Shared assets: `templates/`, `static/`, and collected assets in `staticfiles/`.
- Tests: `tests/` with `pytest.ini`, Playwright setup (`playwright.config.js`), Jest config (`jest.config.js`).
- Tooling: `Makefile` targets for install, run, build, test, coverage, security; linters and formatters configured.

Goals (Source of Truth)
- Adhere to repository guidelines in `AGENTS.md` and keep coverage ≥ 85%.
- Maintain consistent coding style (Black, isort, flake8, mypy; eslint/stylelint/djlint).
- Preserve modular app structure (`apps/` for feature apps); keep app-specific templates/styles colocated.
- Document decisions and progress in `memory-bank/` and keep `activeContext.md` current.

Scope
- Django app development and maintenance, including URLs, views, templates, and tests.
- Frontend integration via Tailwind and any Next.js assets as configured by the repo.
- CI-friendly scripts via `make` and npm to build, test, and audit.

Out of Scope (for now)
- Product assumptions beyond code evidence (fill in via `productContext.md`).
- Non-validated integrations or services not present in the repo.

Open Questions
- Confirm the product’s primary goals and key user journeys.
- Clarify the intended coupling between Django and Next.js deliverables.

