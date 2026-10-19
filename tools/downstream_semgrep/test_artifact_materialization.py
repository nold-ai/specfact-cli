#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import downstream_semgrep as boundary


_CHILD_READ = "import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())"
_WINDOWS_ACL = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$current = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$descriptors = foreach ($path in @($env:SPECFACT_PROBE_DIRECTORY, $env:SPECFACT_PROBE_FILE)) {
    $acl = Get-Acl -LiteralPath $path
    $raw = [System.Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(), 0)
    $rules = @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]) | ForEach-Object {
        @{ sid = $_.IdentityReference.Value; type = $_.AccessControlType.ToString(); rights = [int]$_.FileSystemRights }
    })
    @{
        path = $path
        owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
        sddl = $acl.GetSecurityDescriptorSddlForm([System.Security.AccessControl.AccessControlSections]::All)
        dacl_present = (($raw.ControlFlags -band [System.Security.AccessControl.ControlFlags]::DiscretionaryAclPresent) -ne 0)
        null_dacl = ($null -eq $raw.DiscretionaryAcl)
        rules = $rules
    }
}
@{ current_user = $current; descriptors = @($descriptors) } | ConvertTo-Json -Depth 6 -Compress
"""


class _ConsumerError(Exception):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _windows_privacy(path: Path, observation: dict[str, object]) -> None:
    environment = dict(os.environ)
    environment["SPECFACT_PROBE_DIRECTORY"] = str(path.parent)
    environment["SPECFACT_PROBE_FILE"] = str(path)
    encoded = base64.b64encode(_WINDOWS_ACL.encode("utf-16-le")).decode("ascii")
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
        check=False,
    )
    observation.update(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
    _require(completed.returncode == 0, "Windows Get-Acl observation failed")
    decoded = cast(dict[str, object], json.loads(completed.stdout))
    _require(isinstance(decoded, dict), "Windows ACL result must be an object")
    current = decoded.get("current_user")
    _require(isinstance(current, str) and current.startswith("S-1-"), "Windows current-user SID unreadable")
    trusted = {cast(str, current), "S-1-5-18", "S-1-5-32-544"}
    descriptors = decoded.get("descriptors")
    _require(isinstance(descriptors, list) and len(descriptors) == 2, "Windows directory/file ACL missing")
    for value, expected_path in zip(cast(list[object], descriptors), (path.parent, path), strict=True):
        _require(isinstance(value, dict), "Windows ACL descriptor unreadable")
        descriptor = cast(dict[str, object], value)
        _require(descriptor.get("path") == str(expected_path), "Windows ACL path differs")
        _require(descriptor.get("owner") in trusted, "Windows ACL owner is untrusted")
        _require(isinstance(descriptor.get("sddl"), str) and bool(descriptor["sddl"]), "Windows SDDL unreadable")
        _require(descriptor.get("dacl_present") is True, "Windows DACL absent")
        _require(descriptor.get("null_dacl") is False, "Windows null DACL permits untrusted access")
        rules = descriptor.get("rules")
        _require(isinstance(rules, list) and bool(rules), "Windows DACL rules unreadable or empty")
        for value in cast(list[object], rules):
            _require(isinstance(value, dict), "Windows ACL rule unreadable")
            rule = cast(dict[str, object], value)
            _require(rule.get("type") in {"Allow", "Deny"}, "Windows ACL rule unreadable")
            if rule["type"] == "Allow":
                _require(rule.get("sid") in trusted, "Windows ACL grants access to an untrusted SID")
    observation["native_acl"] = decoded


def _inspect(path: Path, candidate: Path, payload: bytes, observation: dict[str, object]) -> None:
    _require(type(path) is type(Path()), "Materialization must yield a concrete platform Path")
    _require(path.name == candidate.name, "Materialization changed the original basename")
    _require(path != candidate and path.parent != candidate.parent, "Materialization reused candidate storage")
    _require(stat.S_ISREG(path.lstat().st_mode), "Materialization is not an ordinary file")
    _require(stat.S_ISDIR(path.parent.lstat().st_mode), "Materialization parent is not an ordinary directory")
    _require(path.read_bytes() == payload, "Materialization bytes differ from retained bytes")
    observation.update(path=str(path), directory=str(path.parent), byte_count=len(payload))
    privacy: dict[str, object] = {"platform": os.name}
    observation["privacy"] = privacy
    if os.name == "posix":
        directory = path.parent.stat()
        privacy.update(
            owner_uid=directory.st_uid, effective_uid=os.geteuid(), mode=oct(stat.S_IMODE(directory.st_mode))
        )
        _require(directory.st_uid == os.geteuid(), "Private directory owner differs from effective user")
        _require(directory.st_mode & 0o077 == 0, "Private directory grants group or other access")
    elif os.name == "nt":
        _windows_privacy(path, privacy)
    else:
        raise AssertionError(f"Native storage privacy is unverified for {os.name}")
    privacy["status"] = "verified"
    completed = subprocess.run(
        [sys.executable, "-c", _CHILD_READ, str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
        check=False,
    )
    observation["child"] = {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "joined_inside_context": True,
    }
    _require(completed.returncode == 0, f"Materialization child returned {completed.returncode}")
    _require(completed.stdout == hashlib.sha256(payload).hexdigest() + "\n", "Child digest differs from retained bytes")


def _cleanup(path: Path, observation: dict[str, object]) -> None:
    removed = not os.path.lexists(path) and not os.path.lexists(path.parent)
    observation["cleanup"] = {"file_and_directory_removed": removed}
    _require(removed, "Materialization cleanup leaked file or directory")


def _probe_overlapping_contexts(
    fixture: boundary.AdmittedWheel, candidate: Path, retained: bytes, contexts: list[dict[str, object]]
) -> None:
    outer: dict[str, object] = {"case": "overlap_outer"}
    inner: dict[str, object] = {"case": "overlap_inner"}
    contexts.extend((outer, inner))
    with fixture.materialize() as fourth:
        _inspect(fourth, candidate, retained, outer)
        with fixture.materialize() as fifth:
            _require(fourth.parent != fifth.parent, "Overlapping contexts share a directory")
            _inspect(fifth, candidate, retained, inner)
        _cleanup(fifth, inner)
        _require(fourth.read_bytes() == retained, "Inner cleanup damaged the live outer context")
        outer["survived_inner_cleanup"] = True
    _cleanup(fourth, outer)


def _run_probe(candidate: Path, evidence: dict[str, object]) -> None:
    _require(callable(getattr(boundary.AdmittedWheel, "materialize", None)), "AdmittedWheel.materialize is missing")
    candidate = candidate.resolve(strict=True)
    payload = candidate.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    evidence.update(candidate_basename=candidate.name, candidate_sha256=digest, candidate_bytes=len(payload))
    contexts: list[dict[str, object]] = []
    evidence["contexts"] = contexts
    with tempfile.TemporaryDirectory(prefix="specfact-probe-transport-") as transport_root:
        transport = Path(transport_root) / candidate.name
        transport.write_bytes(payload)
        retained = transport.read_bytes()
        fixture = boundary.AdmittedWheel(
            _filename=transport.name,
            _bytes=retained,
            _sha256=digest,
            _upstream_sha256="0" * 64,
            _authority=boundary._AUTHORITY,
        )
        before = transport.stat()
        transport.write_bytes(b"synthetic overwrite")
        after = transport.stat()
        _require(
            (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), "Transport overwrite changed its inode"
        )
        mutations = ["same_inode_overwrite"]
        evidence["transport_mutations"] = mutations
        normal: dict[str, object] = {"case": "normal"}
        contexts.append(normal)
        with fixture.materialize() as first:
            _inspect(first, candidate, retained, normal)
        _cleanup(first, normal)

        replacement = transport.with_suffix(".replacement")
        replacement.write_bytes(b"synthetic replacement")
        replacement.replace(transport)
        mutations.append("replacement")
        repeated: dict[str, object] = {"case": "repeated"}
        contexts.append(repeated)
        with fixture.materialize() as second:
            _require(second.parent != first.parent, "Repeated context reused a directory")
            _inspect(second, candidate, retained, repeated)
        _cleanup(second, repeated)

        transport.unlink()
        mutations.append("deletion")
        exceptional: dict[str, object] = {"case": "consumer_error"}
        contexts.append(exceptional)
        consumer_error = _ConsumerError("synthetic consumer error")
        third: Path | None = None
        try:
            with fixture.materialize() as third:
                _inspect(third, candidate, retained, exceptional)
                raise consumer_error
        except _ConsumerError as caught:
            _require(caught is consumer_error, "Materialization changed the consumer exception")
        if third is None:
            raise AssertionError("Exceptional context did not yield a Path")
        _cleanup(third, exceptional)
        exceptional["consumer_error_preserved"] = True

        _probe_overlapping_contexts(fixture, candidate, retained, contexts)
        directories = {str(context["directory"]) for context in contexts}
        _require(len(directories) == len(contexts), "Contexts did not use fresh private directories")
    _require(not os.path.lexists(transport_root), "Private transport cleanup failed")
    _require(candidate.read_bytes() == payload, "Real candidate bytes changed during the probe")
    evidence["contexts_verified"] = len(contexts)
    evidence["native_privacy"] = {
        "posix": "verified" if os.name == "posix" else "UNVERIFIED",
        "windows": "verified" if os.name == "nt" else "UNVERIFIED",
    }


def _main() -> int:
    evidence: dict[str, object] = {
        "candidate_only": True,
        "production_admission": "not_requested",
        "fixture": "synthetic-private-authority-test-only",
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "temporary_root": tempfile.gettempdir(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "boundary_sha256": hashlib.sha256(Path(cast(str, boundary.__file__)).read_bytes()).hexdigest(),
    }
    try:
        _require(len(sys.argv) == 2, "Usage: test_artifact_materialization.py CANDIDATE_WHEEL")
        _run_probe(Path(sys.argv[1]), evidence)
    except Exception as error:
        evidence.update(status="failed", error_type=type(error).__name__, error=str(error))
        sys.stdout.write(json.dumps(evidence, sort_keys=True) + "\n")
        return 1
    evidence["status"] = "passed"
    sys.stdout.write(json.dumps(evidence, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
