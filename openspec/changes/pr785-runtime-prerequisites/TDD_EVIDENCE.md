# Prerequisite diagnostic evidence

On 24 October 2026 at 03:55 Europe/Berlin, the isolated two-test baseline exited 1 against unchanged main workflow bytes. Both tests failed their intended assertions. There were zero setup errors and zero skips. Each testcase retained exactly one native `specfact.selector` property.

The first assertion observed normal pull-request and push triggers in addition to manual dispatch. The second observed the normal validation steps instead of the four diagnostic steps. The observer source was absent. No production edit preceded these failures.

The existing auxiliary Python 3.12.13 environment ran the frozen `baseline2.sh` plan with plugin autoload, conftests and project pytest configuration disabled. The exact native selector plugin was loaded once. This was a local configuration test, not protected runtime isolation or hosted service proof.

XML SHA-256 is `46fdb7862085c8436c7eb4698636679748ef0f859f8cdb5408bd12f82ea9da7c`. Frozen baseline input manifest SHA-256 is `c9d1e389e5069f075a02942af7f3d9c5741f7a95e9f535a2da4a92e00da74ad4`. The independent corrected mapping review SHA-256 is `46feb2348a17a48b473cf75a30e9e72431abadf46f585e09a9233709a9fe7c22`.

The coordinator retains raw XML, combined output, exit status, frozen plan and both original and corrected review reports in the recovery audit. GREEN and the source/hosted inspections remain pending. No native release RED, CI execution, policy authority or deployment is claimed.

The normal TEST-first commit then stopped at the mandatory Radon CC17 finding in the second test. The correction expresses the same four dictionaries as one exact ordered-list equality. Independent review `37aa10768f7d23385869fbd7dc5f80c715a9116d5f1fa067d599c849b70ab85d` accepted every preserved condition. No hook was bypassed.

The corrected test SHA-256 is `6256afb8aa1ced621c27b896b3a69fdc56e83a0711697d75d926b15ab7bbf149`. A separate baseline3 run against unchanged workflow bytes again produced two intended assertion failures, zero errors/skips and one selector property each. Its XML SHA-256 is `cb29460118fd5722cf5a3c4b540c48f145701f451a7a1a35531ab2c0f7bc34c8`. The baseline2 outputs remain original evidence for the earlier test bytes. Observer implementation and hosted proof remain pending.
