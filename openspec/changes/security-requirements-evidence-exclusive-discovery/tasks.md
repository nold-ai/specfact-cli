# Tasks: security-requirements-evidence-exclusive-discovery

## 1. Specification and failing evidence

- [x] 1.1 Add the exclusive-discovery security delta.
- [x] 1.2 Add focused regressions for project-module shadowing and gate environment isolation.
- [x] 1.3 Run the focused regressions against HEAD and record failing-before evidence.

## 2. Implementation

- [x] 2.1 Make exclusive discovery retain bundled modules and explicit fixture roots only.
- [x] 2.2 Enable exclusive discovery in the local evidence adapter and pull-request workflow.

## 3. Verification

- [x] 3.1 Run focused tests and record passing-after evidence.
- [x] 3.2 Run required formatting, typing, linting, YAML, security, and changed-scope review gates.
- [x] 3.3 Validate the OpenSpec change strictly.
- [x] 3.4 Update the internal wiki mirror and graph when the sibling checkout is available; otherwise record the follow-up.
