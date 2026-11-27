import hashlib
import ssl
from importlib.resources import as_file, files


def test_certifi_bundle_excludes_compromised_emsign_root() -> None:
    with as_file(files("certifi").joinpath("cacert.pem")) as bundle:
        context = ssl.create_default_context(cafile=str(bundle))
    fingerprints = {hashlib.sha256(cert).hexdigest() for cert in context.get_ca_certs(binary_form=True)}
    compromised = {"86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b"}

    assert fingerprints, "certifi must retain a nonempty CA trust store"
    assert fingerprints & compromised == set()
