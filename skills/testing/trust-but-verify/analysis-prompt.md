# Trust-But-Verify: Analysis Phase

You are analyzing a feature branch to create a verification checklist for browser-based testing.

## Context

**Branch:** {BRANCH_NAME}
**Base:** main

## Your Inputs

1. **ExecPlan** -- Read from `docs/plans/`. Find the plan most relevant to this branch (match by branch name, date, or topic).
2. **Diff** -- Run `git diff main...HEAD` to see what changed. Focus on frontend source changes.
3. **PR Description** -- Run `gh pr view --json title,body` to get PR context (if a PR exists, otherwise skip).
4. **App Map** -- Read `~/.claude/skills/app-navigator/app-map.md` if it exists. This tells you what pages exist and how to navigate to them.
5. **Playbooks** -- Read files in `~/.claude/skills/app-navigator/playbooks/` if they exist. These document interaction patterns.

## Your Output

Produce a **Verification Checklist** in this exact format:

```
## Verification Checklist

### 1. [Feature/Change Name]
- **Page:** /route/path
- **Elements to verify:** [list of UI elements that should be present based on plan + diff]
- **Happy path:**
  1. [Step-by-step interaction sequence]
  2. [Expected outcome after each step]
- **Edge cases:**
  - [Empty state: what happens with no data?]
  - [Invalid input: what happens with bad values?]
  - [Boundary: max length, special characters, etc.]
- **Error states:**
  - [Network failure: what should the UI show?]
  - [Permission denied: handled gracefully?]
  - [Server error: error message displayed?]
- **Responsive:** [yes/no -- only if this page is in the diff]
  - [Specific layout expectations if any]

### 2. [Next Feature/Change]
...
```

## Guidelines

- Only include pages/routes that are RELEVANT to the plan and diff. Don't test the whole app.
- Be specific about UI elements: "a button labeled 'Generate'" not "a button".
- Be specific about expected outcomes: "a toast notification saying 'Document created'" not "success feedback".
- For edge cases, think about what the plan says should happen AND what common failure modes exist.
- If the app map exists, reference page names from it for consistency.
- If the diff shows new routes, include them even if they're not in the app map yet.
- Order checklist items by importance: core functionality first, edge cases last.
