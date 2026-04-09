# SlideKit for Codex

This repository supports both Claude Code and Codex.

- Keep all files under `skills/` intact. They are the Claude Code workflow layer.
- For Codex, use this `AGENTS.md` as the execution guide.
- Treat `builder/` as the source of truth for the local generation pipeline.

## Goal

Generate SlideKit HTML decks, reviewable JSON intermediates, and optional poster output without modifying the Claude-specific files.

## Core Architecture

- `builder/`
  - Local Python pipeline for scanning inputs and generating output
  - Key modules: `cli.py` (entry point), `slidekit_builder.py` (main builder), `plan_exporter.py` (JSON export), `patterns.py`, `themes.py`
- `skills/slidekit-create/`
  - Claude-specific interactive deck creation workflow
- `skills/slidekit-build/`
  - Claude-specific paper-to-slide planning workflow
- `skills/slide-check/`
  - Claude-specific browser review workflow
- `slide_reviewer.html`
  - Local reviewer for `slide_plan.json` and `slide_content.json`
- `slide-templates/`
  - Reusable HTML template references

## Codex Operating Rules

- Do not delete, rename, or rewrite Claude-specific files unless explicitly asked.
- Prefer the local CLI over reimplementing generation logic.
- Prefer `slide_content.json` and `slide_plan.json` as stable handoff formats.
- When the user wants interactive questioning, keep it minimal and compress it into as few turns as possible.
- When enough input is already available, proceed directly instead of recreating Claude's phase-by-phase interview.

## Recommended Codex Flows

### 1. Fast local generation

Use when the user already has a PDF, text file, folder input, or `slide_plan.json`.

```bash
python -m builder <input>
```

Examples:

```bash
python -m builder paper.pdf
python -m builder notes.md
python -m builder input_folder
python -m builder slide_plan.json
```

### 2. Export intermediate files first

Use when the user wants to inspect or edit the structure before HTML generation.

```bash
python -m builder paper.pdf --export-plan
python -m builder paper.pdf --export-md
python -m builder paper.pdf --export-content
```

All three options export **both** `slide_plan.json` and `slide_content.json`. The difference is what else is included:

- `--export-plan` / `--export-content`
  - `slide_plan.json` — Builder-oriented plan with slide `type`
  - `slide_content.json` — Content-oriented payload without fixed layout types
- `--export-md` (adds Markdown on top of both JSONs)
  - `slide_plan.json` + `slide_content.json` (same as above)
  - `content.md` — Markdown export for manual refinement

### 3. Codex-friendly remake flow

Use this instead of trying to replicate Claude's full multi-phase skill workflow.

1. Export from the source material.
2. Let the user edit `slide_content.json` or `content.md` if needed.
3. If a final `slide_plan.json` exists, run `python -m builder slide_plan.json`.
4. If only `slide_content.json` exists, use it as the design/content brief and create or update a compatible `slide_plan.json` before building.

### 4. Poster generation

```bash
python -m builder paper.pdf --poster
python -m builder paper.pdf --poster --size a1
```

## Review Guidance for Codex

Claude uses `/slide-check` with `agent-browser`. Codex should not depend on that workflow.

Preferred alternatives:

- Review `index.html` and generated slide HTML directly
- Use local screenshots or browser automation only if available
- Use `slide_reviewer.html` for JSON-level review before final HTML generation

## Template Guidance

- Reuse `slide-templates/` and files under `skills/slidekit-create/references/` as reference material
- Do not assume Claude-specific template discovery paths such as `~/.claude/...`
- If template reuse is needed for Codex, copy or reference templates from this repository directly

## Prompting Guidance

When the user asks Codex to build slides, prefer collecting this information up front:

- input file or folder
- output directory, if fixed
- language
- theme or visual direction
- whether they want direct HTML generation or editable intermediate JSON first
- whether poster output is required

If any of those are missing, infer the safe defaults:

- language: Japanese
- mode: generate intermediate JSON first for ambiguous research inputs
- output: builder default timestamped output directory

## Non-Goals

- Do not try to emulate Claude slash commands literally
- Do not rewrite `SKILL.md` files into Codex-native format
- Do not replace the builder with a new implementation unless explicitly requested
