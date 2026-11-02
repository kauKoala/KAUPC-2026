# Adding Bridges Problem Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a version-controlled DOMjudge package for `다리 추가하기` that can be tested without a running contest database.

**Architecture:** Keep the problem statement, Python reference solution, deterministic test generator, generated `.in/.ans` fixtures, and package metadata in `problems/addingbridges`. A Python unittest suite invokes the reference executable and checks representative answers; DOMjudge imports the resulting ZIP as a runtime copy.

**Tech Stack:** Python 3 standard library, DOMjudge/ICPC problem-package layout, PowerShell archive helper.

---

### Task 1: Reference solution regression test

**Files:**
- Create: `problems/addingbridges/tests/test_solution.py`
- Create: `problems/addingbridges/submissions/accepted/solution.py`

- [ ] **Step 1: Write a test that invokes the missing Python solution with a disconnected graph, a useful bridge, and a duplicate edge.**
- [ ] **Step 2: Run `python -m unittest problems/addingbridges/tests/test_solution.py -v` and confirm it fails because `solution.py` is absent.**
- [ ] **Step 3: Implement Floyd-Warshall initialization and `O(N^2)` edge-addition updates in `solution.py`.**
- [ ] **Step 4: Re-run the unittest and confirm it passes.**

### Task 2: Reproducible problem package

**Files:**
- Create: `problems/addingbridges/problem.yaml`
- Create: `problems/addingbridges/domjudge-problem.ini`
- Create: `problems/addingbridges/problem_statement/problem.html`
- Create: `problems/addingbridges/generators/generate_tests.py`
- Create: `problems/addingbridges/data/sample/1.in`
- Create: `problems/addingbridges/data/sample/1.ans`
- Create: `problems/addingbridges/data/secret/*.in`
- Create: `problems/addingbridges/data/secret/*.ans`

- [ ] **Step 1: Add package metadata and a Korean statement that matches the supplied constraints.**
- [ ] **Step 2: Add a deterministic generator that writes targeted test inputs and obtains answers by running the reference solution.**
- [ ] **Step 3: Generate fixtures and run every fixture through the reference solution, comparing stdout to its `.ans` file.**

### Task 3: Team-facing build and DB-import boundary documentation

**Files:**
- Create: `problems/addingbridges/README.md`
- Create: `scripts/build-problem.ps1`
- Create: `docs/problem-storage-and-import.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Document the exact source-controlled files and the separate runtime records created by DOMjudge import.**
- [ ] **Step 2: Add a build command that creates `dist/addingbridges.zip` from the package without including local tests or generated caches.**
- [ ] **Step 3: Run the complete unittest suite, generate fixtures, build the ZIP, and inspect its entries.**
- [ ] **Step 4: Commit and push the tested package.**
