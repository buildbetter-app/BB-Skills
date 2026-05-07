---
name: steering-capture
description: Capture a user steering signal as a structured note under ~/.bb/steering-notes/, then apply the smallest durable adaptation that prevents the next miss. Use when the user corrects direction, redirects an approach, or asks the agent to adapt behavior.
---

# Steering Capture

Use this skill to turn a single piece of user steering — a correction, redirection, or validated unusual choice — into a durable, queryable note. A sibling skill (`steering-review`) promotes accumulated notes into long-lived guidance during a periodic review.

## Inputs

- The steering signal itself (the user's correction, redirection, or explicit guidance)
- The current task context the agent was operating in
- Recent notes already on disk at `~/.bb/steering-notes/` (for conflict and supersession checks)

## Outputs

- A new note at `~/.bb/steering-notes/SN-YYYYMMDD-HHMMSS-<8hex>.md`
- Optionally: edits to one durable surface (`~/.claude/CLAUDE.md`, `~/.claude/rules/<topic>.md`, `~/.claude/skills/<skill>/SKILL.md`, or repo-local equivalents) when the fix is obvious and bounded

## How this skill writes notes

This skill is **soft-dependent** on the `bb` CLI:

- If `bb steering log` is available, use it. The CLI handles id generation, file write, and DB index in one atomic operation.
- Otherwise, fall back to writing the SN-*.md file directly under `~/.bb/steering-notes/`.

Detection (run once at the start of the skill):

```bash
if command -v bb >/dev/null 2>&1 && bb steering --help >/dev/null 2>&1; then
  USE_BB=1
else
  USE_BB=0
  mkdir -p ~/.bb/steering-notes
fi
```

The fallback path is the original file-I/O flow described below in step 8b. The contract — file location, frontmatter schema, body sections — is identical across both paths so `steering-review` doesn't care which one wrote a given note.

## Steps

1. **Detect `bb` once** using the snippet above. Set `USE_BB`.

2. **Summarize the root cause** in one process-focused sentence. No blame, no narrative — just the rule that was missed.

3. **Check recent notes for conflicts** before promoting any guidance.
   - List recent pending notes:
     ```bash
     if [ "$USE_BB" = 1 ]; then
       bb steering list --status pending --json | head -20
     else
       ls -t ~/.bb/steering-notes/SN-*.md 2>/dev/null | head -20
     fi
     ```
   - Optionally search for prior notes on the same theme before adding a new one:
     ```bash
     [ "$USE_BB" = 1 ] && bb steering search "<keywords>" --limit 5
     ```
   - If two notes prescribe conflicting durable behavior and precedence is not explicit, **pause and ask the user** which behavior should win.
   - If a newer note explicitly overrides an older one, treat the newer note as authoritative.

4. **Decide scope.** Default `scope: user` — the lesson is personal and applies across repos. Use `scope: repo` only when the rule is genuinely repo-specific (e.g. "in this repo, never modify generated code under `gen/`").

5. **Apply the smallest durable adaptation that prevents repeat misses.** Only do this when the fix is obvious; otherwise leave `promotion_status: pending` and let `steering-review` handle it later.
   - User scope (default):
     - `~/.claude/CLAUDE.md` — global behavior defaults
     - `~/.claude/rules/<topic>.md` — durable invariants
     - `~/.claude/skills/<skill>/SKILL.md` — repeatable workflows
   - Repo scope:
     - `AGENTS.md` or `CLAUDE.md` at repo root
     - `.claude/rules/`
     - `.claude/skills/<skill>/SKILL.md`
   - Track every file you edit; pass them as `--apply` (bb mode) or fill `promotion_files` (fallback).

6. **Adaptation heuristics:**
   - Single, isolated miss → log note + local fix only.
   - Repeated pattern → update one durable surface in the same turn.
   - High-impact policy miss → add a rule under `~/.claude/rules/` (or repo `.claude/rules/`).

7. **Write the note.**

   **7a. bb mode (preferred):**
   ```bash
   bb steering log \
     --signal "$signal" \
     --root-cause "$root_cause" \
     --adaptation "$adaptation_summary" \
     --scope "$scope" \
     --pattern-key "$pattern_key" \
     --tags "$tags_csv" \
     ${applied_files:+--apply $applied_files} \
     --json
   ```
   The CLI generates `note_id`, writes the SN-*.md file, and inserts the DB row in one transaction. Capture the printed `file_path` for the final report.

   **7b. Fallback mode:** generate id and write the file by hand.
   ```bash
   ts=$(date +%Y%m%d-%H%M%S)
   hex=$(openssl rand -hex 4)
   note="$HOME/.bb/steering-notes/SN-${ts}-${hex}.md"
   # write the SN-*.md file using the template below
   ```
   Use the Note Template — every field that bb mode would set must appear in the frontmatter so `bb steering scan` can later index it identically.

8. **Report** the note filename and any adaptation files in your final reply.

## Note Template

```md
---
note_id: SN-YYYYMMDD-HHMMSS-<8hex>
timestamp: YYYY-MM-DD HH:MM TZ
scope: user            # or: repo
pattern_key:           # short stable identifier for the behavior family
tags: []               # routing + clustering hints
promotion_status: pending   # or: promoted | not-needed | superseded
promotion_files: []         # absolute paths of durable files updated
promotion_note:             # one line: what the durable change says
supersedes: []
superseded_by:
files_updated:
  - <path>
---

# SN-YYYYMMDD-HHMMSS-<8hex>

## Steering Signal
<verbatim or paraphrased user correction>

## Root Cause
<one process-focused sentence>

## Adaptation
<what you changed, or "pending — left for steering-review">
```

## Guardrails

- **Do not auto-commit.** Just write files. Let the user review and commit.
- **Do not invent durable rules from a single weak signal.** If frequency or magnitude is unclear, leave `promotion_status: pending`.
- **Do not write to any `docs/processes/agent-steering-notes/` path.** This skill's home is `~/.bb/steering-notes/`. Repo-local steering systems (e.g. bbapp's) use a different convention and are out of scope.
