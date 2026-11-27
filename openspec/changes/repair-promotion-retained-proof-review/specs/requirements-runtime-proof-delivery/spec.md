## ADDED Requirements

### Requirement: Retained upload authentication passes promotion review

The retained PR786 upload verification SHALL keep the original validation of provider job identity, execution time, upload receipt, exact archive inventory, and retained member bytes. The protected inline and standalone paths SHALL apply equivalent validation. Tests of the inline workflow SHALL execute the selected checked-in fragment from a file with controlled inputs so the protected review can evaluate the full promotion diff.

#### Scenario: Reuse of the authenticated retained upload

- **GIVEN** the recorded provider upload and the retained original ZIP
- **WHEN** the standalone or inline verifier inspects the upload
- **THEN** it accepts the recorded upload and rejects altered job metadata, receipts, or retained bytes
- **AND** the verifier and its inline workflow tests satisfy protected promotion Code Review.
