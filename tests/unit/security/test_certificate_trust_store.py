import hashlib
import ssl

import certifi


def test_certifi_bundle_excludes_compromised_emsign_root() -> None:
    context = ssl.create_default_context(cafile=certifi.where())
    fingerprints = {hashlib.sha256(cert).hexdigest() for cert in context.get_ca_certs(binary_form=True)}
    compromised = {"86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b"}

    assert fingerprints, "certifi must retain a nonempty CA trust store"
    assert fingerprints & compromised == set()
