# Contributing to BB-Skills

Thanks for your interest in contributing. This guide covers the main ways to contribute: adding skills, adding platform adapters, testing, and submitting pull requests.

## Adding a new skill

1. Choose the pack your skill belongs to (`core`, `spec-workflow`, or `testing`) or propose a new pack.
2. Create a directory under `skills/<pack>/<skill-name>/`.
3. Write a `SKILL.md` file in that directory. This is the canonical skill definition -- adapters transform it into platform-specific formats.
4. Update the pack's `pack.yml` to include your new skill.
5. Add a one-line entry to the skill reference table in `README.md`.

### SKILL.md structure

A skill file should contain:

- A clear title and one-line description
- The full prompt/instructions the AI agent will follow
- Any required context, constraints, or output format expectations

Look at existing skills in `skills/spec-workflow/` for examples.

## Adding a new platform adapter

Adapters live in `bb_skills_adapters/` and convert `SKILL.md` files into platform-specific formats.

1. Create a new file in `bb_skills_adapters/` (e.g., `my_platform.py`).
2. Extend `BaseAdapter` from `bb_skills_bb_skills_adapters/base.py`.
3. Implement the required methods for transforming skill content into your platform's format.
4. Register the adapter so the CLI can discover it.
5. Add the platform to the support matrix in `README.md`.

See `bb_skills_bb_skills_adapters/claude.py` or `bb_skills_bb_skills_adapters/cursor.py` for reference implementations.

## Testing

Run the test suite with:

```bash
pytest
```

When adding a new skill or adapter, include tests that verify:

- The skill file is valid and parseable
- The adapter produces correct output for the target platform
- Edge cases (missing fields, empty content) are handled

## Pull request guidelines

- **One skill per PR.** Keep changes focused -- do not bundle unrelated skills or adapters.
- **Include tests.** PRs without test coverage for new functionality will be asked to add them.
- **Update docs.** If your change affects user-facing behavior, update `README.md` accordingly.
- **Write a clear description.** Explain what the skill does, why it is useful, and how to verify it works.
- **Disclose AI assistance.** If you used AI tools to write your contribution, mention it in the PR description.

## Development setup

1. Clone the repository.
2. Install dependencies: `pip install -e ".[test]"`
3. Run tests: `pytest`
4. Make your changes on a feature branch and open a PR against `main`.
