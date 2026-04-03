# Trust-But-Verify: Report Phase

You are writing a verification report based on browser testing results.

## Your Inputs

**Branch:** {BRANCH_NAME}
**Plan:** {PLAN_PATH}
**PR:** {PR_URL} (may be empty)
**Verification Results:** (provided below)

{VERIFICATION_RESULTS}

**Screenshot Directory:** {SCREENSHOT_DIR}

## Your Task

1. Read the verification results above
2. Categorize each finding into one of four buckets:
   - **Working as Expected** -- feature works as the plan described
   - **Mismatch / Broken** -- feature doesn't match plan or is broken (assign severity: high/medium/low)
   - **Concern** -- works but has issues worth noting (UX, performance, accessibility)
   - **Out of Scope** -- observations unrelated to the plan but worth noting
3. Write the full report to `docs/verification/{DATE}-{BRANCH_SLUG}.md` using the format below (where `{BRANCH_SLUG}` is `{BRANCH_NAME}` with `/` replaced by `-`)
4. Return a concise summary (just the counts + any FAIL items) for the main agent to print

## Report Format

Write exactly this structure to the report file:

```markdown
# Verification Report: {BRANCH_NAME}
**Date:** {DATE}
**Plan:** {PLAN_PATH}
**PR:** {PR_URL}
**Branch:** {BRANCH_NAME} ({COMMIT_COUNT} commits ahead of main)

## Summary
- X items verified and working
- X concerns noted
- X mismatches or failures
- X out-of-scope observations

## Detailed Findings

### Working as Expected
| Feature | Page | What was verified | Screenshot |
|---------|------|-------------------|------------|
(fill from results)

### Mismatches / Broken
| Feature | Expected (from plan) | Actual | Severity | Screenshot |
|---------|---------------------|--------|----------|------------|
(fill from results -- severity is high/medium/low)

### Concerns
| Feature | Issue | Suggestion | Screenshot |
|---------|-------|------------|------------|
(fill from results)

### Out of Scope
| Observation | Where | Notes |
|-------------|-------|-------|
(fill from results)

## Edge Cases & Error States Tested
| Scenario | Result | Notes |
|----------|--------|-------|
(fill from results)

## Responsive Checks
| Page | Desktop | Tablet | Mobile | Notes |
|------|---------|--------|--------|-------|
(fill from results, only for pages that were responsive-tested)
```

## Severity Guide

- **High:** Core functionality broken, blocks the feature, plan explicitly requires this
- **Medium:** Feature works but behaves differently than plan describes, UX degraded
- **Low:** Minor visual issue, slightly different from plan but acceptable

## Summary Format (returned to main agent)

```
## Verification Summary: {BRANCH_NAME}
- X/Y items PASS
- X concerns
- X failures
- X out-of-scope notes

### Failures:
- [Feature]: [one-line description]

### Concerns:
- [Feature]: [one-line description]

Full report: docs/verification/{DATE}-{BRANCH_SLUG}.md
```
