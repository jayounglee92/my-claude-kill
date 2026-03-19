# Completion Checklists

Detailed checklists referenced from STEP 8.

## Accessibility (a11y) Checklist

Run when user selects a11y in STEP 8 optional items.

### Automated Check

```bash
pnpm exec axe-core <url>   # or browser Lighthouse
```

### Manual Verification

| Item | Verification |
|------|-------------|
| Keyboard-only operation | All features usable via Tab → Enter/Space → Escape |
| Focus indicator | Focus state is visually clear |
| Screen reader | ARIA labels read meaningfully |
| Error announcement | Errors conveyed via `role="alert"` or `aria-live="polite"` |
| Color contrast | Meets WCAG AA (4.5:1 ratio) |

---

## Responsive Checklist (MANDATORY)

Run for **every feature** — this is not optional.

| Breakpoint | Verification |
|------------|-------------|
| Mobile (< 640px) | No layout breakage, touch targets ≥ 44px |
| Tablet (640-1024px) | Sidebar/grid transitions are smooth |
| Desktop (> 1024px) | Content doesn't stretch too wide (check max-width) |

> Every feature must pass all three breakpoints before completion.
