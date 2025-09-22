# Performance Notes

- **Critical CSS layering**: `app-base.css` provides shared reset + layout; keep file under 12KB to inline for LCP-critical templates if needed. Tailwind build (`output.css`) can be tree-shaken by pruning unused utilities before production deploy.
- **Font strategy**: Continue using system stack (`Inter` fallback) via tokens to avoid additional network hops; if custom fonts reintroduced, add `font-display: swap` declarations.
- **Script loading**: `ui-shell.js` uses `defer` and minimal observers; remaining vendor scripts could be guarded behind feature detection (e.g. skip `cdn-performance.js` on non-production builds).
- **Media handling**: Ensure hero and card illustrations include `loading="lazy"` and `decoding="async"` attributes; CSS sets `img { max-width: 100%; }` to prevent layout shifts.
- **Caching**: Tokens rely on `?v={% now 'U' %}` cache-busting. For production, prefer hashed filenames to avoid stamping on every request.
- **CLS protections**: Navigation height is locked via `nav-shell` styles and `.h-16` spacer removed in favour of sticky nav; reduces top-of-page shift.
