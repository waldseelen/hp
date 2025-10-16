# Repository Guidelines

## Project Structure & Module Organization
- `project/` holds Django settings, shared services (`blog`, `main`, `tools`, `contact`, `chat`), and `manage.py`.
- `apps/` hosts feature apps; create new Django apps here and wire them through `project/settings/`.
- Shared UI assets live in root `templates/` and `static/`; keep app-specific templates and styles beside their module.
- `tests/` mirrors domains with `unit/`, `integration/`, `e2e/`, and `visual/` suites to keep coverage focused.
- Build tooling sits in `package.json`, `tailwind.config.js`, `postcss.config.js`, and helper scripts under `scripts/`.

## Build, Test, and Development Commands
- `make install` installs Python and Node dependencies, runs migrations, and installs pre-commit hooks.
- `make runserver` (or `python manage.py runserver`) starts Django; pair with `npm run dev` for Tailwind watch.
- `make build` compiles Tailwind CSS and collects static files; `make build-production` prepares the release bundle.
- `make test`, `make test-ui`, and `make test-coverage` wrap pytest including coverage output in `htmlcov/`.
- Use `npm run build:all`, `npm run test:e2e`, and `npm run accessibility:full` for frontend builds, Playwright, and axe automation.

## Coding Style & Naming Conventions
- Python relies on Black (88 chars), isort, flake8, and mypy; keep 4-space indentation, snake_case modules/functions, CamelCase classes.
- Templates run through `djlint`; CSS and JS lint via `stylelint` and `eslint`. Run `make format` before review.
- URL names should stay hyphenated (`portfolio-project-detail`), while Django app directories remain lower_snake_case.

## Testing Guidelines
- `pytest.ini` discovers `test_*.py` files and `Test*` classes; fast checks belong in `tests/unit/`, cross-app flows in `tests/integration/`.
- Tag scenarios with existing markers (`integration`, `performance`, `accessibility`, etc.) so targeted make targets stay quick.
- Coverage must stay at or above 85% (`--cov-fail-under=85`); inspect `htmlcov/index.html` after `make test-coverage`.
- Run `npm run test:e2e` before merging UI-heavy work and attach screenshots or videos to the PR when they reveal regressions.

## Commit & Pull Request Guidelines
- Follow history conventions: leading emoji plus imperative verb (example: `:white_check_mark: Complete final validation step`).
- Keep commits focused, reference tickets in the body, and do not commit secrets or compiled assets.
- Pull requests need a feature overview, testing proof, and notes on migrations or security impacts.
- Ensure `make check-all` passes before requesting review and flag any known gaps in the PR description.

## Security & Configuration Tips
- Copy `.env.example` to `.env` and populate secrets locally; never commit the result.
- Run `make security` before release branches to execute Bandit and resolve high-severity findings.

## Agent Memory Bank (Codex CLI)
- Purpose: Maintain persistent project context across sessions. I must read all files in `memory-bank/` at the start of every task and keep them current.
- Location: Root `memory-bank/` directory with core Markdown files.
- Priority: Keep `activeContext.md` and `progress.md` freshest; they guide current work.

### Memory Bank Structure
- Core files:
  - `projectbrief.md` — Scope, goals, and source of truth
  - `productContext.md` — Why/how the product should work
  - `activeContext.md` — Current focus, recent changes, next steps
  - `systemPatterns.md` — Architecture, patterns, critical paths
  - `techContext.md` — Tech stack, dependencies, tooling
  - `progress.md` — Status, what works, known gaps
- Additional context: Add subfolders or docs under `memory-bank/` for APIs, integrations, tests, and deploys when complexity warrants it.

### Core Workflows
- Plan Mode:
  - Read all memory bank files
  - Verify completeness; if gaps, propose a plan
  - Develop a strategy and share the approach
- Act Mode:
  - Re-check memory bank
  - Update docs as context changes
  - Execute the task, then document changes

### Update Triggers
- After significant changes or discoveries
- When the user requests “update memory bank” (must review all files)
- When context needs clarification or decisions shift

### Repo-Specific Notes
- Follow the commands and conventions above when proposing or executing changes.
- Preferred structure and naming are enforced by the linters and `make format`.
- Keep coverage ≥ 85% and run targeted test suites as appropriate.
