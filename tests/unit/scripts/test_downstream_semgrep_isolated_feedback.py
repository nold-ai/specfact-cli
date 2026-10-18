from __future__ import annotations

import base64
import copy
import csv
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Literal

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe
ArchiveMutation = Literal["runtime", "mode", "entrypoint", "metadata", "none"]
ArchiveMembers = dict[str, tuple[zipfile.ZipInfo, bytes]]
CONTENT_MUTATIONS = {
    "runtime": (b"return 7", b"return 8"),
    "entrypoint": (b"semgrep.main:main", b"semgrep.main:evil"),
    "metadata": (b"click>=8", b"click>=1"),
}


@pytest.mark.parametrize("binding", ["candidate", "admitted"])
def test_clean_audit_json_with_nonzero_exit_rejects(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, binding: str
) -> None:
    module = contract._module()
    admitted, actual, candidate = contract._bound_audit(module, wheel_recipe, tmp_path)
    if binding == "candidate":
        verified = module.verify_candidate(wheel_recipe[0], wheel_recipe[2], candidate.path)
        bound = verified.candidate_audit_input(actual, tmp_path / "audit.txt")
    else:
        bound = admitted.audit_input(actual, tmp_path / "audit.txt")
    stdout = json.dumps(contract._audit_result())
    successful = subprocess.CompletedProcess(["pip-audit"], 0, stdout, "")
    failed = subprocess.CompletedProcess(successful.args, 2, successful.stdout, successful.stderr)
    report = bound.assert_complete_result(successful)
    assert report["actual_inventory"] == bound.actual_inventory
    assert report["production_admission"] == ("not_requested" if binding == "candidate" else "admitted")
    with pytest.raises(ValueError, match="Advisory lookup failed"):
        bound.assert_complete_result(failed)


def _read_members(path: Path) -> tuple[ArchiveMembers, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {info.filename: (copy.copy(info), archive.read(info)) for info in archive.infolist()}, archive.comment


def _regenerate_record(members: ArchiveMembers) -> None:
    record_name = f"semgrep-{contract.DOWNSTREAM}.dist-info/RECORD"
    record = io.StringIO(newline="")
    writer = csv.writer(record, lineterminator="\n")
    for name in sorted(members):
        if name != record_name:
            content = members[name][1]
            digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
            writer.writerow((name, f"sha256={digest}", str(len(content))))
    writer.writerow((record_name, "", ""))
    members[record_name] = members[record_name][0], record.getvalue().encode()


def _rewrite_member(path: Path, mutation: ArchiveMutation) -> tuple[ArchiveMembers, str | None, bytes]:
    original, comment = _read_members(path)
    members = {name: (copy.copy(info), content) for name, (info, content) in original.items()}
    suffixes = {
        "runtime": "/main.py",
        "mode": "/semgrep-core",
        "entrypoint": "/entry_points.txt",
        "metadata": "/METADATA",
    }
    target = None if mutation == "none" else next(name for name in members if name.endswith(suffixes[mutation]))
    if target is not None:
        info, content = members[target]
        if mutation == "mode":
            info.external_attr &= ~(0o111 << 16)
        else:
            before, after = CONTENT_MUTATIONS[mutation]
            assert content.count(before) == 1
            members[target] = info, content.replace(before, after)
    _regenerate_record(members)
    with zipfile.ZipFile(path, "w") as archive:
        archive.comment = comment
        for info, content in members.values():
            archive.writestr(copy.copy(info), content)
    return original, target, comment


def _assert_member_headers(before: zipfile.ZipInfo, after: zipfile.ZipInfo, removed_executable: bool) -> None:
    expected = copy.copy(before)
    if removed_executable:
        assert before.external_attr & (0o111 << 16)
        expected.external_attr &= ~(0o111 << 16)
    header_fields = (
        "filename",
        "date_time",
        "compress_type",
        "comment",
        "extra",
        "create_system",
        "create_version",
        "extract_version",
        "reserved",
        "flag_bits",
        "volume",
        "internal_attr",
        "external_attr",
    )
    for field in header_fields:
        assert getattr(after, field) == getattr(expected, field), (before.filename, field)


def _assert_payload_change(before: bytes, after: bytes, replacement: tuple[bytes, bytes] | None) -> None:
    if replacement is None:
        assert after != before
        return
    old, new = replacement
    assert before.count(old) == 1
    assert after == before.replace(old, new)
    assert after != before


def _assert_isolated_rewrite(
    path: Path, original: ArchiveMembers, target: str | None, comment: bytes, mutation: ArchiveMutation
) -> None:
    rewritten, rewritten_comment = _read_members(path)
    assert list(rewritten) == list(original)
    assert rewritten_comment == comment
    with zipfile.ZipFile(path) as archive:
        contract._assert_record(archive)
    payload_mutated = mutation in CONTENT_MUTATIONS
    for name, (before_info, before_content) in original.items():
        after_info, after_content = rewritten[name]
        _assert_member_headers(before_info, after_info, name == target and mutation == "mode")
        if name == target and payload_mutated:
            _assert_payload_change(before_content, after_content, CONTENT_MUTATIONS[mutation])
        elif name.endswith("/RECORD") and payload_mutated:
            _assert_payload_change(before_content, after_content, None)
        else:
            assert after_content == before_content


@pytest.mark.parametrize("mutation", ["runtime", "mode", "entrypoint", "metadata"])
def test_candidate_rejects_one_isolated_mutation(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, mutation: ArchiveMutation
) -> None:
    module = contract._module()
    recipe_path, _recipe, upstream = wheel_recipe
    candidate = module.build_candidate(recipe_path, upstream, tmp_path / "candidate")
    original, target, comment = _rewrite_member(candidate.path, mutation)
    _assert_isolated_rewrite(candidate.path, original, target, comment, mutation)
    error = (
        "Candidate archive attributes changed"
        if mutation == "mode"
        else rf"Candidate payload changed: {re.escape(str(target))}$"
    )
    with pytest.raises(ValueError, match=error):
        module.verify_candidate(recipe_path, upstream, candidate.path)


def test_candidate_accepts_noop_zip_rewrite(wheel_recipe: contract.WheelRecipe, tmp_path: Path) -> None:
    module = contract._module()
    recipe_path, _recipe, upstream = wheel_recipe
    candidate = module.build_candidate(recipe_path, upstream, tmp_path / "candidate")
    original_bytes = candidate.path.read_bytes()
    original, target, comment = _rewrite_member(candidate.path, "none")
    _assert_isolated_rewrite(candidate.path, original, target, comment, "none")
    assert candidate.path.read_bytes() == original_bytes
    assert module.verify_candidate(recipe_path, upstream, candidate.path).sha256 == candidate.sha256
