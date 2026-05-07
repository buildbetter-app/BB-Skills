---
name: steering-review
description: Periodic review of pending steering notes — cluster, score, promote into durable guidance, and write a dated review artifact. Use weekly, or on demand when the pending pile gets large.
argument-hint: "[--since YYYY-MM-DD]"
---

# Steering Review

Run this skill on a cadence (weekly is the default) to convert accumulated steering notes into durable behavioral guidance. The companion `steering-capture` skill writes the inbound notes; this skill drains and promotes them.

## Inputs

- All notes under `~/.bb/steering-notes/SN-*.md` with `promotion_status: pending`
- Optional `--since YYYY-MM-DD` window (default: all pending notes)
- Current durable guidance surfaces:
  - `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/skills/`
  - For `scope: repo` notes: `AGENTS.md`, `CLAUDE.md`, `.claude/rules/`, `.claude/skills/` in the relevant repo

## Outputs

- A review artifact at `~/.bb/steering-reviews/YYYY-MM-DD.md`
- Updated frontmatter on every reviewed note (`promotion_status` flipped from `pending` to `promoted` / `not-needed` / `superseded`, plus `promotion_files`, `promotion_note`)
- Edits across the durable surfaces named above

## How this skill talks to `bb`

Soft dependency. If `bb steering` is available, use it for note discovery and status updates — joins, FTS search, and atomic file+DB updates come for free. Otherwise fall back to grep + manual frontmatter edits. The output (review artifact + updated note frontmatter) is byte-identical across both modes.

```bash
if command -v bb >/dev/null 2>&1 && bb steering --help >/dev/null 2>&1; then
  USE_BB=1
else
  USE_BB=0
fi
mkdir -p ~/.bb/steering-reviews
```

## Steps

1. **Detect `bb`** using the snippet above.

2. **Find candidate notes.**
   ```bash
   if [ "$USE_BB" = 1 ]; then
     bb steering list --status pending ${SINCE:+--since "$SINCE"} --json
   else
     grep -lE '^promotion_status:[[:space:]]*pending' ~/.bb/steering-notes/SN-*.md 2>/dev/null
   fi
   ```
   For older notes missing `promotion_status`, infer conservatively: treat as `pending` unless metadata or body clearly says otherwise. Drop notes already marked `promoted`, `not-needed`, or `superseded`.

3. **Cluster** in this order:
   1. Shared `pattern_key`
   2. Shared `tags`
   3. Semantic clustering over note summaries
   4. If still ambiguous, propose cluster boundaries explicitly and justify each one

4. **Score each cluster** with this rubric:

   | Factor | Range | Weight | How to score |
   |---|---:|---:|---|
   | Frequency | 0-5 | 4 | How often the pattern appears across notes in the window |
   | User irateness | 0-5 | 4 | Explicit frustration, repeated correction, urgency, or profanity |
   | Magnitude | 0-5 | 3 | How much the correction changes workflow or ship criteria |
   | Blast radius | 0-5 | 3 | How many tasks, skills, or repos are affected |
   | Recency | 0-3 | 1 | Newer misses get a small tie-break boost |
   | Evaluation gap | 0-3 | 2 | Does the system currently lack a rule/skill that would have prevented the miss? |

   `priority_score = 4*frequency + 4*irateness + 3*magnitude + 3*blast_radius + recency + 2*evaluation_gap`

5. **Route each cluster using theory-of-mind** — place guidance where a future agent will read it first for that task.
   - Default behavior across all work → `~/.claude/CLAUDE.md`
   - Durable invariants and policies → `~/.claude/rules/<topic>.md`
   - Repeatable workflows → `~/.claude/skills/<skill>/SKILL.md` (or update an existing one)
   - For `scope: repo` notes, mirror to repo-local `AGENTS.md` / `CLAUDE.md` / `.claude/rules/` / `.claude/skills/`
   - Do not append blindly. Merge or remove superseded guidance when a newer note overrides it.

6. **Evaluate before applying.**
   - **Retrieval eval:** simulate 3-5 future tasks that resemble the cluster's notes; confirm the updated guidance would surface first for those tasks.
   - **Scope eval:** the set of files you intend to change must match the scored clusters one-to-one. No drive-by edits.

7. **Apply changes.** Edit the durable surfaces, then update each promoted note's frontmatter.

   **bb mode:**
   ```bash
   bb steering update <note-id> \
     --status promoted \
     --add-files /path/to/CLAUDE.md /path/to/rule.md \
     --note "<one-line description of the durable change>"
   ```

   **Fallback mode:** edit the SN-*.md frontmatter in place — set `promotion_status: promoted`, populate `promotion_files: [...]`, add `promotion_note: ...`.

8. **Mark the rest.**
   - Notes intentionally kept local → `promotion_status: not-needed` with a one-line rationale.
   - Notes overridden by newer ones → `promotion_status: superseded` and link `superseded_by`.

   In bb mode:
   ```bash
   bb steering update <note-id> --status not-needed --note "<rationale>"
   bb steering update <older-id> --status superseded --superseded-by <newer-id>
   ```

9. **Write the review artifact** to `~/.bb/steering-reviews/YYYY-MM-DD.md` using the template below.

10. **(bb mode only)** Register the artifact:
    ```bash
    bb retrospective record --kind steering-review \
      --artifact ~/.bb/steering-reviews/$(date +%F).md \
      --window-start "$SINCE" --window-end "$(date +%F)" \
      --metrics '{"candidates":N,"promoted":P,"not_needed":X,"superseded":S}'
    ```
    Skip silently if `bb retrospective` is unavailable.

11. **Report** the review path, count of notes promoted vs not-needed vs superseded, and the durable files changed.

## Review Artifact Template

```md
# YYYY-MM-DD Steering Review

## Window
<since DATE | all pending>

## Candidate Set
<count, clustering method, high-priority clusters>

## Clusters & Scores
| Cluster | pattern_key | Notes | Score | Routed to |
|---|---|---:|---:|---|
| ... | ... | ... | ... | ... |

## Promotions
- <pattern_key>: <one-line description> → <files changed>

## Not Needed
- <note_id>: <rationale>

## Supersessions
- <older_note_id> superseded by <newer_note_id>: <reason>

## Structural Proposals
<optional: refactors to the durable surface that would improve retrieval>

## Verification
- Retrieval eval: <prompts used + outcomes>
- Scope eval: <changed files vs scored clusters>
```

## Guardrails

- **Do not commit.** Write files only. The user reviews and commits.
- **Do not delete notes.** Update frontmatter; the file stays as audit history.
- **Refactors stay scoped.** If a refactor does not measurably improve retrieval or reduce duplicate guidance, drop it.
- **Don't promote weak signals.** A single low-irateness, low-frequency note is rarely worth a durable rule. Mark it `not-needed` and move on.
