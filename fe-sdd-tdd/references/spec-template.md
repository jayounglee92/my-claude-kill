# Spec Template

Use this template when generating a spec draft in STEP 0-4. Combine user interview answers + codebase analysis results to fill in each section.

## Template

```markdown
# [FEATURE-ID] Feature Name

## Overview
<!-- Based on Q1 -->
One-line description.

## User Flows
<!-- Based on Q2 -->
1. User navigates to [page/button]
2. User [inputs/selects]
3. User [submits/confirms]
4. [Result screen] is displayed

## Screen States

### Loading State
- [ ] Skeleton UI / Spinner / Text

### Success State
<!-- Based on Q4 -->
- [ ] Data fields to display
- [ ] Success message or redirect path

### Error State
<!-- Based on Q5 -->
- [ ] Error message on API failure
- [ ] Network error handling
- [ ] Retry button

### Empty State
- [ ] UI when no data exists

## Input Fields & Validation
<!-- Based on F1-F4 (for form features) -->

| Field | Type | Required | Validation Rule | Trigger |
|-------|------|----------|----------------|---------|
| name  | text | Y        | min 1 char     | onSubmit |

## API Integration
<!-- Based on Q3 + codebase analysis -->

### Request
POST /api/events/{id}/register
Content-Type: application/json

{
  "name": string
}

### Success Response
{
  "success": true,
  "data": { ... }
}

### Error Response
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}

## Permission Matrix
<!-- Include when authorization logic is involved -->

| Action | Guest | Owner | Other User | Admin |
|--------|-------|-------|-----------|-------|
| Read   | ✅    | ✅    | ✅        | ✅    |
| Create | ❌    | ✅    | ✅        | ✅    |
| Update | ❌    | ✅    | ❌        | ❌    |
| Delete | ❌    | ✅    | ❌        | ✅    |

## Technical Context (Auto-Detected)
<!-- From codebase analysis -->
- **Reusable Components**: `components/ui/Button`, `components/Form/Input`
- **Related Types**: `types/event.ts` → `EventRegistration` interface
- **State Management**: React Query (`@tanstack/react-query`)
- **URL Path**: `/events/[id]/register`

## Out of Scope
- Explicitly list what this spec does NOT cover
```

## Tips

- Remove unnecessary sections based on feature type (e.g., "Input Fields" not needed for bug fixes)
- Always include **Permission Matrix** when authorization is involved
- Always include **success/error response schemas** when API is involved
- List reusable components detected from codebase analysis in **Technical Context**
- Write the spec in the **user's language** (see Language Rule in SKILL.md)
