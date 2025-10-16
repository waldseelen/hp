# Tech Context

Languages & Frameworks
- Python (Django), Celery scaffold present
- JavaScript/TypeScript (Next.js, Playwright, Jest)
- CSS (Tailwind, PostCSS)

Tooling & Commands
- Make targets: `make install`, `make runserver`, `make build`, `make build-production`, `make test`, `make test-ui`, `make test-coverage`, `make security`, `make format`, `make check-all`.
- Node scripts: `npm run dev`, `npm run build:all`, `npm run test:e2e`, `npm run accessibility:full`.

Quality Gates
- Lint/format: Black (88), isort, flake8, mypy; djlint; stylelint; eslint.
- Coverage: ≥ 85% enforced; see `htmlcov/` after coverage runs.

Dependencies & Config
- Python: `requirements.txt`, `pyproject.toml`, virtual envs (`.venv/`, `venv/`).
- Node: `package.json`, `tailwind.config.js`, `postcss.config.js`, `playwright.config.js`, `jest.config.js`.
- Deployment: `Procfile`, `railway.*`, `vercel.json` present; confirm actual targets.

Environments
- Local: `.env` from `.env.example` (never commit real secrets).
- CI: Run `make check-all` and targeted suites using markers as needed.

Open Items
- Confirm Celery broker/result backend and monitoring (Flower, etc.) if used.
- Clarify Prisma/microservices directories’ roles and integration points.

