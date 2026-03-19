---
name: fe-sdd-tdd
description: "Use when implementing any frontend feature or bugfix - auto-discovers the spec directory, reads the spec first, then follows Testing Trophy: unit tests drive TDD cycle, integration tests as main layer, E2E for key user flows. If no spec exists, interactively generates one by combining user interview questions with codebase analysis. Also use when the user says spec, 기능 구현, TDD, 테스트 먼저, 스펙 작성, or mentions a feature ID like EVT-021."
---

# Frontend Spec-Driven Development + Test-Driven Development

## Overview

**Spec first. Tests first. Implementation last.**

Based on Kent C. Dodds' **Testing Trophy**. Test strategy is determined by **confidence-to-cost ratio**, not volume.

- **Spec-Driven Development** — Always locate and read the project's spec directory before implementing. If no spec exists, **generate one** through user interview + codebase analysis.
- **Test-Driven Development** — Write tests before implementation code.
- **Testing Trophy** — Integration tests are the widest layer, unit tests drive the TDD cycle, E2E tests cover only critical user flows.

```
        /\
       /E2E\          ← Critical flows only (few)
      /------\
     /Integration\    ← Widest layer (many)
    /------------\
   / Unit Tests   \   ← TDD cycle driver
  /----------------\
 / Static Analysis  \  ← Always running (TS)
/--------------------\
```

**The Iron Law:**
```
No implementation code without a spec. No implementation code without a failing test.
```

---

## Language Rule

This skill is written in English. However, **all user-facing communication must match the user's language**.

- Detect the user's language from their first message
- Questions, options, status updates, explanations → user's language
- Spec documents (STEP 0-4) → user's language
- Code (variable names, test descriptions) → English
- UI text in code (button labels, error messages) → user's language if project targets that locale

---

## References

This skill uses bundled reference files. Read them **when you reach the relevant step**, not upfront.

| File | When to Read |
|------|-------------|
| `references/spec-template.md` | STEP 0-4: generating a spec draft |
| `references/test-examples.md` | STEP 2 & 4: writing unit or integration tests |
| `references/msw-and-playwright.md` | STEP 4: MSW setup, STEP 6: E2E with Playwright |
| `references/checklists.md` | STEP 8: a11y and responsive verification |

---

## The Master Flow

```
STEP 0-0: Discover spec directory (SPEC_DIR)
  │
  ├─ Auto-scan project for spec location
  ├─ If not found → ask user for spec directory path
  └─ Cache result for the session
        │
        ▼
Spec exists in SPEC_DIR?
  │
  ├─ YES → STEP 1 (Read Spec) → STEP 2 (Unit Test RED)
  │
  └─ NO → STEP 0: Spec Generation Mode
           ├─ 0-1. Confirm no spec exists
           ├─ 0-2. User interview (core questions)
           ├─ 0-3. Codebase analysis (parallel)
           ├─ 0-4. Generate spec draft (→ read references/spec-template.md)
           ├─ 0-5. User confirmation / revision loop
           └─ Confirmed → STEP 2
```

---

## STEP 0: Spec Generation Mode

### 0-0. Spec Directory Discovery

**Run ONCE per session.** Discovered path = `SPEC_DIR`.

```bash
for dir in docs/specs specs docs/requirements docs/features .specs requirements docs; do
  [ -d "$dir" ] && echo "SPEC_DIR=$dir" && break
done
find . -maxdepth 3 -type f -name "*.md" | xargs grep -l "## User Flows\|## API Integration" 2>/dev/null | head -5
grep -r "specDir\|spec_dir\|specsPath" package.json .sddrc 2>/dev/null
```

| Priority | Method |
|----------|--------|
| 1 | Directory found by auto-scan |
| 2 | Spec-like files → derive parent dir |
| 3 | Config file hint |
| 4 | **Ask user** (fallback) |

### 0-1. Check Spec Existence

```bash
ls $SPEC_DIR/
```

If no spec found → enter generation mode.

### 0-2. User Interview

**Identify feature type first**, then ask questions accordingly.

| Type | Examples |
|------|----------|
| New Page | Signup, dashboard |
| New Component | Comment widget, filter |
| Form / Input | Registration, profile edit |
| Data Display | List, detail, search |
| Interaction / UX | Infinite scroll, DnD |
| Bug Fix | Broken validation, layout |

**Common Questions (all types):**

| # | Question | Purpose |
|---|----------|---------|
| Q1 | What does this feature do? (one sentence) | Goal |
| Q2 | User action sequence? | User flow |
| Q3 | API endpoints? (method + path) | API |
| Q4 | What does user see on success? | Success state |
| Q5 | How to handle errors? | Error state |

**Type-specific questions:**

- **Form**: Fields needed? Required/optional? Validation rules? Validation trigger?
- **Data Display**: Pagination? Empty state? Loading UI? Sort/filter?
- **New Page**: URL path? Auth required? SEO needed?
- **Bug Fix**: Current behavior? Expected behavior? Repro steps?

### 0-3. Codebase Analysis

Run **in parallel** with interview. Present results as a table.

```bash
find src/ app/ -maxdepth 2 -type f \( -name "*.ts" -o -name "*.tsx" \) 2>/dev/null | sort
grep -ri "KEYWORD" src/ --include="*.tsx" --include="*.ts" -l 2>/dev/null
find src/app/api app/api pages/api -type f 2>/dev/null | sort
grep -E "tanstack|zustand|recoil|jotai|redux|swr" package.json
grep -E "radix|shadcn|headlessui|antd|mui|chakra" package.json
find __tests__/ tests/ -type f -name "*.test.*" 2>/dev/null | head -10
ls src/components/ui/ 2>/dev/null
grep -rl "useAuth\|useSession\|useUser" src/ 2>/dev/null
```

### 0-4. Generate Spec Draft

→ **Read `references/spec-template.md`** for the full template and tips.

Combine user answers + codebase analysis. Save to `SPEC_DIR/[FEATURE-ID].md`.

### 0-5. User Confirmation

Present draft → user chooses: **Confirm** / **Revise** / **Start over**.

**Revision rules:**
- New feature added → ask follow-up questions, update entire spec
- Simple edit → apply immediately
- Always re-confirm after revision

---

## STEP 1: Read the Spec

**MANDATORY. Never skip.**

Check for: user flows, inputs/outputs, edge cases (error/empty/loading), validation rules.

**Do not implement behavior not in the spec.**

---

## STEP 2: Unit Test RED

Break spec behavior into smallest testable units. Write tests first.

→ For code examples, **read `references/test-examples.md`**.

```bash
pnpm exec vitest run __tests__/components/<ComponentName>.test.tsx
```

Verify: test fails due to **missing functionality**, not config/type errors.

---

## STEP 3: GREEN — Minimal Implementation

Write minimum code to pass the test. YAGNI — stay within spec scope.

**Sub-skills to apply:**

| Target | Skill |
|--------|-------|
| Next.js patterns | `next-best-practices` |
| React performance | `vercel-react-best-practices` |
| Component design | `building-components` |
| Composition patterns | `vercel-composition-patterns` |
| Accessibility, responsive | `web-design-guidelines` |

---

## STEP 4: Integration Tests — The Core Layer

Verify component works with real API, routing, and state. **Write more of these than unit tests.**

→ For code examples + MSW setup, **read `references/test-examples.md`** and **`references/msw-and-playwright.md`**.

---

## STEP 5: REFACTOR

| # | Check | Action |
|---|-------|--------|
| 1 | Side effects during render? | Extract to `useEffect` / custom hook |
| 2 | Inline API logic? | Extract to custom hook |
| 3 | Duplicate types? | Consolidate to `types/` |
| 4 | Component > 100 lines? | Separate UI from logic |
| 5 | Tests still pass? | Must pass without changes |

```bash
pnpm test:unit
```

---

## STEP 6: E2E — Critical Flows Only

Only the **1-2 most critical** user scenarios. If integration tests cover it, skip E2E.

→ For Playwright workflow and commands, **read `references/msw-and-playwright.md`**.

---

## STEP 7: Decision Points — STOP & ASK

### Auto-scan for unresolved items:

```bash
grep -rn "TODO\|FIXME\|HACK\|XXX" src/ --include="*.ts" --include="*.tsx"
```

### Triggers:

| Trigger | Action |
|---------|--------|
| UX decision not in spec | Present A/B/C options |
| API differs from spec | Report mismatch, user decides |
| Performance tradeoff | Present pros/cons |
| a11y decision | Present WAI-ARIA options |
| Reuse vs new component | Compare constraints |
| Library choice | Comparison table |
| Unimplemented spec feature (TODO) | Implement now vs defer |

### Format:

```
🔀 Decision needed.
**Situation**: [describe]
**Options**: A) ... B) ... C) ...
**Recommendation**: [pick + reason]
```

Record decision in spec, then continue.

---

## STEP 8: Completion Checklist

### Mandatory (always run)

| Item | Tasks |
|------|-------|
| **Responsive** | Verify all 3 breakpoints (mobile / tablet / desktop). Touch targets ≥ 44px. → **Read `references/checklists.md`** |

### Optional (ask user)

| Item | Default |
|------|---------|
| Accessibility (a11y) | Y if form/interaction → **Read `references/checklists.md`** |
| i18n | Per project setting |
| Storybook | Y if shared component |
| Documentation | N |
| Error monitoring | Y if payment/auth |

---

## Test Strategy Auto-Recommendation

| Complexity | Examples | Distribution |
|------------|----------|-------------|
| **Low** | Style fix, text change | Unit 2-3 |
| **Medium** | Form + API, filter | Unit 3-5 + Integration 2-3 |
| **High** | Multi-step, payment, auth | Unit 5+ + Integration 3-5 + E2E 1-2 |

---

## Spec vs Implementation Mismatch

1. Describe the mismatch clearly
2. User chooses: A) Update spec, or B) Change implementation
3. Update spec file, then continue

---

## Red Flags — STOP

- Writing code before reading the spec
- Implementing without tests
- Not verifying test fails first
- Adding behavior outside spec
- "I'll add tests later"
- "Let me write E2E too" (when integration suffices)
- "Spec is vague, I'll guess" → **Return to Spec Generation**
- "No spec, let me just build" → **Return to STEP 0**

**If any apply: stop and restart from SPEC.**

---

## Checklist

- [ ] Discover spec directory (STEP 0-0)
- [ ] Check `SPEC_DIR/` for existing spec
- [ ] If no spec: STEP 0 (interview + codebase + spec generation)
- [ ] If spec exists: read and verify completeness
- [ ] Spec confirmed by user
- [ ] Unit tests written and failing (RED)
- [ ] Minimal implementation passes tests (GREEN)
- [ ] Integration tests with MSW passing
- [ ] Refactor: hooks extracted, duplication removed, tests green
- [ ] TODO/FIXME scan — report unresolved items
- [ ] E2E for critical flows (if High complexity)
- [ ] All STOP & ASK decision points handled
- [ ] Responsive verified at all breakpoints (MANDATORY)
- [ ] Optional checklist confirmed with user
- [ ] No code outside spec scope
