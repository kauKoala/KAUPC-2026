# Problem Editor QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make problem authoring data generation inspectable and bounded, serialise verification, and restore the statement preview.

**Architecture:** `tools/problem-editor/app.py` remains the single authoring application. The generator persists structured settings and generated-data metadata alongside the package; rendering reads that metadata. Preview becomes server-rendered content within the authoring document so it does not create a separately authenticated frame request.

**Tech Stack:** Python standard library HTTP server, unittest, DOMjudge provisioner.

---

### Task 1: Add failing editor behavior tests

**Files:**
- Create: `tests/test_problem_editor.py`
- Modify: `tools/problem-editor/app.py`

- [ ] Add tests asserting that generated cases are written only to `data/secret`, seed records expose input and output, and verification records serial order.
- [ ] Run `python -m unittest tests.test_problem_editor -v` and confirm the assertions fail before implementation.

### Task 2: Replace generator code editing with controlled generation

**Files:**
- Modify: `tools/problem-editor/app.py`
- Test: `tests/test_problem_editor.py`

- [ ] Add a settings parser for integer lower/upper bounds and seed lines.
- [ ] Generate input from each seed into `data/secret`, invoke the MAIN answer once per input, and persist displayed metadata.
- [ ] Remove the example/secret selector from the generator form and render generated cases with seed, input, and answer previews.
- [ ] Run the focused tests and commit the isolated change.

### Task 3: Make preview and verification safe

**Files:**
- Modify: `tools/problem-editor/app.py`
- Test: `tests/test_problem_editor.py`

- [ ] Render the statement preview directly in the editor page instead of through an iframe.
- [ ] Keep `verify_package` explicitly serial and include execution order in its result table.
- [ ] Run focused and full regression tests, then commit.

### Task 4: Deploy and exercise the flow

**Files:**
- No source changes expected.

- [ ] Create data through the browser, verify the generated content view, run sequential validation, publish, and submit as a participant.
- [ ] Record UX findings from the end-to-end run.
