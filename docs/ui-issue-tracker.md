# UI Issue Tracker

| Issue | Location | Severity | Labels | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Horizontal overflow from hero background orbs | templates/pages/portfolio/home.html:12 | High | ui, css | Resolved | Rebuilt hero with `hero__background` + `overflow-hidden` container to remove scroll on <360px devices. |
| Inconsistent container widths relying on removed overrides | templates/base/base.html:54 | High | ui, css | Resolved | Introduced `.ds-container` tokenised layout and remapped `.container` class in `app-base.css`. |
| Skip navigation missing focus styling | templates/base/base.html:80 | Medium | accessibility, ui | Resolved | Added `.skip-link` helper with visible focus and repositioned links. |
| Theme toggle lacked persistence and aria labels | templates/components/navigation/navigation.html:34 | Medium | accessibility, ui | Resolved | Added `data-theme-toggle` API with labels and persisted state in `static/js/ui-shell.js`. |
| Contact form focus rings and spacing inconsistent | templates/pages/contact/form.html:18 | High | ui, accessibility | Resolved | Reworked form with semantic `form-field` wrappers, consistent padding, and focus-visible states. |
| Legacy scroll reveal animations stalled on reduced motion | static/css/components/app-components.css:220 | Low | performance, accessibility | Resolved | Added IntersectionObserver with reduced-motion fallback in `ui-shell.js`. |
| Duplicate `What I Do` cards causing layout shift | templates/pages/portfolio/home.html:72 | Medium | ui | Resolved | Replaced duplicated section with single grid leveraging design tokens. |
