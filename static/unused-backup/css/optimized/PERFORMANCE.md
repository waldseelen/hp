# CSS Bundle Optimization Guide

## Bundle Strategy

### 1. Critical CSS (Inline)
- Above-the-fold styles
- Navigation and layout
- Base typography
- **Load:** Inline in <head>

### 2. Main CSS Bundle
- Core component styles
- Accessibility features
- Form styles
- **Load:** High priority with preload

### 3. Enhanced CSS Bundle
- Animations and transitions
- Advanced components
- **Load:** After main content

### 4. Tailwind CSS Bundle
- Utility classes
- Framework styles
- **Load:** Asynchronously after page load

## Implementation

### Django Settings

Add to your base template:
```html
{% include 'partials/optimized-css.html' %}
```

### Performance Metrics

Monitor these metrics:
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Cumulative Layout Shift (CLS)
- Time to Interactive (TTI)

### Build Commands

Development:
```bash
npm run dev
```

Production:
```bash
npm run build:production
```

## Best Practices

1. **Critical CSS**: Keep under 14KB for optimal performance
2. **Bundle splitting**: Separate critical from non-critical styles
3. **Loading strategy**: Use preload for important resources
4. **Caching**: Set appropriate cache headers for bundles
5. **Monitoring**: Track bundle sizes and loading times

## Bundle Sizes

Check current bundle sizes in manifest.json