# System Patterns

Architecture
- Django monolith with modular apps under `project/` and `apps/`.
- Frontend tooling present (Next.js/Tailwind), likely for styles and/or separate SPA pages.
- Celery entrypoint exists (`project/celery.py`), implies async task capability.

Key Technical Decisions (Observed)
- Python formatting and linting stack: Black, isort, flake8, mypy, Ruff cache present.
- Frontend stack: Tailwind, PostCSS, Playwright, Jest; Next.js build artifacts in `.next/`.
- Makefile orchestrates install/build/test/security tasks.

Design/Code Patterns
- App-specific templates and static colocated; shared assets at repo root.
- URL naming prefers hyphenation; Django apps use lower_snake_case.
- Tests organized by unit/integration/e2e/visual in `tests/`.

Critical Implementation Paths
- Local dev: `make install` → `make runserver` (+ `npm run dev`).
- CI checks: `make check-all` before PRs; coverage must be ≥ 85%.
- Build: `make build`/`make build-production`; static collection expected.

Risks & Considerations
- Validate Celery broker/backend settings before enabling background tasks.
- Confirm how/if Next.js output integrates with Django templates/static.
- Ensure environment secrets via `.env` (never committed) per guidelines.

