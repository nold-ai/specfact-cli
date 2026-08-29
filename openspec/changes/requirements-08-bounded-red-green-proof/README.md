# Requirements 08: Bounded Red-Green Proof

> **Parked 2026-08-29 — superseded, not implemented.** Core issue #675 and paired modules issue #414 were closed as Not Planned. The accepted direction is the cheaper seal-bound risk/test-intent plus implementation-checkpoint loop in preflight #682/#684 and modules #431/#434. This folder is preserved for history and was not archived, so none of its delta specifications were merged into canonical specs.

This change defines a protocol for proving one bounded historical statement by replaying exact selectors at an explicit red commit R, a green implementation checkpoint H, and the delivered head D. B, R, and H remain the three proof commits; D binds the proof to what is actually delivered and permits only named post-green evidence bookkeeping.

Planning only: no runtime behavior is implemented on this branch.
