# MSW & Playwright Reference

## MSW (Mock Service Worker) Setup

### File Structure

| File | Role |
|------|------|
| `mocks/handlers.ts` | Shared API mock handler definitions |
| `mocks/server.ts` | MSW server for Vitest (`setupServer`) |
| `vitest.setup.ts` | MSW server start/reset/teardown around tests |

### Handler Override in Tests

```typescript
import { server } from '@/mocks/server'
import { http, HttpResponse } from 'msw'

it('handles API error', async () => {
  server.use(
    http.get('/api/v1/members/me', () =>
      HttpResponse.json(
        { success: false, error: { code: 'UNAUTHORIZED', message: 'Auth failed' } },
        { status: 401 },
      ),
    ),
  )
  // ... test code
})
```

- Define common success responses in `mocks/handlers.ts`, override per-test with `server.use()`
- `afterEach(() => server.resetHandlers())` automatically resets overrides

### Adding New API Handlers

```typescript
// mocks/handlers.ts
export const handlers = [
  http.get('/api/v1/new-endpoint', () => {
    return HttpResponse.json({ success: true, data: { /* ... */ } })
  }),
]
```

---

## Playwright E2E

### Tool Roles

| Tool | Role | When to Use |
|------|------|-------------|
| `playwright-cli` | Browser interaction + test code auto-generation + debugging | During development |
| `pnpm exec playwright test` | Automated `.test.ts` execution (pass/fail) | CI, pre-push hooks |

### playwright-cli Key Commands

```bash
playwright-cli open <url>        # Open browser
playwright-cli snapshot          # DOM structure + element refs
playwright-cli click <ref>       # Click element (→ auto-generates code)
playwright-cli fill <ref> "text" # Fill input (→ auto-generates code)
playwright-cli screenshot        # Capture screenshot
playwright-cli console           # View console logs
playwright-cli run-code "..."    # Run Playwright code directly
playwright-cli close             # Close browser
```

### E2E Workflow

```
playwright-cli explore & interact → use auto-generated code for test files → pnpm exec playwright test for CI
```

| Phase | Tool | Purpose |
|-------|------|---------|
| Explore + Code gen | `playwright-cli` | Interact with page, auto-generate Playwright code |
| Write test file | `.test.ts` file | Combine generated code + assertions |
| CI execution | `pnpm exec playwright test` | Automated pass/fail (CI, hooks) |
| Debugging | `playwright-cli` | Diagnose failures, screenshots, console |

### CI Commands

```bash
pnpm exec playwright test tests/e2e/<name>.test.ts           # Single file
pnpm exec playwright test tests/e2e/<name>.test.ts --headed   # Headed mode
pnpm exec playwright test tests/e2e/<name>.test.ts -g "name"  # Specific test
pnpm test                                                      # All E2E
```

---

## Command Reference (Quick)

```bash
# Unit/Integration
pnpm exec vitest run <path>
pnpm test:unit

# E2E — Explore/Debug
playwright-cli open <url>
playwright-cli snapshot

# E2E — CI execution
pnpm exec playwright test <path>
pnpm test
```
