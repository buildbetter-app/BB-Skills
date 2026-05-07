# Proposal: bb CLI capture extensions

**Status:** Draft
**Owner:** TBD
**Audience:** maintainers of `bbapp/packages/apps/cli`
**Related:** the `self-improvement` skill pack in BB-Skills

## 1. Motivation

The `bb` CLI today captures Codex and Claude Code agent sessions and uploads them to `/v3/rest/agent-sessions/upsert`. Locally it stores only `~/.bb/config.json` (auth) and `~/.bb/agent-session-submit-errors.jsonl` (failed-sync log). The provider-native session JSONLs at `~/.codex/sessions/**` and `~/.claude/projects/<sanitized-cwd>/*.jsonl` are read-through, not indexed.

That coverage is enough for **session sync and resume**, but a new class of personal-coaching skills wants three additional shapes of data:

1. **A queryable view of the event stream** (so a skill can ask "how often did I rerun tests in the same session?" without parsing JSONL).
2. **File diffs** for every commit seen in those sessions (so review-style skills can read actual patch content, not just SHAs).
3. **PR review comments and reviews** for PRs the user authored (so skills can mine reviewer feedback patterns).

Concrete consumers already exist as skills in BB-Skills' `self-improvement` pack:

- `pr-review-retrospective` currently shells out to `gh` ad-hoc on every run. With CLI-side capture this becomes a sqlite query: faster, offline-capable, historically complete, and resilient to GitHub rate limits.
- `steering-review` would gain the ability to cross-reference steering notes against the diffs that prompted them.
- A future `tool-call-retrospective` skill could mine the events table for inefficient agent patterns ("read same file 8x in one session").

This proposal adds local capture under `~/.bb/data/bb.db` and a small set of `bb capture` and `bb db` subcommands. Server-side mirroring is explicitly **out of scope for v1** — sqlite is treated as a derived view, so we can event-source it later without breaking consumers.

## 2. Storage decision

Recommended: **sqlite at `~/.bb/data/bb.db`**, chmod 600.

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Sqlite (recommended) | Indexed lookups, joins, queryable from any skill via `sqlite3` CLI, single-file, atomic | Need DDL migrations, ~50MB binary if statically linked (or system sqlite) | Picked |
| JSONL append-log | Simplest possible | No joins, full scans for every query, no schema evolution | Skip — skills will reinvent indexes |
| Server-side ingestion only | One source of truth, cross-device | Network-dependent, latency, rate limits, leaks ~all dev activity to a server | Skip for v1 — keep local-only and revisit |

A future server-side mirror can pull from sqlite or replay the same capture commands against a remote DB. Treating sqlite as a derived view (rebuildable from the JSONL + `git` + `gh`) makes that migration low-risk.

## 3. Schema

```sql
-- One row per agent session known to bb
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL,                       -- 'codex' | 'claude_code'
  provider_session_id TEXT NOT NULL,
  cwd TEXT,
  repo_root TEXT,
  git_branch TEXT,
  commit_sha TEXT,
  github_repository TEXT,                       -- 'owner/repo' if known
  pr_number INTEGER,
  pr_url TEXT,
  pr_base_branch TEXT,
  started_at TEXT,
  ended_at TEXT,
  cli_version TEXT,
  source_jsonl_path TEXT NOT NULL,              -- the JSONL bb materialized from
  UNIQUE(provider, provider_session_id)
);

-- Materialized from CanonicalAgentEvent (see types.rs:32-44 in bb CLI)
CREATE TABLE events (
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,                         -- CanonicalAgentEvent.sequenceNumber
  provider_event_id TEXT,
  kind TEXT NOT NULL,                           -- 'user_message' | 'assistant_message' | 'tool_call' | 'tool_result' | 'status'
  role TEXT,
  occurred_at TEXT NOT NULL,
  text TEXT,                                    -- truncated to 4000 chars upstream
  payload_json TEXT,                            -- raw JSON object
  PRIMARY KEY (session_id, seq)
);

-- One row per (repo, sha) seen in sessions or via on-demand capture
CREATE TABLE commits (
  repo TEXT NOT NULL,                           -- 'owner/repo' or repo_root path if no remote
  sha TEXT NOT NULL,
  branch TEXT,
  author TEXT,
  committed_at TEXT,
  message TEXT,
  insertions INTEGER,
  deletions INTEGER,
  files_changed INTEGER,
  PRIMARY KEY (repo, sha)
);

CREATE TABLE commit_diffs (
  repo TEXT NOT NULL,
  sha TEXT NOT NULL,
  path TEXT NOT NULL,
  patch TEXT,                                   -- unified diff for this file at this sha
  PRIMARY KEY (repo, sha, path),
  FOREIGN KEY (repo, sha) REFERENCES commits(repo, sha) ON DELETE CASCADE
);

CREATE TABLE prs (
  repo TEXT NOT NULL,
  number INTEGER NOT NULL,
  title TEXT,
  author TEXT,
  base_branch TEXT,
  head_branch TEXT,
  state TEXT,                                   -- 'open' | 'closed' | 'merged'
  created_at TEXT,
  merged_at TEXT,
  closed_at TEXT,
  url TEXT,
  PRIMARY KEY (repo, number)
);

CREATE TABLE pr_comments (
  repo TEXT NOT NULL,
  pr_number INTEGER NOT NULL,
  comment_id INTEGER NOT NULL,
  kind TEXT NOT NULL,                           -- 'review_thread' | 'issue' (review summary lives in pr_reviews)
  author TEXT,
  body TEXT,
  path TEXT,
  line INTEGER,
  created_at TEXT,
  in_reply_to INTEGER,
  PRIMARY KEY (repo, pr_number, comment_id),
  FOREIGN KEY (repo, pr_number) REFERENCES prs(repo, number) ON DELETE CASCADE
);

CREATE TABLE pr_reviews (
  repo TEXT NOT NULL,
  pr_number INTEGER NOT NULL,
  review_id INTEGER NOT NULL,
  reviewer TEXT,
  state TEXT,                                   -- 'APPROVED' | 'CHANGES_REQUESTED' | 'COMMENTED' | 'DISMISSED'
  body TEXT,
  submitted_at TEXT,
  PRIMARY KEY (repo, pr_number, review_id),
  FOREIGN KEY (repo, pr_number) REFERENCES prs(repo, number) ON DELETE CASCADE
);

-- Personal corpus: steering notes mirrored from ~/.bb/steering-notes/SN-*.md.
-- The MD files remain source of truth (editable, greppable, gitable);
-- this table is a query/index layer kept in sync by `bb steering scan` and
-- by every `bb steering log|update`.
CREATE TABLE steering_notes (
  note_id TEXT PRIMARY KEY,                     -- 'SN-YYYYMMDD-HHMMSS-XXXXXXXX'
  scope TEXT NOT NULL,                          -- 'user' | 'repo'
  repo TEXT,                                    -- absolute path or 'owner/repo'; NULL when scope='user'
  pattern_key TEXT,
  tags_json TEXT,                               -- JSON array
  promotion_status TEXT NOT NULL,               -- 'pending' | 'promoted' | 'not-needed' | 'superseded'
  promotion_files_json TEXT,                    -- JSON array of absolute paths
  promotion_note TEXT,
  supersedes_json TEXT,                         -- JSON array of note_ids
  superseded_by TEXT,
  source TEXT,                                  -- 'manual' | 'pr-review-retrospective' | 'auto-detect'
  source_artifact TEXT,                         -- e.g. retrospective MD that emitted this note
  steering_signal TEXT,                         -- body section
  root_cause TEXT,
  adaptation TEXT,
  file_path TEXT NOT NULL,                      -- absolute path of the SN-*.md on disk
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX steering_status   ON steering_notes(promotion_status);
CREATE INDEX steering_pattern  ON steering_notes(pattern_key);
CREATE INDEX steering_created  ON steering_notes(created_at);
CREATE INDEX steering_source   ON steering_notes(source);

-- Full-text search over note bodies for cluster work.
CREATE VIRTUAL TABLE steering_notes_fts USING fts5(
  note_id UNINDEXED,
  steering_signal,
  root_cause,
  adaptation,
  pattern_key,
  content='steering_notes',
  content_rowid='rowid'
);

-- One row per generated retrospective artifact under ~/.bb/retrospectives/.
CREATE TABLE retrospectives (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,                           -- 'pr-review' (extensible)
  generated_at TEXT NOT NULL,
  window_start TEXT,
  window_end TEXT,
  artifact_path TEXT NOT NULL,                  -- absolute path of the MD
  metrics_json TEXT,                            -- {pr_count, comment_count, theme_count, notes_emitted}
  UNIQUE(kind, generated_at)
);

CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE INDEX events_kind         ON events(kind);
CREATE INDEX events_occurred     ON events(occurred_at);
CREATE INDEX commits_branch      ON commits(branch);
CREATE INDEX prs_state           ON prs(state);
CREATE INDEX pr_comments_author  ON pr_comments(author);
CREATE INDEX pr_comments_created ON pr_comments(created_at);
CREATE INDEX sessions_pr         ON sessions(github_repository, pr_number);
CREATE INDEX sessions_started    ON sessions(started_at);
```

The `events` table is **materialized from JSONL** by `bb capture events`. The JSONL files (`~/.codex/sessions/**`, `~/.claude/projects/**`) remain the source of truth. Rebuilding the table from sources is supported and explicitly safe.

## 4. New subcommands

Two subcommand families.

**Capture / DB (data layer):**
```
bb capture events       [--since DATE] [--all]
bb capture diffs        [--since DATE] [--repo SLUG]
bb capture pr-comments  [--since DATE] [--repo SLUG]
bb capture all          [--since DATE]
bb db path
bb db query "SELECT ..."
bb db rebuild           # drop materialized tables, replay capture from sources
```

**Personal corpus (steering + retrospectives):**
```
bb steering log         --signal "..." [--root-cause "..."] [--adaptation "..."]
                        [--scope user|repo] [--repo PATH] [--pattern-key X]
                        [--tags a,b,c] [--source SOURCE] [--source-artifact PATH]
                        [--apply FILE...]              # files updated as part of the fix
                        [--json]                       # print {note_id, file_path}
bb steering list        [--status pending|promoted|not-needed|superseded]
                        [--since DATE] [--pattern-key X] [--scope user|repo] [--json]
bb steering get         <note-id> [--json]
bb steering update      <note-id> [--status STATUS] [--add-files PATH...] [--note "..."]
                        [--superseded-by NOTE-ID]
bb steering search      "<query>" [--limit N] [--json]   # FTS5 over note bodies
bb steering scan                                          # re-read SN-*.md into the DB

bb retrospective pr-data  [--since DATE] [--repo SLUG] [--json]   # fetch PRs+comments, return JSON
bb retrospective record   --kind KIND --artifact PATH
                          [--window-start DATE] [--window-end DATE] [--metrics JSON]
bb retrospective list     [--kind KIND] [--json]
bb retrospective get      <date> [--kind KIND]
```

For each:

### `bb capture events [--since DATE] [--all]`
- **Reads:** the same provider session paths used today (`providers.rs:262-497` for Codex, `providers.rs:651-837` for Claude Code).
- **Writes:** `sessions` and `events` rows. Idempotent on `(provider, provider_session_id)` for sessions and `(session_id, seq)` for events.
- **Side effects:** none beyond DB writes.
- **Errors:** transient parse errors per record are skipped with a counter; per-file errors abort that file only.

### `bb capture diffs [--since DATE] [--repo SLUG]`
- **Reads:** distinct `(repo_root, commit_sha)` pairs from `sessions` newer than `--since`. Resolves each via `git -C <repo_root> show --format=fuller --numstat --patch <sha>`.
- **Writes:** `commits` (one row) and `commit_diffs` (one row per file). Skip if `(repo, sha)` already present.
- **Errors:** if `repo_root` no longer exists or `sha` is unreachable, log to `~/.bb/agent-session-submit-errors.jsonl` style file (`~/.bb/capture-errors.jsonl`) and continue.

### `bb capture pr-comments [--since DATE] [--repo SLUG]`
- **Reads:** PRs to ingest are determined by union of:
  1. Distinct `(github_repository, pr_number)` from `sessions` newer than `--since`
  2. `gh search prs --author=@me --created=">=DATE"` (so we don't miss PRs that didn't have a recorded session)
- **Per PR, fetches:**
  ```
  gh api repos/{repo}/pulls/{n}                 -> prs row
  gh api repos/{repo}/pulls/{n}/comments  --paginate
  gh api repos/{repo}/pulls/{n}/reviews   --paginate
  gh api repos/{repo}/issues/{n}/comments --paginate
  ```
- **Writes:** upserts `prs`, `pr_comments`, `pr_reviews`. Idempotent on the natural keys defined in the schema.
- **Errors:** `gh` auth failure aborts immediately with an actionable message. Per-PR `gh api` failures are logged and skipped.

### `bb capture all [--since DATE]`
Convenience: runs `events`, `diffs`, then `pr-comments` in that order.

### `bb db path`
Prints `~/.bb/data/bb.db`. Skills use this to locate the DB.

### `bb db query "SQL"`
Runs the SQL via the embedded sqlite, prints results as JSON lines on stdout. Read-only by default; reject any statement that doesn't start with `SELECT`, `EXPLAIN`, or `WITH ... SELECT`. (Verify that the chosen sqlite crate supports a read-only handle.)

### `bb db rebuild`
Drops `events`, `commits`, `commit_diffs`, `prs`, `pr_comments`, `pr_reviews` and re-runs `bb capture all` from sources. Re-runs `bb steering scan` afterwards to repopulate the steering index. Confirmation prompt unless `--yes`.

### `bb steering log`
- **Reads:** flags only.
- **Writes:** creates a new `~/.bb/steering-notes/SN-YYYYMMDD-HHMMSS-<8hex>.md` file with the frontmatter contract documented in BB-Skills' `steering-capture` SKILL, **and** inserts the corresponding `steering_notes` row.
- **Output:** prints the absolute path of the new file. With `--json`, prints `{"note_id":"SN-...","file_path":"..."}`.
- **Errors:** if `--scope repo` and `--repo` is omitted, default to `git rev-parse --show-toplevel` from `cwd`; abort if not inside a repo.

### `bb steering list / get / update`
- `list` queries the `steering_notes` table; `--status pending` is the common case for `steering-review`.
- `get` returns the full row + body (read from the file on disk). With `--json`, returns the row as JSON plus `body_md`.
- `update` mutates **both** the SN-*.md frontmatter and the DB row in one transaction. Adding files is additive (de-duped). Setting `--status` triggers `updated_at`.

### `bb steering search "query"`
FTS5 query against `steering_notes_fts`. Use this to find existing notes before logging a new one (avoids duplicate captures of the same pattern).

### `bb steering scan`
Walks `~/.bb/steering-notes/*.md`, parses YAML frontmatter, upserts into `steering_notes`. Idempotent. Run this if files were edited by hand or written by a skill that bypassed `bb steering log`.

### `bb retrospective pr-data [--since DATE]`
- **Reads:** runs `bb capture pr-comments --since DATE` first (so DB is fresh), then queries `prs`, `pr_comments`, `pr_reviews` for the window.
- **Writes:** nothing new in the DB beyond the capture step.
- **Output:** JSON describing PRs in window, all comments grouped by PR, reviewers, and review verdicts. The skill ingests this for clustering.
- **Why on the CLI:** centralizes the gh-fetch + filter logic. The skill handles the LLM-reasoning portion (theme clustering); the CLI handles deterministic data shape.

### `bb retrospective record`
Skills call this **after** writing a retrospective MD file. Inserts a row in `retrospectives` so `bb retrospective list/get` can find it later.

### `bb retrospective list / get`
Read-only.

## 5. Capture pipelines — implementation notes

- **events** can reuse most of `providers.rs`. The existing event normalizer already produces `CanonicalAgentEvent` (`types.rs:32-44`); add a sqlite sink alongside the existing API submission. Recommend extracting a small `EventSink` trait so `sync` (HTTP) and `capture events` (sqlite) share the parser.
- **diffs** uses `git2` if already a dependency; otherwise shell out to `git` like `git.rs` does today (verify which approach `git.rs` uses — `git.rs:15-23`). Parse `--numstat` for the rollup totals; full patch as one string per file.
- **pr-comments** uses the existing reqwest HTTP client (`http.rs:1-78`) for the `gh` API directly, **or** shells out to `gh`. Shelling out is simpler (no PAT management — the user's `gh` already has one) and matches what skills do today; recommend that for v1.

## 5b. Personal corpus pipelines

### Steering note write path

`bb steering log` is the canonical write. The flow:

1. Generate `note_id` = `SN-$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4)`.
2. Compute `file_path` = `~/.bb/steering-notes/<note_id>.md`.
3. Begin sqlite transaction.
4. Insert row into `steering_notes` (FTS index trigger fires automatically).
5. Write the SN-*.md file from frontmatter + body fields. Use atomic rename (`tmpfile + rename`) so a partial write never appears.
6. Commit transaction.
7. Print `file_path` on stdout (or JSON if `--json`).

Failure modes:
- DB write succeeds but file write fails: rollback DB transaction.
- File write succeeds but DB insert fails (duplicate `note_id`): unlink file, abort.

### Steering update path

`bb steering update` modifies both surfaces in one transaction:

1. Read current frontmatter from disk (source of truth).
2. Apply mutations (`promotion_status`, `promotion_files`, `promotion_note`, `superseded_by`).
3. Write SN-*.md atomically.
4. Update `steering_notes` row + `updated_at`.

If anyone has hand-edited the file since the DB was last in sync, the file's frontmatter wins and the DB is reconciled. `bb steering scan` is the bulk reconcile.

### Skill integration contract — soft dependency

BB-Skills' `self-improvement` pack uses these subcommands when available, but **falls back to direct file I/O** when `bb` is missing or doesn't have the steering surface yet. A skill should detect the surface like this:

```bash
if command -v bb >/dev/null 2>&1 && bb steering --help >/dev/null 2>&1; then
  bb steering log --signal "..." --root-cause "..." --scope user --pattern-key foo --json
else
  # write SN-*.md directly to ~/.bb/steering-notes/
fi
```

This keeps skills usable on machines that don't have a recent enough `bb`, while letting them benefit immediately on machines that do.

### Retrospective generation path

`pr-review-retrospective` (skill) and `bb` split labor:

1. Skill calls `bb retrospective pr-data --since DATE --json` (or skill falls back to `gh` directly if `bb` is too old).
2. CLI runs `bb capture pr-comments --since DATE` (idempotent), then emits JSON with PRs + comments grouped.
3. Skill performs the LLM-reasoning portion: theme clustering, naming, scoring, drafting the MD.
4. Skill writes `~/.bb/retrospectives/pr-review-YYYY-MM-DD.md`.
5. Skill calls `bb retrospective record --kind pr-review --artifact PATH --metrics '{"pr_count":N,...}'` to register it.
6. For each cluster meeting threshold, skill calls `bb steering log --source pr-review-retrospective --source-artifact PATH ...`.

CLI never invokes the LLM. Skill never reaches for `gh` if `bb` has the data.

## 6. Hook integration (optional, phase 4)

The Stop hook (`hooks.rs:14-117`) already runs `bb hook stop` at the end of every Codex/Claude Code session. Extend it to optionally run capture:

```
bb agent-sessions hooks install --claude --capture-diffs --capture-pr-comments
bb agent-sessions hooks install --codex  --capture-diffs --capture-pr-comments
```

The installed Stop hook then runs:
```
bb hook stop                                     # current behavior — sync to API
bb capture diffs --since=<session_started_at>    # if --capture-diffs was set
bb capture pr-comments --repo=<github_repository> --since=<session_started_at>
```

### Future: auto-detection of steering signals

Once `bb capture events` materializes session events into sqlite, an additional hook step can scan the just-completed session for steering signals (user messages starting with "no", "stop", "don't", or following a tool-call rejection) and emit `pending` notes via `bb steering log --source auto-detect` without user invocation. This is **out of scope for v1** — described here only so the schema (`source` column on `steering_notes`) and command surface are forward-compatible.

Detection is fuzzy and benefits from LLM judgment, so the right shape is probably an opt-in skill (`steering-detect`) that runs on session-start, processes a queue of recently-finished sessions, and calls `bb steering log` per detected signal. The CLI need not embed an LLM.

```
# context for the future hook (not phase 4)
bb hook stop --queue-steering-detect             # marks the session for next-start scan
```

Failures in the new captures must NOT break sync. Wrap each in `|| true` equivalent.

## 7. Open questions

1. **Retention.** Keep forever vs prune > 180 days vs user-configurable? Recommend keep-forever for v1, add `bb db prune --before DATE` later if disk usage becomes a real complaint.
2. **events: materialize vs view.** The proposed design materializes. Alternative: define a sqlite virtual table over JSONL (e.g. via the `csv` virtual table or a custom one) so the events table stays in sync without `bb capture events`. Materialization is simpler to reason about and survives source-file rotation; recommend keeping materialization for v1.
3. **Server-side mirror.** Out of scope for v1 — but the schema is intentionally compatible with a future `/v3/rest/{commits,prs,pr-comments}/upsert` endpoint family. Decide later whether mirroring should be opt-in or default.
4. **`gh` auth assumption.** Assume `gh auth status` succeeds; otherwise abort `bb capture pr-comments` with a clear message. No re-auth flow in v1.
5. **PR diff vs commit diffs.** PR-level diff (`gh pr diff`) differs from the union of commit diffs when rebases or merge commits intervene. Recommend capturing **commit diffs only** in v1 (simpler, matches what's already in `sessions`), and adding a `pr_diffs` table later if a consumer skill needs it.
6. **Steering source of truth.** SN-*.md files vs DB row. Recommend **files are source of truth** — the DB is rebuildable via `bb steering scan`. Tradeoff: every `bb steering update` does two writes. Acceptable for low write volume.
7. **Multi-machine sync.** Steering notes are personal but a developer might use multiple machines. v1 punts (rsync-your-`~/.bb/` works); v2 could add `bb steering pull/push` against the API.

## 8. Migration & risk

- **DB migrations:** `schema_migrations` table tracks applied versions. Each migration is an idempotent SQL block in `src/db/migrations/NNN_*.sql`. On startup, `bb db open()` runs any unapplied migrations.
- **Disk usage estimate.** A developer with 50 PRs/month, ~20 commits each, ~10 files each, ~2KB diff each → ~200MB/year for diffs. Comments are negligible (~5MB/year). Events are bounded by upstream JSONL volume, typically 10-100MB/month per heavy user. Plan for ~1-2GB for an active developer over 5 years; well within sqlite limits.
- **Privacy.** The DB will contain code, commit messages, comment bodies, and PR titles. Default `chmod 600` on `~/.bb/data/bb.db`. Document the path so users can shred it. Do not log DB contents to stderr or telemetry.
- **Concurrency.** Sqlite WAL mode by default. The CLI is short-lived per invocation — no long-held connections — so contention is minimal even with overlapping `bb capture` runs. Verify the chosen sqlite crate has WAL.
- **Failed captures:** append a JSONL row to `~/.bb/capture-errors.jsonl` (mirror the existing `agent-session-submit-errors.jsonl` pattern in `auth.rs:404-433`) and continue.

## 9. Phased rollout

| Phase | Scope | Depends on |
|---|---|---|
| 1 | `bb db path`, `bb db query`, `bb capture events` | sqlite + DDL only |
| 2 | `bb steering log/list/get/update/scan/search` | sqlite + steering DDL; unblocks soft-dependency in `steering-capture` and `steering-review` skills |
| 3 | `bb capture diffs` | `git` available on PATH (or `git2`) |
| 4 | `bb capture pr-comments` + `bb retrospective pr-data/record/list/get` | `gh` available + authenticated |
| 5 | Stop-hook integration via `--capture-diffs` / `--capture-pr-comments` | Phases 3-4 |
| 6 (later) | Auto-detection of steering signals (`steering-detect` skill + `bb hook stop --queue-steering-detect`) | Phase 1 (`events` table); LLM access in skills |
| 7 (later) | Server-side mirror; `pr_diffs` table; `bb db prune` | Real consumer demand |

Each phase ships independently. Skills in BB-Skills already work via direct file I/O today; they progressively gain faster paths as phases land:

- After **Phase 2**: `steering-capture` / `steering-review` delegate to `bb steering` instead of grepping notes.
- After **Phase 4**: `pr-review-retrospective` calls `bb retrospective pr-data` instead of shelling out to `gh` itself.
- After **Phase 6**: a new `steering-detect` skill captures corrections without manual invocation.

## 10. References

- `bbapp/packages/apps/cli/src/main.rs` — subcommand structure (lines 73-96)
- `bbapp/packages/apps/cli/src/types.rs` — `CanonicalAgentEvent` (lines 32-44), `AgentSessionUpsertInput` (lines 48-74)
- `bbapp/packages/apps/cli/src/providers.rs` — Codex parser (lines 262-497), Claude parser (lines 651-837)
- `bbapp/packages/apps/cli/src/auth.rs` — HTTP client + error log pattern (lines 404-454)
- `bbapp/packages/apps/cli/src/git.rs` — git/PR metadata resolution (lines 15-75)
- `bbapp/packages/apps/cli/src/paths.rs` — `~/.bb/`, `~/.codex/sessions/`, `~/.claude/projects/` layout (lines 12-59)
- `bbapp/packages/apps/cli/src/hooks.rs` — Stop hook installer (lines 14-163)

Verify line numbers before implementing — they are accurate as of 2026-05-07 but may drift.
