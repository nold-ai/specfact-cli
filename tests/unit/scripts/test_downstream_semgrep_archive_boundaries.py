from __future__ import annotations

import io
import struct
import zipfile
from functools import partial
from pathlib import Path

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe


def _mutate_member_headers(data: bytes, offsets: tuple[int, int], value: int, attribute: str) -> bytes:
    result = bytearray(data)
    central = data.index(b"PK\x01\x02")
    local = struct.unpack_from("<I", data, central + 42)[0]
    for base, offset in zip((central, local), offsets, strict=True):
        struct.pack_into("<H", result, base + offset, value)
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        assert getattr(archive.infolist()[0], attribute) == value
    assert struct.unpack_from("<H", result, local + offsets[1])[0] == value
    return bytes(result)


def _mutate_volume(data: bytes) -> bytes:
    result = bytearray(data)
    central = data.index(b"PK\x01\x02")
    struct.pack_into("<H", result, central + 34, 1)
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        assert archive.infolist()[0].volume == 1
    return bytes(result)


def _mutate_archive_comment(data: bytes) -> bytes:
    result = bytearray(data)
    end = data.rindex(b"PK\x05\x06")
    struct.pack_into("<H", result, end + 20, 1)
    result.extend(b"x")
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        assert archive.comment == b"x"
    return bytes(result)


def _mutate_local_header_only(data: bytes) -> bytes:
    result = bytearray(data)
    central = data.index(b"PK\x01\x02")
    local = struct.unpack_from("<I", data, central + 42)[0]
    original_time = struct.unpack_from("<H", data, local + 10)[0]
    struct.pack_into("<H", result, local + 10, original_time ^ 1)
    assert result[local + 10 : local + 12] != data[local + 10 : local + 12]
    assert result[central:] == data[central:]
    return bytes(result)


def _mutate_trailing_bytes(data: bytes) -> bytes:
    result = bytearray(data)
    result.extend(b"unreviewed trailer")
    assert result.endswith(b"unreviewed trailer")
    return bytes(result)


def _mutate_prefix(data: bytes) -> bytes:
    result = bytearray(data)
    result[:0] = b"unreviewed prefix"
    assert result.startswith(b"unreviewed prefix")
    return bytes(result)


def _mutate_central_order(data: bytes) -> bytes:
    result = bytearray(data)
    central = data.index(b"PK\x01\x02")
    end = data.rindex(b"PK\x05\x06")
    records: list[bytes] = []
    position = central
    while position < end:
        assert data[position : position + 4] == b"PK\x01\x02"
        lengths = struct.unpack_from("<HHH", data, position + 28)
        next_position = position + 46 + sum(lengths)
        records.append(data[position:next_position])
        position = next_position
    assert position == end and len(records) > 1
    result[central:end] = b"".join(reversed(records))
    with zipfile.ZipFile(io.BytesIO(data)) as original, zipfile.ZipFile(io.BytesIO(result)) as changed:
        assert changed.namelist() == list(reversed(original.namelist()))
    return bytes(result)


def _mutate_archive(data: bytes, mutation: str) -> bytes:
    central = data.index(b"PK\x01\x02")
    local = struct.unpack_from("<I", data, central + 42)[0]
    assert data[local : local + 4] == b"PK\x03\x04"
    mutations = {
        "utf8-flag": partial(_mutate_member_headers, offsets=(8, 6), value=0x800, attribute="flag_bits"),
        "volume": _mutate_volume,
        "extract-version": partial(_mutate_member_headers, offsets=(6, 4), value=21, attribute="extract_version"),
        "archive-comment": _mutate_archive_comment,
        "local-header-only": _mutate_local_header_only,
        "trailing-bytes": _mutate_trailing_bytes,
        "prefix": _mutate_prefix,
        "central-order": _mutate_central_order,
    }
    if mutation not in mutations:
        raise AssertionError(f"Unknown mutation: {mutation}")
    result = mutations[mutation](data)
    assert result != data
    return result


@pytest.mark.parametrize(
    "mutation",
    [
        "utf8-flag",
        "volume",
        "extract-version",
        "archive-comment",
        "local-header-only",
        "trailing-bytes",
        "prefix",
        "central-order",
    ],
)
def test_candidate_rejects_serialized_archive_changes(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path, mutation: str
) -> None:
    module = contract._module()
    recipe_path, _recipe, upstream = wheel_recipe
    candidate = module.build_candidate(recipe_path, upstream, tmp_path / "candidate")
    original_bytes = candidate.path.read_bytes()
    mutated_bytes = _mutate_archive(original_bytes, mutation)
    candidate.path.write_bytes(mutated_bytes)
    assert candidate.path.read_bytes() == mutated_bytes
    with zipfile.ZipFile(io.BytesIO(original_bytes)) as original, zipfile.ZipFile(candidate.path) as mutated:
        contract._assert_record(mutated)
        assert {info.filename: mutated.read(info) for info in mutated.infolist()} == {
            info.filename: original.read(info) for info in original.infolist()
        }
    with pytest.raises(ValueError, match="Candidate archive attributes changed"):
        module.verify_candidate(recipe_path, upstream, candidate.path)


def test_upstream_utf8_flag_is_normalized_by_candidate_writer(
    wheel_recipe: contract.WheelRecipe, tmp_path: Path
) -> None:
    module = contract._module()
    recipe_path, recipe, upstream = wheel_recipe
    original_bytes = upstream.read_bytes()
    upstream.write_bytes(_mutate_archive(original_bytes, "utf8-flag"))
    with zipfile.ZipFile(io.BytesIO(original_bytes)) as original, zipfile.ZipFile(upstream) as patched:
        assert {info.filename: patched.read(info) for info in patched.infolist()} == {
            info.filename: original.read(info) for info in original.infolist()
        }
        normalized_name = patched.infolist()[0].filename.replace(contract.UPSTREAM, contract.DOWNSTREAM, 1)
        assert patched.infolist()[0].flag_bits == 0x800
    recipe["wheels"][0]["upstream_sha256"] = contract._sha(upstream.read_bytes())
    contract._write_json(recipe_path, recipe)
    candidate = module.build_candidate(recipe_path, upstream, tmp_path / "candidate")
    with zipfile.ZipFile(candidate.path) as archive:
        assert archive.getinfo(normalized_name).flag_bits == 0
        contract._assert_record(archive)
    verified = module.verify_candidate(recipe_path, upstream, candidate.path)
    assert verified.sha256 == candidate.sha256
