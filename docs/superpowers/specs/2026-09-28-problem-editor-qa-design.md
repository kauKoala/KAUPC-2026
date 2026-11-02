# Problem editor QA design

## Goal

Make the authoring flow usable without repository knowledge: a writer can inspect generated data, generate only judging data, and run verification without parallel execution spikes.

## Decisions

- Replace the exposed Python generator editor with a bounded form for the built-in integer generator: minimum, maximum, and one seed per line.
- Generation always writes `data/secret`; the UI does not expose an example-data mode.
- Store a per-test seed record with input and generated answer, and render it in the data table.
- Keep verification single-process: one submission is compiled and exercised across test cases before moving to the next submission. Add the execution order to the result.
- Render the preview in-process instead of an authenticated iframe. The iframe is redirected to DOMjudge login in a framed context and is therefore blocked by the login page's frame policy.

## Verification

- Unit-test URL generation and preview body rendering without an iframe.
- Unit-test generator validation, secret-only destination, and saved seed metadata.
- Unit-test verification order with subprocess calls stubbed at the module boundary.
- Run the existing portal regression suite and inspect the production authoring page after deployment.
