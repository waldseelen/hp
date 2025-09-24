# Accessibility Guidelines - WCAG 2.1 AA Compliance

## Color Contrast Requirements

### WCAG AA Standards
- **Normal Text**: Minimum 4.5:1 contrast ratio
- **Large Text**: Minimum 3.0:1 contrast ratio (18pt+ or 14pt+ bold)
- **UI Components**: Minimum 3.0:1 contrast ratio

### Approved Color Combinations

#### Light Theme
- **Body Text**: #1a1a1a on #ffffff (15.8:1) ✅
- **Links**: #0066cc on #ffffff (7.7:1) ✅
- **Secondary Text**: #4a4a4a on #ffffff (9.7:1) ✅

#### Dark Theme
- **Body Text**: #f0f0f0 on #121212 (14.2:1) ✅
- **Links**: #66b3ff on #121212 (8.1:1) ✅
- **Secondary Text**: #d0d0d0 on #121212 (11.3:1) ✅

## Focus Management

### Focus Indicators
- **Visible Focus Ring**: 2px solid outline with 2px offset
- **High Contrast**: 3px outline in high contrast mode
- **Color**: Blue (#005fcc) for visibility
- **Never Remove**: Always maintain focus indicators

### Focus Order
1. Skip navigation link (first focusable element)
2. Main navigation
3. Page content in logical order
4. Footer navigation

## Keyboard Navigation

### Required Support
- **Tab**: Move forward through interactive elements
- **Shift+Tab**: Move backward through interactive elements
- **Enter**: Activate buttons and links
- **Space**: Activate buttons, check checkboxes
- **Arrow Keys**: Navigate within components (menus, tabs)
- **Escape**: Close modals, dropdowns

### Interactive Element Requirements
- **Minimum Size**: 44px × 44px touch target
- **Keyboard Accessible**: All interactive elements
- **Clear Focus**: Visible focus indicators
- **Logical Order**: Tab order follows visual layout

## Screen Reader Support

### Semantic HTML
- **Headings**: Proper heading hierarchy (h1 → h2 → h3)
- **Lists**: Use `<ul>`, `<ol>` for grouped items
- **Forms**: Associate labels with form controls
- **Tables**: Use `<th>` for headers with `scope` attribute

### ARIA Labels
- **aria-label**: For elements without visible text
- **aria-describedby**: For additional descriptions
- **aria-expanded**: For collapsible elements
- **aria-current**: For current page/state
- **role**: When semantic HTML isn't sufficient

### Skip Links
- **Skip to Content**: First focusable element
- **Skip Navigation**: Direct access to main content
- **Position**: Visually hidden until focused

## Responsive Design

### Mobile Accessibility
- **Touch Targets**: Minimum 44px × 44px
- **Zoom Support**: Up to 200% without horizontal scroll
- **Text Scaling**: Readable at 200% zoom
- **Orientation**: Support both portrait and landscape

### Viewport
- **Meta Tag**: `<meta name="viewport" content="width=device-width, initial-scale=1">`
- **No User Scaling Restrictions**: Allow pinch-to-zoom

## Motion and Animation

### Reduced Motion
- **Respect Preference**: `prefers-reduced-motion: reduce`
- **Essential Motion Only**: Disable decorative animations
- **Alternative Indicators**: Use static alternatives

### Safe Animations
- **No Flashing**: Avoid content that flashes more than 3 times per second
- **Subtle Transitions**: Keep animations smooth and brief
- **User Control**: Provide pause/stop controls for auto-playing content

## Color and Contrast

### Color Usage
- **Not Sole Indicator**: Don't rely only on color to convey information
- **Text Labels**: Supplement color with text or icons
- **Error States**: Use text + color for form validation

### Testing Tools
- **Browser DevTools**: Built-in contrast checkers
- **axe-core**: Automated accessibility testing
- **Color Oracle**: Color blindness simulator
- **Manual Testing**: Test with real users

## Implementation Checklist

### Every Page Must Have
- [ ] Skip navigation link
- [ ] Proper heading hierarchy
- [ ] Alt text for images
- [ ] Form labels associated with inputs
- [ ] Focus indicators on interactive elements
- [ ] WCAG AA contrast ratios
- [ ] Keyboard navigation support

### Testing Requirements
- [ ] Test with keyboard only
- [ ] Test with screen reader
- [ ] Verify focus order
- [ ] Check color contrast
- [ ] Validate HTML semantics
- [ ] Test at 200% zoom
- [ ] Verify reduced motion preference

## Emergency Color Fixes

If any color combinations fail WCAG AA:

1. **Text on Light Backgrounds**
   - Use: #1a1a1a (near black)
   - Links: #0066cc (blue)

2. **Text on Dark Backgrounds**
   - Use: #f0f0f0 (near white)
   - Links: #66b3ff (light blue)

3. **Interactive Elements**
   - Primary: #0066cc background, #ffffff text
   - Success: #0d7f3e background, #ffffff text
   - Error: #c41e3a background, #ffffff text
   - Warning: #b8860b background, #ffffff text

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Color Contrast Analyzer](https://www.tpgi.com/color-contrast-checker/)
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WebAIM Screen Reader Survey](https://webaim.org/projects/screenreadersurvey9/)