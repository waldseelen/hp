# UI Before/After Highlights

| Area | Before | After | Impact |
| --- | --- | --- | --- |
| Navigation | Fixed menu relied on inline scripts and inconsistent hit areas on small screens. | New `nav-shell` layout with consistent spacing, keyboard focus states, and auto-hide scroll behaviour handled via `ui-shell.js`. | Clearer IA and improved keyboard/mobile usability. |
| Hero (Home) | Heavy absolute backgrounds caused horizontal scroll <360px and typography scale jumped between breakpoints. | Token-driven hero with `hero__*` classes, balanced typography, and chip badges that clamp per breakpoint. | Eliminates overflow, supports micro-interactions without layout shifts. |
| Contact Form | Mixed Tailwind overrides; focus states missing; cards stacked without hierarchy on tablet. | Componentized panels (`form-panel`, `contact-panel`) with consistent spacing, focus rings, and responsive two-column grid from `contact-shell`. | Better readability, accessible form controls, predictable layout at 768–1024px. |
| Global Styles | Multiple ad-hoc fix files (`responsive-overrides.css`, `emergency-fix.css`, `svg-fix.css`, `modern-enhancements.css`) with `!important` overrides. | Consolidated design system (`design-tokens.css`, `app-base.css`, `app-typography.css`, `app-components.css`) exposing CSS variables for color, spacing, typography, radius, and shadows. | Single source of truth; easier thematic changes and consistent behaviour across pages. |
