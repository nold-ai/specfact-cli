# Design: Preserve optional requirement decision context

## Ownership and public boundary

Core owns optional versioned records, shared parsing/validation and separate digest. Reuse plan.py Clarifications and preserve legacy plan hashes. Public parsing/hash APIs require beartype/icontract contracts.

Use existing Bridge Adapter, plugin registration and requirement/evidence extension surfaces. Keep producer-original records separate from normalized presentation. Parsing and digest evaluation are side-effect free; runtime adapters own invocation, filesystem snapshots and explicitly selected external access. No new graph engine, hosted service or unrestricted shell runner is introduced.

## Decisions

### Optional versioned decision context

The system SHALL provide a versioned RequirementDecisionContext companion to existing requirement inputs. Version 1 records SHALL retain stable record IDs, typed assumption/clarification-decision kinds, explicit disposition, original source references and source digests, and typed links to requirements, acceptance cases, components or ADRs. It SHALL reuse existing clarification question/answer/integration records rather than create a competing clarification workflow. Owner, review date and falsifying verification links SHALL remain optional in ordinary use. Records SHALL represent explicit source assertions only; unrecorded assumptions SHALL NOT be invented or claimed discovered.

### Separate decision context identity

Decision-relevant content SHALL have a separately versioned canonical digest over normalized IDs, kinds, dispositions, question/answer or assumption statements, typed links and explicit verification references. Source content digests SHALL bind the imported assertion to its original artifact. Historical session timestamps and other non-decision metadata SHALL NOT change the decision digest unless explicitly selected by policy. Legacy plan hashes SHALL remain unchanged and SHALL continue to exclude clarifications. A changed bound decision or source digest SHALL invalidate reuse of evidence that binds that context; an absent optional context SHALL NOT invalidate ordinary legacy evidence.

### Assertions and assurance authority remain distinct

Imported dispositions and answered_by/owner strings SHALL NOT authenticate approval. Ordinary evaluation SHALL report a touched unresolved recorded assumption as advisory. An explicitly selected assurance policy MAY require resolution, ownership, review date or verification links. Unavailable or ambiguous required evidence SHALL remain UNKNOWN; a reconciled behavioral contradiction SHALL remain FAIL. A trace link SHALL establish association only, not behavioral satisfaction or proof that unmapped behavior is absent.

## Dependencies and rollout

An additive core contract precedes module consumption. No dependency on seals, #247, #241 or #242. Compatibility and context are independently deliverable; each upstream context profile still requires fixtures.

Start additive behavior in shadow/advisory mode where appropriate. Preserve independent required checks. Review exact core/module version and signed payload identities before adoption. Roll back by disabling optional context/hooks/projection or restoring the prior compatible signed pair; retain reports with their original schema, statuses and limitations.

## Verification boundaries

Every spec scenario becomes an independently meaningful fixture or integration assertion before behavior changes. Test negative identities, missing/ambiguous input and source preservation rather than merely mirroring data classes. Reports of planning inspection do not claim execution. Use pytest structured identities first and declare unsupported platforms/producers explicitly.
