---
name: review
description: Run a BuildBetter-first UX/usability and/or code review for the current feature.
argument-hint: <usability|code|both>
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Run a BuildBetter-enriched review for the current feature with one of these modes:

- `usability`: user-story walkthrough and UX validation
- `code`: implementation/code quality review
- `both` (default): run both

This command is BuildBetter-first: prioritize `buildbetter-context.md`, `buildbetter-context.json`, and `user-stories.md` as review evidence when available.

## Execution Flow

1. **Initialize context**
   - Locate the current feature directory and verify available documents.
   - Required docs: `spec.md`, `plan.md`, `tasks.md`.
   - BuildBetter docs: `buildbetter-context.md`, `buildbetter-context.json`, `user-stories.md` (optional but preferred).
   - If required docs are missing: stop and instruct the user to run the missing prerequisite skill (e.g., use the specify, plan, or tasks skill first).

2. **Resolve review mode**
   - Parse `$ARGUMENTS`:
     - if contains `usability` -> usability-only
     - if contains `code` -> code-only
     - if contains `both` or empty -> both
   - If arguments are ambiguous, default to `both`.

3. **Load minimal review context**
   - From `spec.md`: user stories, acceptance scenarios, functional and non-functional requirements.
   - From `plan.md`: architecture constraints, intended UX/platform surfaces, technical tradeoffs.
   - From `tasks.md`: story coverage, dependency ordering, test tasks.
   - From BuildBetter artifacts (if present): exact quotes, evidence IDs, themes, customers affected, evidence-backed stories.

4. **Usability review (if selected)**
   - Evaluate each primary user story through this narrative:
     - Is this easy to use?
     - Is this intuitive?
     - Does this solve the problem?
     - Does this work?
   - For each question, produce a verdict: `pass`, `risk`, or `fail` with rationale.
   - Use BuildBetter evidence IDs (`BB-EXTRACTION-*`) where available.
   - Detect whether this is a visual/UI-heavy feature (pages, flows, forms, dashboard, mobile/web UI states).
   - If visual/UI-heavy:
     - Recommend Playwright validation and provide a focused scenario list tied to user stories.
     - Include coverage for happy path, alternate flow, and failure/edge case.
   - If not visual-heavy:
     - Recommend API/integration behavior checks aligned with user stories and acceptance criteria.

5. **Code review (if selected)**
   - Review implementation state using current branch changes and task intent.
   - Prioritize findings in this order:
     - correctness/behavioral regressions
     - security/privacy issues
     - reliability/performance risks
     - missing tests for user-story acceptance criteria
     - maintainability issues that materially increase delivery risk
   - Keep findings concrete with file references and impact statements.
   - If no issues are found, state that explicitly and list remaining testing gaps.

6. **Coverage and traceability checks**
   - Map each reviewed user story to:
     - acceptance criteria coverage
     - task coverage (`tasks.md`)
     - evidence linkage (BuildBetter IDs) when available
   - Flag any story with weak evidence, missing validation, or missing implementation coverage.

7. **Produce review report**
   - Write `FEATURE_DIR/review.md` with this structure:

   ```markdown
   # Review Report

   ## Review Scope
   - Mode: [usability|code|both]
   - BuildBetter Evidence: [available|partial|missing]

   ## Usability Review
   - Story: ...
   - Easy to use: [pass|risk|fail] - rationale
   - Intuitive: [pass|risk|fail] - rationale
   - Solves the problem: [pass|risk|fail] - rationale
   - Works: [pass|risk|fail] - rationale
   - Evidence refs: [BB-EXTRACTION-###]

   ## Playwright Recommendation
   - Needed: [yes|no]
   - Why:
   - Suggested scenarios:

   ## Code Review Findings
   - [Severity] [File] Finding summary and recommendation

   ## Coverage Matrix
   - Story -> acceptance criteria -> tasks -> evidence refs

   ## Verdict
   - Ready / Ready with risks / Not ready
   - Blocking issues:
   - Suggested next step:
   ```

8. **Report completion**
   - Return the path to `review.md`.
   - Summarize:
     - mode used
     - whether Playwright is recommended
     - top risks/blockers
     - readiness verdict

## Rules

- Be explicit and deterministic; avoid vague review statements.
- Never fabricate evidence IDs or implementation status.
- Keep BuildBetter quotes redacted if re-quoted.
- Do not modify `spec.md`, `plan.md`, or `tasks.md` in this command.
