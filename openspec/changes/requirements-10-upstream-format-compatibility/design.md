# Design: Refresh native upstream artifact compatibility

## Ownership and public boundary

Core owns shared profile recognition, parsing/readiness contracts and pinned fixture metadata. Modules owns command persistence and signed runtime acceptance.

Use existing Bridge Adapter, plugin registration and requirement/evidence extension surfaces. Keep producer-original records separate from normalized presentation. Parsing and digest evaluation are side-effect free; runtime adapters own invocation, filesystem snapshots and explicitly selected external access. No new graph engine, hosted service or unrestricted shell runner is introduced.

## Decisions

### Pinned upstream artifact profiles

The adapter SHALL test pinned Spec Kit v1.1.0 fixtures alongside retained v0.12.18 and supported OpenSpec fixtures. Fixture metadata SHALL identify upstream tag/commit, artifact paths and content digests. Support SHALL be evaluated from the effective artifact profile, including enabled known extensions and template resolution, rather than inferred from Markdown or a claimed CLI version. The supported profile allowlist SHALL be explicit and versioned; unknown or unsupported custom profiles SHALL be rejected with an actionable diagnostic.

### Extension coexistence and atomic import

A supported SpecFact extension that only adds invocation hooks SHALL NOT by its presence invalidate a supported native artifact profile. An extension that alters artifact templates SHALL require a tested effective profile. Import and readiness validation SHALL complete before persistence; any profile, parse or readiness failure SHALL leave existing imported state unchanged. Import SHALL remain offline and SHALL NOT execute upstream scripts, fetch templates or rewrite upstream inputs.

## Dependencies and rollout

No new runtime prerequisite on #740. Modules counterpart consumes the released shared profile contract; retain legacy native import. Follow up on closed core #350/modules #168 rather than reopen them.

Start additive behavior in shadow/advisory mode where appropriate. Preserve independent required checks. Review exact core/module version and signed payload identities before adoption. Roll back by disabling optional context/hooks/projection or restoring the prior compatible signed pair; retain reports with their original schema, statuses and limitations.

## Verification boundaries

Every spec scenario becomes an independently meaningful fixture or integration assertion before behavior changes. Test negative identities, missing/ambiguous input and source preservation rather than merely mirroring data classes. Reports of planning inspection do not claim execution. Use pytest structured identities first and declare unsupported platforms/producers explicitly.
