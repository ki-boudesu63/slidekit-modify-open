# SlideKit for Codex

This repository supports both Claude Code and Codex.

- Keep all files under `skills/` intact. They are the Claude Code workflow layer.
- For Codex, use this `AGENTS.md` as the execution guide.
- The default Codex behavior for paper-to-slide work is interactive.

## Goal

Mirror the intent of Claude's `slidekit-build` workflow without deleting or rewriting the Claude-specific assets.

The intended flow is:

1. read the paper or source material
2. extract important text and figure candidates
3. have the AI design the slide structure
4. have the AI create `slide_plan.json` and `slide_content.json`
5. review the JSON
6. render HTML with `builder/`

This also includes the `slidekit-create` stage:

7. use `slide_content.json` as design input
8. interactively decide visual direction
9. generate the final slide HTML set

## Core Architecture

- `skills/slidekit-build/`
  - Claude-specific interactive paper-to-slide workflow
- `skills/slidekit-create/`
  - Claude-specific interactive deck creation workflow
  - Also the reference specification for Codex's create-stage behavior
- `skills/slide-check/`
  - Claude-specific browser review workflow
- `builder/`
  - Local renderer and export pipeline used after JSON is ready
- `slide_reviewer.html`
  - Local reviewer for `slide_plan.json` and `slide_content.json`
- `slide-templates/`
  - Reusable HTML template references

## Codex Operating Rules

- Do not delete, rename, or rewrite Claude-specific files unless explicitly asked.
- Default to an interactive conversation when the user asks to turn a PDF or paper into slides.
- Default to an interactive conversation when the user asks to turn `slide_content.json` or structured content into slides.
- Do not treat `python -m builder <pdf>` as the primary paper-to-slide workflow.
- For paper-to-slide work, the AI should first understand the content and create JSON itself.
- Use `builder/` mainly after `slide_plan.json` is finalized.
- `slide_plan.json` and `slide_content.json` are the main handoff formats between planning and rendering.
- Keep the conversation efficient, but do not skip necessary clarification when slide structure depends on user intent.
- Codex should be able to handle both stages:
  - `slidekit-build` equivalent: paper -> JSON
  - `slidekit-create` equivalent: JSON/content -> final HTML

## Preferred Codex Workflow

### 1. Interactive paper-to-slide mode

This is the default when the user asks to turn a PDF or document into slides.

1. Read the source material.
2. Extract key sections, findings, and figure candidates.
3. Ask the user the minimum necessary interactive questions.
4. Design the slide outline.
5. Create `slide_plan.json`.
6. Create `slide_content.json`.
7. Let the user review or revise the JSON.
8. Run the renderer:

```bash
python -m builder slide_plan.json
```

### 2. JSON-first review mode

Use when the user wants to inspect structure before rendering.

- create or update `slide_plan.json`
- create or update `slide_content.json`
- review with `slide_reviewer.html` or direct file editing
- render only after review is complete

### 3. Interactive create mode

This is the default when the user provides `slide_content.json`, structured notes, or asks for deck creation from prepared content.

1. Read `skills/slidekit-create/SKILL.md` as the behavioral reference.
2. Treat that file as a specification, not a directly executable slash command.
3. Interactively confirm only the minimum required items such as:
   - language
   - deck style
   - theme direction
   - target audience
   - number of slides
4. Use `slide_content.json` as the primary content payload.
5. Recreate the intent of `slidekit-create` in Codex:
   - choose slide patterns
   - assign content to slides
   - generate `001.html` to `NNN.html`
   - generate `index.html`
6. If useful, also update or regenerate `slide_plan.json` as the rendered plan.

### 4. Renderer-only mode

Use only when the user already has a finalized `slide_plan.json`.

```bash
python -m builder slide_plan.json
```

### 5. Poster mode

Use when the user explicitly wants a poster after the plan is ready.

```bash
python -m builder slide_plan.json --poster
python -m builder slide_plan.json --poster --size a1
```

## PDF Extraction Guidance

For PDF input, the intended flow is:

1. extract text and figures from the PDF
2. have the AI interpret that content
3. have the AI build the slide structure
4. have the AI author the JSON

The extraction step is preparation, not the final planning step.

`builder` helper commands may still be used as support tooling when helpful, but they are secondary to the AI-led planning flow.

## slidekit-create Guidance for Codex

Codex cannot directly invoke Claude slash commands such as `/slidekit-create`.

However, Codex should still support the create stage by using:

- `skills/slidekit-create/SKILL.md` as the workflow specification
- `skills/slidekit-create/references/patterns.md` as the layout reference
- `skills/slidekit-create/references/index-template.html` when useful
- `slide_content.json` as the primary structured content input

In other words:

- direct slash-command execution: not available
- functional reproduction of the workflow: expected and supported

## Review Guidance for Codex

Claude uses `/slide-check` with `agent-browser`. Codex should not depend on that workflow.

Preferred alternatives:

- review `slide_plan.json` directly
- review `slide_content.json` directly
- use `slide_reviewer.html` for JSON-level review
- render HTML and inspect `index.html` only after the JSON is acceptable

## Template Guidance

- Reuse `slide-templates/` and files under `skills/slidekit-create/references/` as reference material.
- Do not assume Claude-specific template discovery paths such as `~/.claude/...`.
- If template reuse is needed for Codex, reference templates from this repository directly.

## Prompting Guidance

When the user asks Codex to build slides, start in interactive mode and collect:

- input file
- output preference
- language
- slide deck vs poster
- target audience
- desired level of detail
- whether they want a conservative academic summary or a presentation-optimized restructuring

If the user gives only a PDF and no further direction, assume:

- language: Japanese
- mode: interactive paper-to-slide
- output: JSON review first, then render
- style: presentation-optimized but faithful to the paper

## Command Model

Codex does not have Claude-style slash command registration in this repository.

- There is no `/slidekit-build` registration layer here.
- There is no `/slidekit-create` registration layer here.
- Use this `AGENTS.md` plus normal prompts and local commands instead.
- Treat "please make slides from this paper" as the trigger for the interactive build workflow.
- Treat "please make slides from this `slide_content.json`" as the trigger for the interactive create workflow.

## Non-Goals

- Do not try to emulate Claude slash commands literally.
- Do not rewrite `SKILL.md` files into Codex-native format.
- Do not replace the builder with a new implementation unless explicitly requested.
