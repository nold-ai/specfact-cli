import json
from collections.abc import Callable
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specfact_cli.registry import CommandRegistry, module_packages as packages
from tests.unit.security.test_executable_identity_oracles import (
    _assert_genuine_signature,
    _canonical_compatibility,
    _register,
)
from tests.unit.security.test_module_command_squatting import _reset_registration
from tests.unit.security.test_package_candidate_eligibility import (
    _signed_copy,
    selection_key as selection_key,
)


ENCODINGS: dict[str, tuple[bytes, int]] = {
    "owner-execute": (b"harmless permission probe", 0o744),
    "group-execute": (b"harmless permission probe", 0o654),
    "other-execute": (b"harmless permission probe", 0o645),
    "thin-big-32": (b"\xfe\xed\xfa\xce" + bytes(20), 0o644),
    "thin-little-32": (b"\xce\xfa\xed\xfe" + bytes(20), 0o644),
    "thin-big-64": (b"\xfe\xed\xfa\xcf" + bytes(20), 0o644),
    "fat-little-32": (b"\xbe\xba\xfe\xca" + bytes(20), 0o644),
    "fat-big-64": (b"\xca\xfe\xba\xbf" + bytes(20), 0o644),
    "fat-little-64": (b"\xbf\xba\xfe\xca" + bytes(20), 0o644),
}
ENCODING_GROUPS = {
    "execute-bits": ("owner-execute", "group-execute", "other-execute"),
    "thin-32": ("thin-big-32", "thin-little-32"),
    "big-64": ("thin-big-64", "fat-big-64"),
    "fat-little": ("fat-little-32", "fat-little-64"),
}


def _observe_encoding(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    key: Ed25519PrivateKey,
    case: tuple[str, bool],
) -> tuple[str, bool, bool]:
    encoding, grouped = case
    label = f"{encoding}-{'grouped' if grouped else 'legacy'}"
    workspace = root / label
    try:
        with monkeypatch.context() as probe_patch:
            _canonical_compatibility(probe_patch, workspace / "canonical", key, grouped)
            candidate = workspace / "candidate"
            path = _signed_copy(candidate, key, None)
            (path / "logs").mkdir()
            target = path / "logs/helper"
            data, mode = ENCODINGS[encoding]
            target.write_bytes(data)
            target.chmod(mode)
            _assert_genuine_signature(path)
            _register(probe_patch, candidate, grouped)
            return (
                label,
                CommandRegistry.get_module_metadata("code") is None,
                (path / "src").resolve() not in packages._ACTIVE_MODULE_SRC_DIRS,
            )
    finally:
        _reset_registration()


@pytest.mark.parametrize("encoding_group", ENCODING_GROUPS)
def test_each_executable_encoding_is_denied(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    selection_key: Ed25519PrivateKey,
    encoding_group: str,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    encodings = ENCODING_GROUPS[encoding_group]
    observations = [
        _observe_encoding(monkeypatch, tmp_path, selection_key, (encoding, grouped))
        for encoding in encodings
        for grouped in (True, False)
    ]
    record_testsuite_property(f"executable_encoding_observations-{encoding_group}", json.dumps(observations))
    assert {encoding for group in ENCODING_GROUPS.values() for encoding in group} == set(ENCODINGS)
    assert len(observations) == len(encodings) * 2
    assert all(root_denied and source_denied for _, root_denied, source_denied in observations), (
        f"Omitted executable encoding obtained authority: {observations}"
    )
