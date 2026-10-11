# Deferred dependency inventory follow-up

PR #748 inherits the approved five-PR stack and its current scope, tests and
proof without changing them. This follow-up preserves the historical inventory
and audit record from 21 September 2026. Its package candidates are not a current
upgrade instruction or executable artifact review.

After #753 is integrated, retarget this planning follow-up to dev and refresh the
remaining inventory under #747 with fresh artifact/advisory/compatibility review.
JSON 3 and unselected Python/Ruby upgrades remain deferred. Keep #747 and the
active OpenSpec change open until the broader accepted tasks complete. No new
production dependency, release version, verifier policy or fixture pin is changed.

Reconciled on 11 October 2026 after protected policy #3 and core #758 merged.
The inherited native five-PR stack is #757, with root baseline
30f98cc14e074802a9f21c6b84e69e743eee6442 and final top
53f531c2fb640c968e3d6f7612ec7c1d2422aa3b. The required version gate selects
one 0.55.6 consolidated bugfix release after protected dev reserved 0.55.5.
This branch stays a planning follow-up, outside the five native stack members.
The owner requested all five dependency PRs remain unmerged.
