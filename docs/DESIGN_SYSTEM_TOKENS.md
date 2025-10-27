# Design System Tokens Documentation

**Living Documentation - Last Updated:** December 2024
**Version:** 2.0
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Color Tokens](#color-tokens)
3. [Typography Tokens](#typography-tokens)
4. [Spacing Tokens](#spacing-tokens)
5. [Shadow Tokens](#shadow-tokens)
6. [Animation Tokens](#animation-tokens)
7. [Usage Guidelines](#usage-guidelines)
8. [Integration with Components](#integration-with-components)

---

## Overview

This document serves as the **single source of truth** for all design tokens used across the portfolio site. Design tokens are the visual design atoms of the design system — specifically, they are named entities that store visual design attributes.

### Design Token Philosophy

- **Consistency:** Tokens ensure visual consistency across all components
- **Maintainability:** Central token definitions make updates easier
- **Scalability:** Token-based system scales with project growth
- **Accessibility:** All tokens meet WCAG AA compliance standards

### Token Structure

All tokens follow a hierarchical naming convention:
```
--{category}-{property}-{variant}-{state}
```

**Example:** `--color-primary-400` or `--space-md`

---

## Color Tokens

### Primary Color Palette

Our primary color system is based on a **WCAG AA compliant** golden/warm palette that creates premium brand identity.

#### Primary Scale (10 shades)

| Token | Value | Hex Code | Use Case | WCAG Contrast |
|-------|-------|----------|----------|---------------|
| `--color-primary-50` | `#fefdf8` | Very Light Cream | Subtle backgrounds | AAA on dark |
| `--color-primary-100` | `#fdf9ed` | Light Cream | Light backgrounds | AAA on dark |
| `--color-primary-200` | `#f9f1d4` | Soft Gold | Hover states on light | AA on dark |
| `--color-primary-300` | `#f4e6a4` | Pale Gold | Disabled states | AA on dark |
| `--color-primary-400` | `#e6c547` | Medium Gold | **Primary Brand Color** | AAA on dark |
| `--color-primary-500` | `#c8b560` | Dark Gold | Active states | AAA on dark |
| `--color-primary-600` | `#a89550` | Deep Gold | Headings, emphasis | AAA on dark |
| `--color-primary-700` | `#8b7355` | Bronze | Strong emphasis | AAA on light |
| `--color-primary-800` | `#6b705c` | Dark Bronze | Text on light | AAA on light |
| `--color-primary-900` | `#4a4e3a` | Deep Bronze | Dark text | AAA on light |

**Key Primary Colors:**
```css
--color-primary: var(--color-primary-400);      /* Main brand color */
--color-primary-dark: var(--color-primary-600); /* Dark variant */
--color-primary-light: var(--color-primary-200); /* Light variant */
```

### Secondary Color Palette

Secondary colors support the primary palette with neutral grays.

| Token | Value | Hex Code | Use Case |
|-------|-------|----------|----------|
| `--color-secondary-50` | `#fafaf9` | Lightest Gray | Backgrounds |
| `--color-secondary-100` | `#f5f5f4` | Very Light Gray | Subtle backgrounds |
| `--color-secondary-200` | `#e7e5e4` | Light Gray | Borders, dividers |
| `--color-secondary-300` | `#d6d3d1` | Medium Light Gray | Disabled backgrounds |
| `--color-secondary-400` | `#a8a29e` | Medium Gray | Placeholder text |
| `--color-secondary-500` | `#78716c` | Gray | Secondary text |
| `--color-secondary-600` | `#57534e` | Dark Gray | Body text |
| `--color-secondary-700` | `#44403c` | Darker Gray | Headings |
| `--color-secondary-800` | `#292524` | Very Dark Gray | Dark mode backgrounds |
| `--color-secondary-900` | `#1c1917` | Darkest Gray | Dark mode surfaces |

### Semantic Color Tokens

Semantic colors communicate meaning and state.

#### Success
```css
--color-success: #10b981;        /* Green - Success states */
--color-success-light: #d1fae5;  /* Light success background */
--color-success-dark: #047857;   /* Dark success variant */
```

#### Warning
```css
--color-warning: #f59e0b;        /* Amber - Warning states */
--color-warning-light: #fef3c7;  /* Light warning background */
--color-warning-dark: #d97706;   /* Dark warning variant */
```

#### Error
```css
--color-error: #ef4444;          /* Red - Error states */
--color-error-light: #fee2e2;    /* Light error background */
--color-error-dark: #dc2626;     /* Dark error variant */
```

#### Info
```css
--color-info: #3b82f6;           /* Blue - Informational states */
--color-info-light: #dbeafe;     /* Light info background */
--color-info-dark: #2563eb;      /* Dark info variant */
```

### Functional Color Tokens

#### Text Colors
```css
--color-text-primary: #1c1917;       /* Primary text (dark) */
--color-text-secondary: #57534e;     /* Secondary text */
--color-text-tertiary: #78716c;      /* Tertiary text */
--color-text-disabled: #a8a29e;      /* Disabled text */
--color-text-inverse: #fafaf9;       /* Text on dark backgrounds */
--color-text-premium: #e6c547;       /* Premium accent text */
--color-text-premium-accent: #c8b560; /* Premium headings */
```

#### Background Colors
```css
--color-bg-primary: #0a0a0a;         /* Main dark background */
--color-bg-secondary: #1a1a1a;       /* Secondary dark surface */
--color-bg-tertiary: #2a2a2a;        /* Tertiary surface */
--color-bg-elevated: #1e1e1e;        /* Elevated surfaces (cards) */
--color-bg-overlay: rgba(0,0,0,0.7); /* Overlay backgrounds */
```

#### Border Colors
```css
--color-border-primary: rgba(230, 197, 71, 0.2);   /* Primary borders */
--color-border-secondary: rgba(255, 255, 255, 0.1); /* Subtle borders */
--color-border-focus: rgba(230, 197, 71, 0.6);     /* Focus rings */
```

---

## Typography Tokens

### Font Families

```css
--font-sans: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
--font-mono: "JetBrains Mono", "Consolas", "Monaco", monospace;
--font-display: var(--font-sans); /* Display/Heading font */
--font-body: var(--font-sans);    /* Body text font */
```

### Font Sizes

Our type scale follows a modular scale for consistent visual hierarchy.

| Token | Value | rem | px (16px base) | Use Case |
|-------|-------|-----|----------------|----------|
| `--font-size-xs` | 0.75rem | 0.75 | 12px | Overlines, tiny labels |
| `--font-size-sm` | 0.875rem | 0.875 | 14px | Captions, small text |
| `--font-size-base` | 1rem | 1 | 16px | **Base body text** |
| `--font-size-lg` | 1.125rem | 1.125 | 18px | Large body text |
| `--font-size-xl` | 1.25rem | 1.25 | 20px | Extra large text |
| `--font-size-2xl` | 1.5rem | 1.5 | 24px | Display large |
| `--font-size-3xl` | 1.875rem | 1.875 | 30px | Display XL |
| `--font-size-4xl` | 2.25rem | 2.25 | 36px | Display 2XL |

### Font Weights

```css
--font-weight-normal: 400;   /* Regular text */
--font-weight-medium: 500;   /* Medium emphasis */
--font-weight-semibold: 600; /* Semi-bold emphasis */
--font-weight-bold: 700;     /* Bold emphasis */
--font-weight-extrabold: 800; /* Extra bold (displays) */
```

### Line Heights

```css
--line-height-tight: 1.25;   /* Headings */
--line-height-snug: 1.375;   /* Sub-headings */
--line-height-normal: 1.5;   /* Body text */
--line-height-relaxed: 1.625; /* Comfortable reading */
--line-height-loose: 2;      /* Spacious text */
```

### Letter Spacing

```css
--letter-spacing-tight: -0.025em;  /* Tight tracking */
--letter-spacing-normal: 0;        /* Normal tracking */
--letter-spacing-wide: 0.025em;    /* Wide tracking */
--letter-spacing-wider: 0.05em;    /* Wider tracking */
--letter-spacing-widest: 0.1em;    /* Widest (overlines) */
```

### Typography Utility Classes

Pre-defined classes combining size, weight, and line-height:

```css
.text-display-2xl   /* 36px, 800 weight, 1.25 line-height */
.text-display-xl    /* 30px, 700 weight, 1.25 line-height */
.text-display-lg    /* 24px, 600 weight, 1.375 line-height */
.text-body-xl       /* 20px, 400 weight, 1.625 line-height */
.text-body-lg       /* 18px, 400 weight, 1.625 line-height */
.text-body          /* 16px, 400 weight, 1.5 line-height */
.text-caption       /* 14px, 500 weight, 1.5 line-height */
.text-overline      /* 12px, 600 weight, 1.5 line-height, uppercase */
```

---

## Spacing Tokens

Our spacing system follows a **base-8 approach** for consistent and harmonious layouts.

### Base Spacing Scale

| Token | Value | rem | px (16px base) | Use Case |
|-------|-------|-----|----------------|----------|
| `--space-0` | 0 | 0 | 0px | No spacing |
| `--space-1` | 0.25rem | 0.25 | 4px | Tiny spacing |
| `--space-2` | 0.5rem | 0.5 | 8px | **Base unit** |
| `--space-3` | 0.75rem | 0.75 | 12px | Small spacing |
| `--space-4` | 1rem | 1 | 16px | Medium small |
| `--space-5` | 1.25rem | 1.25 | 20px | Medium |
| `--space-6` | 1.5rem | 1.5 | 24px | Medium large |
| `--space-8` | 2rem | 2 | 32px | Large |
| `--space-10` | 2.5rem | 2.5 | 40px | Extra large |
| `--space-12` | 3rem | 3 | 48px | 2XL |
| `--space-16` | 4rem | 4 | 64px | 3XL |
| `--space-20` | 5rem | 5 | 80px | 4XL |
| `--space-24` | 6rem | 6 | 96px | 5XL |
| `--space-32` | 8rem | 8 | 128px | 6XL |

### Semantic Spacing

```css
--spacing-xs: var(--space-2);   /* 8px - Minimal spacing */
--spacing-sm: var(--space-4);   /* 16px - Small spacing */
--spacing-md: var(--space-6);   /* 24px - Medium spacing */
--spacing-lg: var(--space-8);   /* 32px - Large spacing */
--spacing-xl: var(--space-12);  /* 48px - XL spacing */
--spacing-2xl: var(--space-16); /* 64px - 2XL spacing */
```

### Component-Specific Spacing

```css
--spacing-card-padding: var(--space-6);     /* Card internal padding */
--spacing-section-gap: var(--space-16);     /* Between sections */
--spacing-component-gap: var(--space-4);    /* Between components */
--spacing-inline-gap: var(--space-2);       /* Inline elements */
```

---

## Shadow Tokens

Shadows create depth and visual hierarchy.

### Elevation Shadows

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

### Glow Effects (Premium)

```css
--shadow-glow-primary: 0 0 20px rgba(230, 197, 71, 0.3);
--shadow-glow-success: 0 0 20px rgba(16, 185, 129, 0.3);
--shadow-glow-error: 0 0 20px rgba(239, 68, 68, 0.3);
--shadow-glow-premium: 0 0 40px rgba(230, 197, 71, 0.5);
```

### Inner Shadows

```css
--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);
--shadow-inner-premium: inset 0 2px 4px 0 rgba(230, 197, 71, 0.1);
```

---

## Animation Tokens

### Duration

```css
--duration-instant: 100ms;   /* Instant feedback */
--duration-fast: 200ms;      /* Fast transitions */
--duration-normal: 300ms;    /* Default transitions */
--duration-slow: 500ms;      /* Slow transitions */
--duration-slower: 700ms;    /* Very slow transitions */
```

### Easing Functions

```css
--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
--ease-premium: cubic-bezier(0.34, 1.56, 0.64, 1); /* Custom premium easing */
```

### Animation Presets

```css
--transition-fast: all var(--duration-fast) var(--ease-out);
--transition-normal: all var(--duration-normal) var(--ease-in-out);
--transition-slow: all var(--duration-slow) var(--ease-in-out);
--transition-colors: color var(--duration-normal) var(--ease-in-out),
                     background-color var(--duration-normal) var(--ease-in-out),
                     border-color var(--duration-normal) var(--ease-in-out);
```

---

## Usage Guidelines

### Token Application Best Practices

1. **Always Use Tokens:** Never use hardcoded values in components
   ```css
   /* ❌ Bad */
   .component {
       color: #e6c547;
       margin: 24px;
   }

   /* ✅ Good */
   .component {
       color: var(--color-primary);
       margin: var(--spacing-md);
   }
   ```

2. **Semantic Over Literal:** Use semantic tokens when available
   ```css
   /* ❌ Less ideal */
   .text {
       color: var(--color-primary-600);
   }

   /* ✅ Better */
   .text {
       color: var(--color-text-premium-accent);
   }
   ```

3. **Consistent Spacing:** Use spacing scale consistently
   ```css
   /* ✅ Good - Uses scale */
   .card {
       padding: var(--spacing-md);
       gap: var(--spacing-sm);
   }
   ```

4. **Accessibility First:** Always ensure color contrast meets WCAG standards
   ```css
   /* ✅ Always test contrast */
   .text-on-dark {
       color: var(--color-text-inverse); /* Verified AAA contrast */
       background: var(--color-bg-primary);
   }
   ```

### Component Token Overrides

Components can define local token overrides:

```css
.custom-card {
    --card-bg: var(--color-bg-elevated);
    --card-border: var(--color-border-primary);
    --card-padding: var(--spacing-lg);

    background: var(--card-bg);
    border: 1px solid var(--card-border);
    padding: var(--card-padding);
}
```

---

## Integration with Components

### Component-Token Mapping

| Component | Primary Tokens Used |
|-----------|-------------------|
| **ProjectCard** | `--color-primary`, `--spacing-md`, `--shadow-lg` |
| **SectionHeader** | `--color-text-premium-accent`, `--font-size-2xl`, `--spacing-lg` |
| **StatCard** | `--color-success`, `--color-warning`, `--spacing-sm` |
| **EmptyState** | `--color-text-secondary`, `--font-size-xl`, `--spacing-2xl` |
| **GridContainer** | `--spacing-md`, `--spacing-component-gap` |
| **Buttons** | `--color-primary`, `--transition-normal`, `--shadow-md` |
| **Forms** | `--color-border-primary`, `--spacing-sm`, `--transition-fast` |
| **Cards** | `--color-bg-elevated`, `--shadow-xl`, `--spacing-card-padding` |

### Token Usage Examples

#### Button Component
```css
.btn-primary {
    background: var(--color-primary);
    color: var(--color-text-inverse);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    transition: var(--transition-normal);
    box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
    background: var(--color-primary-dark);
    box-shadow: var(--shadow-md);
}
```

#### Card Component
```css
.glass-card {
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border-secondary);
    padding: var(--spacing-card-padding);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-xl);
    transition: var(--transition-normal);
}
```

---

## Design Token Updates

### Update Process

1. **Propose Change:** Document token change in design team meeting
2. **Impact Analysis:** Identify all components using the token
3. **Update Token:** Modify value in `static/css/consolidated.css`
4. **Test Components:** Verify all components render correctly
5. **Update Documentation:** Reflect changes in this document
6. **Version Bump:** Increment design system version

### Token Deprecation

When deprecating tokens:

1. Mark as deprecated with comment
2. Provide migration path
3. Set deprecation timeline (minimum 2 releases)
4. Update all references
5. Remove in scheduled release

---

## References

- **Main Stylesheet:** `static/css/consolidated.css`
- **Component Library:** `templates/components/`
- **UI Kit Showcase:** `templates/pages/portfolio/ui-kit.html`
- **Fixtures Provider:** `apps/portfolio/fixtures_provider.py`
- **Portfolio Components:** `templates/components/portfolio/` (5 reusable components)

### UI Kit Integration

The **Living Documentation UI Kit** at `/ui-kit/` provides interactive examples of all design tokens and portfolio components:

#### Showcased Components
1. **Project Card** - Featured and compact modes with status indicators
2. **Section Header** - Configurable headers with 5 icon types
3. **Statistics Card** - Metrics display with trend indicators
4. **Empty State** - Fallback UI for no-content scenarios
5. **Grid Container** - Responsive grid layout wrapper

#### Data Flow
- **Fixtures Provider** (`fixtures_provider.py`) generates realistic sample data
- **UI Kit View** populates context with fixtures and tokens summary
- **Templates** render interactive examples with live design token values
- **Design Tokens Reference** displays current token metadata

#### Maintenance
- Token changes automatically reflect in UI Kit via CSS variables
- Portfolio components auto-update with new design tokens
- Fixtures provider ensures consistent test data across UI Kit

---

**Maintained by:** Design Team
**Contact:** For questions or suggestions, contact the design system team
**Last Review:** December 2024
