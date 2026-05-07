---
name: pr-review-retrospective
description: Self-coaching retrospective from your own PR review history. Pulls reviewer comments on your authored PRs over a window, clusters by theme, writes a dated MD, and auto-emits steering notes for recurring themes so the steering-review pipeline picks them up.
argument-hint: "[--since YYYY-MM-DD]"
---

# PR Review Retrospective

Use this skill to turn the last N days of reviewer feedback into a personal coaching artifact and to seed durable behavior changes via the existing steering pipeline.

This skill is part of the `self-improvement` pack and closes the loop with two siblings:
- `steering-capture` — writes structured notes from live steering signals
- `steering-review` — periodically promotes notes into durable guidance

This skill emits notes in the same format and location, so the next `steering-review` run can promote them alongside live signals.

## Inputs

- GitHub `gh` CLI authenticated as the user
- Optional `--since YYYY-MM-DD` (default: last 30 days)

## Outputs

- A retrospective at `~/.bb/retrospectives/pr-review-YYYY-MM-DD.md` (today's date)
- Zero or more steering notes at `~/.bb/steering-notes/SN-YYYYMMDD-HHMMSS-<8hex>.md` (one per cluster meeting the auto-emit threshold)

## Prerequisites

This skill prefers `bb` for data fetching when available, falling back to `gh` directly:

```bash
if command -v bb >/dev/null 2>&1 && bb retrospective --help >/dev/null 2>&1; then
  USE_BB=1
else
  USE_BB=0
  gh auth status || { echo "gh not authenticated. Run: gh auth login"; exit 1; }
fi
```

In bb mode, `bb` shells out to `gh` itself and stores results in sqlite — faster on subsequent runs and resilient to GitHub rate limits. Fallback mode shells `gh` directly. Either way, `gh` must ultimately be authenticated on the machine.

## Steps

1. **Detect `bb`** using the snippet above.

2. **Ensure output directories exist.**
   ```bash
   mkdir -p ~/.bb/retrospectives ~/.bb/steering-notes
   ```

3. **Determine the window.**
   - Default: 30 days ago in `YYYY-MM-DD`.
   - Override: `--since YYYY-MM-DD` from the user's invocation.

4. **Fetch authored PRs and reviewer feedback.**

   **bb mode (preferred):**
   ```bash
   bb retrospective pr-data --since "$SINCE" --json
   ```
   Returns a single JSON document: `{ prs: [...], comments_by_pr: {...}, reviews_by_pr: {...} }`. The CLI handles pagination, dedupe, and storage in `pr_comments` / `pr_reviews` tables.

   **Fallback mode:**
   ```bash
   gh search prs --author=@me --created=">=$SINCE" \
     --json url,number,repository,title,state,createdAt,mergedAt \
     --limit 200
   # then per PR:
   gh api "repos/{owner}/{repo}/pulls/{n}/comments"  --paginate
   gh api "repos/{owner}/{repo}/pulls/{n}/reviews"   --paginate
   gh api "repos/{owner}/{repo}/issues/{n}/comments" --paginate
   ```
   Capture per comment: `id`, `user.login`, `body`, `path`, `line`, `created_at`, `in_reply_to_id`. Capture per review: `id`, `user.login`, `state`, `body`, `submitted_at`.

5. **Filter out the user's own comments.** This skill is about feedback received, not given. Drop any comment or review where `user.login` matches the authenticated user.

6. **Cluster comments by theme.** Read the comments and propose 5-10 specific, actionable themes. Themes should name the behavior, not a generic category — e.g. "missing null checks on optional API fields", not "code quality". Assign every comment to one theme; allow a small "long tail" bucket for unclassified. **This is the LLM-reasoning portion** — never delegated to `bb`.

7. **Rank themes** by:
   ```
   score = comment_count * distinct_reviewer_count * (1 + blocked_merge_count)
   ```
   where `blocked_merge_count` is the number of reviews with `state = CHANGES_REQUESTED` that contain at least one comment in the theme.

8. **Render the retrospective** to `~/.bb/retrospectives/pr-review-YYYY-MM-DD.md` using the template below.

9. **Auto-emit steering notes.** For every theme meeting the threshold (≥3 distinct comments **or** appearing on ≥2 distinct PRs), write one steering note.

   **bb mode:**
   ```bash
   bb steering log \
     --signal "Recurring reviewer feedback: <theme name> (N comments across K PRs)." \
     --root-cause "<one process-focused sentence>" \
     --adaptation "pending — left for steering-review." \
     --scope user \
     --pattern-key "pr-review-<slug-of-theme>" \
     --tags "pr-review,<theme-tags>" \
     --source pr-review-retrospective \
     --source-artifact "$ARTIFACT_PATH"
   ```

   **Fallback mode:** write SN-*.md files directly. Use `date +%Y%m%d-%H%M%S` and `openssl rand -hex 4` for the id; vary the hex if you write multiple in a tight loop. Match the frontmatter contract below exactly.

10. **(bb mode only)** Register the artifact:
    ```bash
    bb retrospective record --kind pr-review \
      --artifact "$ARTIFACT_PATH" \
      --window-start "$SINCE" --window-end "$(date +%F)" \
      --metrics '{"pr_count":N,"comment_count":M,"theme_count":T,"notes_emitted":E}'
    ```
    Skip silently if `bb retrospective` is unavailable.

11. **Report** to the user: window, PR count, theme count, retrospective path, count of steering notes emitted, and a one-line suggestion to run `steering-review` next.

## Retrospective Template

```md
# PR Review Retrospective — YYYY-MM-DD

## Window
- Since: YYYY-MM-DD
- Authored PRs in window: N
- Reviewer comments analyzed: M
- Distinct reviewers: K

## Top Themes
### 1. <theme name> — score X (N comments, K reviewers, B blocking reviews)
**What to do differently:** <one sentence>

Representative quotes:
- "<quote>" — `repo#prNum` by @reviewer
- "<quote>" — `repo#prNum` by @reviewer

### 2. ...

## Long Tail
<one-liners for unclustered comments worth keeping>

## Suggested Durable Rules
<themes the user might want to encode in ~/.claude/rules/ via steering-review>

## Steering Notes Emitted
- `~/.bb/steering-notes/SN-...md` — <theme>
- ...
```

## Steering Note Frontmatter Contract

Emitted notes must match the schema `steering-capture` writes, so `steering-review` can promote them without special-casing:

```yaml
---
note_id: SN-YYYYMMDD-HHMMSS-<8hex>
timestamp: YYYY-MM-DD HH:MM TZ
scope: user
pattern_key: pr-review-<slug-of-theme>
tags: [pr-review, <theme-tags>]
promotion_status: pending
promotion_files: []
promotion_note:
supersedes: []
superseded_by:
source: pr-review-retrospective
source_artifact: ~/.bb/retrospectives/pr-review-YYYY-MM-DD.md
files_updated: []
---

# SN-YYYYMMDD-HHMMSS-<8hex>

## Steering Signal
Recurring reviewer feedback: <theme name> (N comments across K PRs).

## Root Cause
<one process-focused sentence>

## Adaptation
pending — left for steering-review.
```

## Guardrails

- **Do not commit.** Files only.
- **Do not modify the user's PRs.** Read-only against GitHub.
- **Filter own comments.** This is about feedback received, never feedback given.
- **Be specific in theme names.** A theme called "code quality" is useless. "Missing null checks on optional API fields" is actionable.
- **Don't auto-emit weak signals.** A theme with 1 comment from 1 reviewer does not become a steering note. Threshold is real.
