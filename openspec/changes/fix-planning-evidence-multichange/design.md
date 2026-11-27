# Design

Retain the existing path-based maturity classifier. Guard implementation review-record selection with `planning_maturity != planned`. Producer, fresh consumer, and final verifier must agree so optional or unrelated approval records cannot alter planning reports or plan identity.

The existing planning validator remains authoritative for completeness; independently recomputed plans must still match. Above planned maturity, retain the one-active-change restriction and existing approval, test, provenance, and final verification. Promotion reuse keeps its independent trusted verification and must not fall through to ordinary planning success.

Regression tests execute the actual shell selection blocks extracted from workflow YAML with planning and implementation scopes. They cover multiple changes, a single change without approval, unrelated approval records, implementation rejection, and retained implementation selection. Existing workflow tests protect promotion and artifact trust. No new runtime helper or public interface is introduced.
