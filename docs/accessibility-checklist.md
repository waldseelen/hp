# Accessibility Checklist

- [x] Skip link present and visible on focus (`templates/base/base.html:86`).
- [x] Focus-visible states defined for interactive elements via `app-base.css` and component classes.
- [x] Navigation supports keyboard interaction; theme toggle and search trigger exposed via button semantics.
- [x] Form controls in contact form include explicit `<label>` elements and ARIA helpers (`templates/pages/contact/form.html`).
- [x] Color contrast meets 4.5:1 using tokenised palette; gradients apply to text with sufficient luminance.
- [x] Reduced-motion preference respected by clamping animations in `app-base.css` and `ui-shell.js` fallback.
- [x] Live regions for Django flash messages use `aria-live="polite"` with tokenised surfaces for visibility.
- [ ] Comprehensive screen reader regression test — recommend NVDA + VoiceOver spot check on hero and navigation.
- [ ] End-to-end keyboard trap audit pending for modal components (`search-modal`).
