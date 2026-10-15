# Tasks: fix-categoryless-module-command-squatting

## TDD / SDD order (enforced)

Specification deltas precede scenario-derived tests; tests must fail on vulnerable HEAD before production code changes.
Production code is implemented only after failing evidence is recorded.

## 1. Worktree and readiness

- [x] 1.1 Confirm work occurs on a non-protected branch in an attached git worktree.
- [x] 1.2 Verify the vulnerability against current registration code and check for overlapping active OpenSpec scope.
- [x] 1.3 Create and link public GitHub issue #718 under module-security feature #352 with required labels.
- [x] 1.4 Validate this change strictly before implementation.
- [x] 1.5 Verify current issue #718 project/Todo, parent #352, labels and empty native dependency lists; earlier
project-access block is resolved.
- [x] 1.6 Update `specfact-cli-internal/wiki/sources/fix-categoryless-module-command-squatting.md` and rebuild the
internal wiki graph when the sibling checkout is available.

## 2. Specification and failing evidence

- [x] 2.1 Add delta scenarios for fail-closed grouped mode and explicit legacy compatibility.
- [x] 2.2 Add focused registry tests derived from both scenarios.
- [x] 2.3 Run the focused tests against vulnerable HEAD and record failing-before evidence.

## 3. Implementation

- [x] 3.1 Skip unverified category-less workspace registration in grouped mode, preserving the authenticated
  official-bundle exception (including specfact-project); reserve permanent core commands for resolved built-in paths
  in both modes.
- [x] 3.2 Preserve categorized routing, non-project legacy sources and explicit unreserved flat registration.

## 4. Verification and documentation review

- [x] 4.1 Run focused registry and category-routing tests and record passing evidence. The reviewed runtime has
  3,430 local passes and native100 GREEN38687870204 at signed e4db7795; later documentation-head gates remain separate.
- [x] 4.2 Run formatting, type, lint, YAML, contract, smart-test, Semgrep, and Bandit gates required for the touched
  scope. Final runtime evidence and unchanged-input contract reuse are recorded in TDD_EVIDENCE.md; new exact-head
  hosted checks remain required. The 17 unchanged protected YAML diagnostics and launcher limitation remain disclosed.
- [ ] 4.3 Refresh `.specfact/code-review.json`, resolve all findings, and record the result. Runtime FULL72 has
  30 exact existing nonblocking findings and zero additions. This documentation correction needs its own exact-head
  checks and completed review; the unresolved companion release-symlink annotation also prevents closure.
- [x] 4.4 Review `README.md`, `docs/`, `docs/index.md`, and sidebar navigation for impact; update only if documented
  behavior changes. The runtime commit updates the affected module category/security references.
- [x] 4.5 Confirm no signed module assets or manifests changed; otherwise bump and re-sign affected modules and run
  signature verification. The core artifact admission code changes no signed bundle assets or cryptographic format.
- [x] 4.6 Validate the OpenSpec change strictly after implementation; repeat after this documentation reconciliation.

## 5. Release and pull request

- [x] 5.1 Apply the required patch version bump across canonical version files and add a Security changelog entry.
- [x] 5.2 Commit with a Conventional Commit message and push the branch. Signed implementation e4db7795 is published.
- [x] 5.3 Create a pull request to `dev` using the repository template and link the OpenSpec change and GitHub issue.

## Post-merge cleanup

- [ ] Archive the completed change with `openspec archive fix-categoryless-module-command-squatting` after merge.
- [ ] Remove the implementation worktree and prune the local branch after merge.

## 6. Current review corrections

- [x] 6.1 Extend spec deltas before tests for official category roots and rejected-package import isolation.
- [x] 6.2 Capture actual failing tests against facb690 before implementation.
- [x] 6.3 Record human acceptance of mapping a9ba0dfd and corrected native authored RED (run 38176059675); final
e550f23e acceptance/proof remains tracked by 6.7.
- [ ] 6.4 Reject packages before all registration side effects and preserve effective built-in discovery.
- [ ] 6.5 Run focused/full/quality gates, restack, and verify final current-head review and Requirements.

- [x] 6.6 Add executable reserved-flat-name controls and reconcile the ended spec shim requirement.
- [ ] 6.7 Obtain exact final mapping acceptance, regenerate authored/final proof after prerequisite #760, and validate
the final stack.

- [ ] 6.8 Reproduce category-builder imports during eligibility and use the existing static category map before side
effects.

## 7. Protected-base validation cycle after #761

- [x] 7.1 Refresh protected dev and capture all existing stack heads and the approved candidate.
- [x] 7.2 Preserve owner acceptance for exact mapping e550f23e; record earlier validation as historical.
- [ ] 7.3 Publish signed specification and authored tests before implementation; retain fresh native RED.
- [ ] 7.4 Restore the approved security correction, synchronize 0.55.8 artifacts, and verify final exact-head gates.
- [ ] 7.5 Restack both planning children, issue authorized signed-head grants and validate scoped-token proof reuse.
- [ ] 7.6 Resolve only validated findings and leave the final three PRs unmerged.

## 8. Protected-base cycle after #767

- [x] 8.1 Verify protected merge c6af68a0 and retain previously green heads as historical evidence.
- [ ] 8.2 Publish signed specification and unchanged accepted tests; retain genuine current-base native RED.
- [ ] 8.3 Restore the accepted guard, synchronize 0.55.9 and validate all current-head required gates.
- [ ] 8.4 Restack both planning children and verify independent protected-context proof reuse.
- [ ] 8.5 Close only verified findings and leave all three target PRs unmerged.

## 9. Protected-base cycle after #768

- [x] 9.1 Verify protected merge daefe0c7, preserve captured heads and exact E550 owner acceptance,
  restate signed specification and keep all earlier-base evidence historical.
- [x] 9.2 Publish accepted controls, document their intent without logic changes, and retain fresh native RED.
- [ ] 9.3 Restore approved guards, synchronize available bugfix0.55.10, and pass all local/current-head gates.
- [ ] 9.4 Sequentially restack #743/#751 and verify independent protected-context proof reuse.
- [ ] 9.5 Resolve only validated findings and leave all three target PRs unmerged.

## 10. Authenticated project bundle compatibility

- [x] 10.1 Verify the supported project installer and all six official artifact signatures; capture reviewed f8ffe7c6.
- [x] 10.2 Specify strict authenticated project-root admission before adding controls or production changes.
- [x] 10.3 Author paired official-artifact and forgery controls; retain genuine regression and protected-base RED.
- [x] 10.4 Implement strict pinned-key admission, retain unsigned/core/import boundaries and pass local gates.
- [x] 10.5 Obtain exact amended mapping acceptance and publish signed authored/native RED before final production.
- [ ] 10.6 Validate final current-head execution, review, authority and required checks before resolving the finding.

## 12. Admission proof and executable coverage review

- [x] 12.1 Specify executable payload coverage before adding cache/bytecode controls.
- [ ] 12.2 Strengthen existing-loader and schema/bridge controls and map the public import-free admission probe.
- [ ] 12.3 Reproduce unsigned cache execution and protected-base failures before implementation.
- [ ] 12.4 Preserve authentic compiled-source caches while denying uncovered executable artifacts.
- [ ] 12.5 Obtain exact amended mapping acceptance; regenerate signed native RED/final proof and full review.

- [ ] 12.6 Prove source-swap, omitted native-format and valid-app cache failures before snapshot implementation.
- [ ] 12.7 Authenticate captured source before standard compiler work and preserve all SAST rules.
- [ ] 12.8 Reverify the fix and independent findings on final test/source hashes before native publication.

- [ ] 12.9 Reproduce same-name project shadow rejection hiding actual installed roots and dependents through public discovery.
- [ ] 12.10 Reproduce payload verification for disabled project roots with stored-state and explicit override controls.
- [ ] 12.11 Select first enabled authorized candidate before sorting; retain ordinary discovery and admitted dependency views.
- [ ] 12.12 Revalidate final exact mapping, full suite, native proof and completed review before declaring #719 merge-ready.

- [ ] 12.13 Reproduce real discovery-to-verification manifest replacement for schema, bridge, command and version fields.
- [ ] 12.14 Bind whole normalized registration metadata to the same authenticated canonical manifest snapshot.
- [ ] 12.15 Revalidate exact amended mapping and all native/local/hosted gates before declaring root merge-ready.

- [ ] 12.16 Reproduce executable addition/replacement after real signature verification but before admission finishes.
- [ ] 12.17 Enforce authenticated executable membership/content rather than signing-filter eligibility alone.

- [ ] 12.18 Reproduce executable insertion/replacement during genuine cache reproduction and observe transient effects.
- [ ] 12.19 Reproduce caches before the final compiler-free executable inventory check; move final authority before effects.

## Indirect category review follow-up

- [ ] Reproduce bundle-induced mounts and existing-root replacement through public registration.
- [ ] Bind indirect category capabilities to authenticated project authority before effects.
- [x] Extend native-format controls for `.so` and `.pyd` and retain clear required fixture diagnostics.
- [ ] Revalidate full delivery, canonical mapping acceptance and exact-current native RED/GREEN/review.

## Alternate-manifest review follow-up

- [ ] Reproduce actual YAML parser escape through public registration in both grouping modes.
- [ ] Normalize parser failure at canonical payload serialization and verify denial/legitimate compatibility.
- [ ] Revalidate final source mapping, complete quality/security checks and exact native proof before publication.

## Review follow-up: complete candidate eligibility

- [x] Specify full local eligibility and coherent dependency selection before new tests.
- [ ] Reproduce actual compatible fallback and dependency-version failures through public registration, including genuine signatures.
- [ ] Compare candidate designs and implement the smallest coherent selection boundary without registration effects.
- [ ] Verify fresh exact test bytes, full gates, standalone verify-fix, then model-diverse interrogation.
- [ ] Recompute canonical mapping and request fresh owner acceptance only after concrete completed validation.

## Additional review coverage controls — 14 October 2026

Three current-head review annotations identify test oracles, not a demonstrated new production vulnerability.
Add a separate control file without altering the five accepted75 authored files. Verify that noncanonical project
publisher metadata has a valid signature under the test bundled trust anchor before asserting denial, isolating
canonical identity from checksum rejection. Map paired consistent-cycle compatibility with an ineligible priority
copy, preserving the existing healthy-cycle positive suite control. Observe the actual warning when conflicting
priority selections are refused; inactive modules alone do not establish an explicit diagnostic. Specifications
already require canonical publisher identity, consistent cycles and explicit bounded conflict refusal. These
strengthened controls require fresh exact mapping acceptance and signed/native reauthoring before publication.
No production behavior, pin, threshold, timeout, signature format or global dependency policy is expanded.

- [x] Validate valid-signature noncanonical publisher denial separately from checksum rejection.
- [x] Map consistent cycle compatibility paired with an ineligible priority override.
- [x] Validate the exact warning for contradictory priority refusal, including silent-warning mutation RED.
- [x] Record exact79 acceptance and verify signed native79 RED38628199251.
- [x] Verify final native79 GREEN38628713533/FULL72/all13 required integrations on the published head.

## Extensionless and identity review follow-up — 14 October 2026

- [x] Specify executable mode/header inventory and genuine-signature field coverage before new tests.
- [x] Reproduce extensionless excluded executable authority on the signed published head without executing it.
- [x] Verify canonical compatibility and valid-crypto noncanonical tier/category/group denial in both modes.
- [x] Implement inventory admission and complete full validation, standalone verify-fix then diverse interrogation.
- [x] Record exact93 acceptance and verify signed native93 RED38635629429 before implementation restoration.
- [x] Verify published059c native93 GREEN38636359296/FULL72/all13 required integrations.

## Individual execute-bit and Mach-O coverage — 14 October 2026

- [x] Specify separate coverage before tests, keeping all seven accepted93 files unchanged.
- [x] Prove each POSIX execute class and remaining six Mach-O encodings independently through public registration.
- [x] Complete exact-source full gates and standalone verification before diverse interrogation.
- [ ] Obtain fresh canonical mapping acceptance and signed native proof before publication.

## Historical accepted100 selector consolidation

- [x] Record native111 pre-JUnit limit failure and preserve authored2b2b/protected production.
- [x] Specify seven nodes covering all18 probe/mode observations before changing the eighth test file.
- [x] Verify all observations precede aggregate denial, isolated execute-bit/header mutations fail, protected100 RED and current100 GREEN.
- [x] Complete final full3420/FULL19score72/types0/1456 with unchanged inputs/graphs.
- [x] Complete final standalone verify-fix before diverse review on194bf bytes, no actionable findings.
- [x] Record actual exact4c3d mapping acceptance before signed/native100 publication.
- [x] Obtain signed native100 RED38647654283 with100 genuine assertion failures and all18 encoding observations before runtime restoration.
- [x] Verify published528b9338 native100 GREEN38648161680, all13 required integrations and current-head CodeRabbit5525712106.

## Project path-link and legacy native follow-up

- [x] Trace root and workspace-store links through actual discovery and retained loaders.
- [x] Capture genuine public failing controls for root and store links in both modes.
- [x] Correct the existing strict/project boundaries and preserve canonical workspace aliases.
- [x] Add explicit legacy coverage for all five omitted native suffixes.
- [x] Complete full gates and independent verification before a new exact canonical mapping review.
- [x] Obtain exact036 mapping acceptance and authentic signed native RED38687272103/GREEN38687870204.
- [ ] Complete the final documentation head checks/review and companion511 before merge readiness.

- [x] Specify final path reobservation after authentication and inventory before adding its regressions.
- [x] Reproduce links introduced inside verification, then verify final root/store reobservation and fallback.

- [x] Complete final3430 full tests, FULL72/30 with zero new findings, types, SAST, Bandit and exact-source installed-wheel matrix.
- [x] Complete standalone readonly verification before three diverse reviewers on final root/store reobservation.
- [x] Obtain exact036 path100 mapping acceptance before signed/native publication; actual djm81 record is retained.
