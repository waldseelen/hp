# Active Context

Current Focus
- Establish and adopt the Memory Bank workflow for this repository.
- Align AGENTS.md with memory practices and repo conventions.

Recent Changes
- Created `memory-bank/` with core files.
- Updated root `AGENTS.md` with Memory Bank guidance and repo-specific notes.

Next Steps
- Fill `productContext.md` with validated goals, personas, and key flows.
- Confirm Django ↔ frontend boundaries and deployment expectations.
- Run `make check-all` locally; address any failing linters/tests.
- Ensure coverage ≥ 85% and update `progress.md` with status.

Active Decisions & Preferences
- Default to minimal, focused changes that align with existing style and structure.
- Prioritize updating `activeContext.md` and `progress.md` after meaningful changes.

Learnings & Insights
- Monorepo includes Django (`project/`, `apps/`) and a Next/Tailwind frontend footprint (`frontend/`, `.next/`).
- Celery scaffolding present (`project/celery.py`), broker/backend configuration to be confirmed.
- Multiple performance, accessibility, and PWA summary docs indicate quality/perf focus.

