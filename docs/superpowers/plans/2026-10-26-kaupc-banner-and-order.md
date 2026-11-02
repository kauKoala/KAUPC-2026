# KAUPC Banner and Order Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the whitespace-sensitive KAUPC banner problem and reorder KAUPC A~K without losing source packages.

**Architecture:** The new A package owns its statement, Python reference, exhaustive data and exact-output validator. Existing packages move as whole directories; manifest labels, shared pointers and statement eyebrow labels move with them. A global markup test prevents a later reintroduction of italic variable markup.

**Tech Stack:** Python 3, HTML, YAML, DOMjudge problem package, PowerShell/Docker provisioner.

---

### Task 1: Establish regression expectations

**Files:**
- Create: `tests/test_statement_markup.py`
- Create: `problems/contests/KAUPC/A/tests/test_solution.py`

- [ ] Write tests that require every contest statement to contain no `<var>` tags and require the banner reference output to retain leading and trailing spaces.
- [ ] Run the tests and confirm they fail because the markup and A package do not yet exist.

### Task 2: Add the new A package

**Files:**
- Create: `problems/contests/KAUPC/A/`
- Modify: `problems/contests/KAUPC/problems.yaml`

- [ ] Create the package through `scripts/new-problem.ps1` with id `wavingbanner` and name `현수막 출력하기`.
- [ ] Implement statement, reference source, exact-output validator, exhaustive tests and all 41 cases.
- [ ] Run package tests and build its DOMjudge archive.

### Task 3: Move existing packages to B~K

**Files:**
- Rename: existing KAUPC source folders and shared pointer folders
- Modify: `problems/contests/KAUPC/problems.yaml`
- Modify: shared `source.txt` files and statement eyebrows

- [ ] Move whole source packages to the approved order and update every label reference.
- [ ] Run layout and archive checks for every KAUPC package.

### Task 4: Apply statement typography

**Files:**
- Modify: all `problems/contests/**/problem_statement/problem.html`
- Modify: `custom/css/contest-portal.css`

- [ ] Replace `<var>` with `<code>` in statements, including shared TEST sources.
- [ ] Convert A/E fixed terms and A case labels to code/caption presentation.
- [ ] Run the markup regression test.

### Task 5: Deploy and verify

**Files:**
- Generated: `build/problem.zip` (not committed)

- [ ] Run all package tests, build all KAUPC archives and sync the provisioner.
- [ ] Push branch, open and merge PR, wait for deployment.
- [ ] Verify A~K order and the new A statement through the participant UI.
