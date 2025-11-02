# Accessibility Guidelines

This document outlines the accessibility standards and guidelines for the Portfolio Website project to ensure WCAG 2.1 AA compliance.

## Table of Contents

1. [Overview](#overview)
2. [Testing Framework](#testing-framework)
3. [WCAG 2.1 AA Requirements](#wcag-21-aa-requirements)
4. [Implementation Guidelines](#implementation-guidelines)
5. [Testing Procedures](#testing-procedures)
6. [Common Issues and Solutions](#common-issues-and-solutions)
7. [Accessibility Checklist](#accessibility-checklist)

## Overview

Our portfolio website is designed to be fully accessible to users with disabilities, meeting WCAG 2.1 AA standards. This includes:

- **Perceivable**: Information must be presentable in ways users can perceive
- **Operable**: Interface components must be operable by all users
- **Understandable**: Information and UI operation must be understandable
- **Robust**: Content must be robust enough for various assistive technologies

## Testing Framework

### Automated Testing Tools

- **axe-core**: Primary accessibility testing engine
- **@axe-core/playwright**: Integration for browser testing
- **Jest**: Test runner for accessibility test suites
- **Puppeteer**: Browser automation for comprehensive testing

### Test Commands

```bash
# Run all accessibility tests
npm run test:a11y

# Run accessibility tests in watch mode
npm run test:a11y:watch

# Run accessibility tests with coverage
npm run test:a11y:coverage

# Run axe-core CLI tool
npm run axe:cli

# Generate CI/CD accessibility report
npm run axe:ci
```

## WCAG 2.1 AA Requirements

### Level A Requirements

1. **Keyboard Access**: All functionality available via keyboard
2. **No Keyboard Trap**: Users can navigate away from any component
3. **Timing Adjustable**: Users can extend time limits
4. **Pause, Stop, Hide**: Users can control moving content
5. **No Seizures**: No content flashes more than 3 times per second
6. **Skip Blocks**: Skip navigation mechanism available
7. **Page Titled**: Each page has a descriptive title
8. **Focus Order**: Logical focus order maintained
9. **Link Purpose**: Link purpose clear from context
10. **Language of Page**: Page language programmatically determined

### Level AA Requirements (Additional)

1. **Captions**: Captions for live audio content
2. **Audio Description**: Audio description for video content
3. **Color Contrast**: 4.5:1 ratio for normal text, 3:1 for large text
4. **Resize Text**: Text can be resized to 200% without loss of functionality
5. **Images of Text**: Avoid images of text when possible
6. **Multiple Ways**: Multiple ways to locate pages
7. **Headings and Labels**: Descriptive headings and labels
8. **Focus Visible**: Keyboard focus is visible
9. **Language of Parts**: Language of content parts identified
10. **On Input**: Changes of context only occur on user request

## Implementation Guidelines

### HTML Structure

```html
<!-- Proper semantic structure -->
<nav role="navigation" aria-label="Main navigation">
  <!-- Navigation content -->
</nav>

<main role="main" id="main-content">
  <!-- Main content -->
</main>

<footer role="contentinfo">
  <!-- Footer content -->
</footer>
```

### Skip Navigation

```html
<!-- Skip links at the beginning of page -->
<a href="#main-content" class="skip-link">Skip to main content</a>
<a href="#navigation" class="skip-link">Skip to navigation</a>
```

### Form Accessibility

```html
<!-- Proper form labeling -->
<label for="email">Email Address *</label>
<input type="email" id="email" name="email" required
       aria-describedby="email-help"
       autocomplete="email">
<div id="email-help">We'll never share your email</div>

<!-- Form grouping -->
<form role="form" aria-label="Contact form">
  <!-- Form fields -->
  <button type="submit" aria-describedby="submit-help">
    Send Message
  </button>
</form>
```

### ARIA Labels and Roles

```html
<!-- Interactive elements -->
<button aria-label="Close dialog" aria-expanded="false">
  <svg aria-hidden="true"><!-- Icon --></svg>
</button>

<!-- Live regions -->
<div aria-live="polite" aria-atomic="true">
  <!-- Dynamic content -->
</div>

<!-- Landmarks -->
<section aria-labelledby="services-heading">
  <h2 id="services-heading">Our Services</h2>
</section>
```

### Focus Management

```css
/* Visible focus indicators */
:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
  transition: outline-color 0.15s ease-in-out;
}

/* Enhanced focus for interactive elements */
.btn:focus-visible {
  box-shadow: 0 0 0 4px rgba(var(--primary-500-rgb), 0.2);
  outline: 2px solid var(--primary-500);
}
```

### Color Contrast

- **Normal text**: Minimum 4.5:1 contrast ratio
- **Large text**: Minimum 3:1 contrast ratio
- **UI components**: Minimum 3:1 contrast ratio
- **Focus indicators**: Must be visible against all backgrounds

### Responsive Design

```css
/* Minimum touch target size */
.btn {
  min-height: 44px;
  min-width: 44px;
  padding: 0.75rem 1rem;
}

/* Mobile optimizations */
@media (max-width: 640px) {
  .form-input {
    font-size: 16px; /* Prevent zoom on iOS */
    min-height: 44px;
  }
}
```

## Testing Procedures

### Manual Testing

1. **Keyboard Navigation**
   - Tab through all interactive elements
   - Ensure logical focus order
   - Test escape key functionality
   - Verify skip links work

2. **Screen Reader Testing**
   - Use NVDA (Windows) or VoiceOver (Mac)
   - Navigate by headings, landmarks, forms
   - Verify all content is announced properly

3. **Color and Contrast**
   - Test with high contrast mode
   - Verify information isn't conveyed by color alone
   - Check focus indicators are visible

4. **Zoom and Resize**
   - Test at 200% zoom
   - Ensure no horizontal scrolling
   - Verify all functionality remains available

### Automated Testing

```javascript
// Example accessibility test
test('should have no accessibility violations', async () => {
  const results = await checkA11y(page, null, {
    rules: {
      'color-contrast': { enabled: true },
      'keyboard-navigation': { enabled: true },
      'aria-label': { enabled: true }
    },
    tags: ['wcag2a', 'wcag2aa', 'wcag21aa']
  });

  expect(results.violations).toHaveLength(0);
});
```

## Common Issues and Solutions

### Issue: Missing Alt Text
**Problem**: Images without alt attributes
**Solution**:
```html
<!-- Decorative images -->
<img src="decoration.jpg" alt="" aria-hidden="true">

<!-- Informative images -->
<img src="chart.jpg" alt="Sales increased 25% from 2023 to 2024">
```

### Issue: Insufficient Color Contrast
**Problem**: Text doesn't meet 4.5:1 ratio
**Solution**: Use color palette with verified contrast ratios

### Issue: Missing Form Labels
**Problem**: Form inputs without associated labels
**Solution**:
```html
<label for="username">Username</label>
<input type="text" id="username" name="username">
```

### Issue: Keyboard Trap
**Problem**: Users can't navigate away from component
**Solution**: Implement proper focus management and escape key handling

### Issue: Missing Skip Links
**Problem**: No way to skip repetitive navigation
**Solution**:
```html
<a href="#main-content" class="skip-link">Skip to main content</a>
```

## Accessibility Checklist

### Pre-Development
- [ ] Review design for accessibility considerations
- [ ] Plan keyboard navigation flow
- [ ] Verify color contrast ratios
- [ ] Design focus indicators

### During Development
- [ ] Use semantic HTML elements
- [ ] Add proper ARIA labels and roles
- [ ] Implement keyboard navigation
- [ ] Test with automated tools

### Pre-Release
- [ ] Run full accessibility test suite
- [ ] Manual keyboard testing
- [ ] Screen reader testing
- [ ] Color contrast verification
- [ ] Mobile accessibility testing

### Maintenance
- [ ] Regular accessibility audits
- [ ] Monitor for regressions
- [ ] Update tests for new features
- [ ] User feedback incorporation

## Browser and Assistive Technology Support

### Supported Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Supported Assistive Technologies
- NVDA (Windows)
- JAWS (Windows)
- VoiceOver (macOS/iOS)
- TalkBack (Android)
- Dragon NaturallySpeaking

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [axe-core Documentation](https://github.com/dequelabs/axe-core)
- [WebAIM Resources](https://webaim.org/)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)

## Contact

For accessibility questions or to report issues, please contact the development team or create an issue in the project repository.
