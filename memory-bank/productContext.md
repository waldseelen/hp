# Product Context

Why This Project Exists
- Unknown from code alone. Please provide a concise value proposition and primary audience.
- Observed modules suggest content publishing (`blog`), communication (`contact`, `chat`), and portfolio (`portfolio_site`). Confirm.

Problems It Solves
- Likely: publishing content, showcasing work, and enabling user contact/interaction.
- Specify operational needs (e.g., moderation, scheduling, analytics) when known.

How It Should Work
- Follow repo workflows: `make runserver`/`python manage.py runserver` with `npm run dev` for Tailwind watch.
- Build pipeline via `make build` or `make build-production`.
- Testing via `make test`, `make test-ui`, `make test-coverage`; Playwright and Jest for frontend.

User Experience Goals
- Aim for accessible, fast, and resilient pages.
- Reference existing audits and summaries in the root:
  - `ACCESSIBILITY_AUDIT_REPORT.md`, `ACCESSIBILITY_GUIDELINES.md`
  - `PERFORMANCE_OPTIMIZATION_SUMMARY.md`, `PWA_IMPLEMENTATION_SUMMARY.md`
  - `CSS_OPTIMIZATION_SUMMARY.md`, `ICON_OPTIMIZATION_SUMMARY.md`, `FONT_OPTIMIZATION_SUMMARY.md`

Unknowns / To Clarify
- Primary personas and their top 3 tasks.
- Content strategy (frequency, formats) and internationalization needs.
- Requirements for real-time chat, notifications, or external integrations.

