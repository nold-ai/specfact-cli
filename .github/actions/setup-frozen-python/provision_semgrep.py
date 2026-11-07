from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path, PurePosixPath
from typing import IO, cast
from urllib.parse import urlsplit


REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_FILE = REPO_ROOT / "ci/security-tool-minimum-versions.json"
MAX_ARCHIVE_BYTES = 80 * 1024 * 1024
MAX_NATIVE_BYTES = 300 * 1024 * 1024
MAX_NOTICE_BYTES = 2 * 1024 * 1024
MAX_CPIO_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class NativeMember:
    source: str
    destination: str
    size: int
    digest: str


@dataclass(frozen=True)
class NativeSelection:
    version: str
    platform: str
    policy_digest: str
    artifact: dict[str, object]
    members: tuple[NativeMember, ...]
    notices: tuple[NativeMember, ...]
    expected: tuple[NativeMember, ...]
    fix: dict[str, object] | None
    components: tuple[dict[str, object], ...]


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("Native selection must contain objects with string keys")
    return cast(dict[str, object], value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Native selection requires a nonempty string")
    return value


def _size(value: object, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= maximum:
        raise ValueError("Native selection size exceeds its fixed bound")
    return value


def _digest(value: object) -> str:
    text = _text(value)
    if re.fullmatch(r"[0-9a-f]{64}", text) is None:
        raise ValueError("Native selection requires a SHA-256 digest")
    return text


def _relative(value: object) -> str:
    text = _text(value)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or text != path.as_posix() or "\\" in text or ":" in text:
        raise ValueError("Unsafe native member path")
    if text == ".":
        raise ValueError("Native members must name files")
    return text


def _members(value: object, source_key: str, maximum: int) -> tuple[NativeMember, ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= 32:
        raise ValueError("Native selection requires a bounded member list")
    members: list[NativeMember] = []
    for raw in value:
        item = _object(raw)
        members.append(
            NativeMember(
                _relative(item.get(source_key)),
                _relative(item.get("installed_path")),
                _size(item.get("size"), maximum),
                _digest(item.get("sha256")),
            )
        )
    if len({member.destination.casefold() for member in members}) != len(members):
        raise ValueError("Conflicting native destinations")
    if len({member.source for member in members}) != len(members):
        raise ValueError("Duplicate native sources")
    return tuple(members)


def _platform_key() -> str:
    systems = {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}
    machines = {"x86_64": "x86_64", "amd64": "x86_64", "arm64": "arm64", "aarch64": "arm64"}
    return f"{systems.get(platform.system(), 'unsupported')}-{machines.get(platform.machine().lower(), 'unsupported')}"


def _download(artifact: dict[str, object], destination: Path, host: str) -> None:
    url = _text(artifact.get("url"))
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != host
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Native artifact URL is outside its selected public origin")
    member = NativeMember(
        url, destination.name, _size(artifact.get("size"), MAX_ARCHIVE_BYTES), _digest(artifact.get("sha256"))
    )
    request: str | urllib.request.Request = url
    if host == "ghcr.io":
        if parsed.path != "/v2/homebrew/core/pcre2/blobs/sha256:" + member.digest:
            raise ValueError("Native bottle must be the exact selected public PCRE2 blob")
        with urllib.request.urlopen(
            "https://ghcr.io/token?service=ghcr.io&scope=repository:homebrew/core/pcre2:pull", timeout=30
        ) as response:
            if response.status != 200:
                raise ValueError("Public native bottle token request failed")
            payload = response.read(65537)
        if len(payload) > 65536:
            raise ValueError("Public native bottle token response exceeds its fixed bound")
        token = _text(_object(json.loads(payload)).get("token"))
        if len(token) > 16384 or re.fullmatch(r"[A-Za-z0-9._~+/-]+=*", token) is None:
            raise ValueError("Invalid public native bottle pull token")
        request = urllib.request.Request(url)
        request.add_unredirected_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise ValueError("Native artifact download did not return HTTP 200")
        _copy_verified(response, destination, member)


def _copy_verified(source: IO[bytes], destination: Path, member: NativeMember) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    with destination.open("xb") as output:
        while data := source.read(min(1024 * 1024, member.size - total + 1)):
            total += len(data)
            if total > member.size:
                raise ValueError("Native member exceeded its declared size")
            output.write(data)
            digest.update(data)
    if total != member.size or digest.hexdigest() != member.digest:
        raise ValueError("Native member size or digest mismatch")


def _verify_installation(destination: Path, members: tuple[NativeMember, ...]) -> None:
    if destination.is_symlink() or not destination.is_dir():
        raise ValueError("Native installation must be an owned directory")
    expected = {member.destination for member in members}
    directories = {
        parent.as_posix() for name in expected for parent in PurePosixPath(name).parents if str(parent) != "."
    }
    actual: set[str] = set()
    for path in destination.rglob("*"):
        name = path.relative_to(destination).as_posix()
        if path.is_symlink() or (path.is_dir() and name not in directories):
            raise ValueError("Unexpected native installation entry")
        if path.is_file():
            actual.add(name)
        elif not path.is_dir():
            raise ValueError("Unexpected native installation entry")
    if actual != expected:
        raise ValueError("Native installation file set differs from selection")
    for member in members:
        path = destination / member.destination
        if path.stat().st_size != member.size:
            raise ValueError("Existing native member size mismatch")
        if os.name != "nt" and member.destination in {"osemgrep", "osemgrep.exe"} and not os.access(path, os.X_OK):
            raise ValueError("Native engine is not executable")
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != member.digest:
            raise ValueError("Existing native member digest mismatch")


def _extract_wheel(archive_path: Path, destination: Path, version: str, members: tuple[NativeMember, ...]) -> None:
    prefix = f"semgrep-{version}.data/purelib/semgrep/bin/"
    with zipfile.ZipFile(archive_path) as archive:
        names: set[str] = set()
        native: set[str] = set()
        for entry in archive.infolist():
            name = _relative(entry.filename.rstrip("/"))
            if name in names or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Unsafe or duplicate native archive entry")
            names.add(name)
            if not entry.is_dir() and name.startswith(prefix) and not name.endswith(".py"):
                native.add(name)
        if native != {member.source for member in members}:
            raise ValueError("Native archive member set differs from selection")
        for member in members:
            entry = archive.getinfo(member.source)
            if entry.file_size != member.size or stat.S_IFMT(entry.external_attr >> 16) not in (0, stat.S_IFREG):
                raise ValueError("Native archive member metadata mismatch")
            with archive.open(entry) as source:
                _copy_verified(source, destination / member.destination, member)


def _limit_output(maximum: int) -> None:
    import resource

    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    limits = [maximum, *(limit for limit in (soft, hard) if limit != resource.RLIM_INFINITY)]
    resource.setrlimit(resource.RLIMIT_FSIZE, (min(limits), min(limits)))


def _extract_curl_fix(fix: dict[str, object], staging: Path, destination: Path) -> tuple[NativeMember, ...]:
    if _platform_key() != "linux-x86_64":
        raise ValueError("Vendor curl selection requires its exact Linux platform")
    members = _members(fix.get("members"), "archive_path", MAX_CPIO_BYTES)
    archive_path = staging / "vendor.rpm"
    _download(fix, archive_path, "repo.almalinux.org")
    offset = _size(fix.get("payload_offset"), archive_path.stat().st_size - 1)
    with archive_path.open("rb") as source:
        source.seek(offset)
        payload = source.read(MAX_ARCHIVE_BYTES + 1)
    if not payload.startswith(bytes.fromhex("28b52ffd")):
        raise ValueError("Vendor curl payload is not the selected Zstandard format")
    compressed = staging / "vendor.payload.zst"
    compressed.write_bytes(payload)
    size = _size(fix.get("cpio_size"), MAX_CPIO_BYTES)
    cpio_path = staging / "vendor.cpio"
    with cpio_path.open("xb") as output:
        subprocess.run(
            ["zstd", "--decompress", "--stdout", "--", str(compressed)],
            stdout=output,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=30,
            preexec_fn=partial(_limit_output, size + 1),
        )
    data = cpio_path.read_bytes()
    if len(data) != size or hashlib.sha256(data).hexdigest() != _digest(fix.get("cpio_sha256")):
        raise ValueError("Vendor curl CPIO payload mismatch")
    selected = {member.source: member for member in members}
    seen: set[str] = set()
    cursor = 0
    while cursor + 110 <= len(data):
        header = data[cursor : cursor + 110]
        if header[:6] != b"070701" or re.fullmatch(rb"[0-9a-fA-F]{104}", header[6:]) is None:
            raise ValueError("Unexpected vendor curl CPIO header")
        fields = [int(header[index : index + 8], 16) for index in range(6, 110, 8)]
        mode, length, name_length = fields[1], fields[6], fields[11]
        cursor += 110
        if not 0 < name_length <= 4096 or cursor + name_length > len(data):
            raise ValueError("Invalid vendor curl member name")
        raw_name = data[cursor : cursor + name_length]
        if raw_name[-1:] != b"\0":
            raise ValueError("Unterminated vendor curl member name")
        name = raw_name[:-1].decode("utf-8")
        cursor = (cursor + name_length + 3) // 4 * 4
        if name == "TRAILER!!!":
            break
        name = _relative(name.removeprefix("./"))
        if name in seen or cursor + length > len(data):
            raise ValueError("Invalid or duplicate vendor curl member")
        seen.add(name)
        if name in selected:
            member = selected.pop(name)
            if not stat.S_ISREG(mode) or length != member.size:
                raise ValueError("Vendor curl member is not the selected regular file")
            target = destination / member.destination
            if target.exists():
                target.unlink()
            import io

            _copy_verified(io.BytesIO(data[cursor : cursor + length]), target, member)
        cursor = (cursor + length + 3) // 4 * 4
    else:
        raise ValueError("Vendor curl CPIO trailer missing")
    if selected:
        raise ValueError("Selected vendor curl members missing")
    return members


def _extract_pcre2_fix(fix: dict[str, object], staging: Path, destination: Path) -> None:
    if _platform_key() != "macos-arm64":
        raise ValueError("Vendor PCRE2 selection requires its exact Mac platform")
    members = _members(fix.get("members"), "archive_path", MAX_CPIO_BYTES)
    selected = {member.source: member for member in members}
    archive_path = staging / "pcre2.bottle.tar.gz"
    _download(fix, archive_path, "ghcr.io")
    names: set[str] = set()
    expanded = 0
    with tarfile.open(archive_path, "r:gz") as archive:
        for entry in archive:
            name = _relative(entry.name.rstrip("/"))
            expanded += entry.size
            if name in names or len(names) >= 1024 or expanded > MAX_NATIVE_BYTES:
                raise ValueError("Invalid, duplicate or oversized native bottle entry")
            names.add(name)
            if name in selected:
                member = selected.pop(name)
                if not entry.isfile() or entry.size != member.size:
                    raise ValueError("Native bottle member is not the selected regular file")
                source = archive.extractfile(entry)
                if source is None:
                    raise ValueError("Native bottle member is unavailable")
                target = destination / member.destination
                if target.exists():
                    target.unlink()
                with source:
                    _copy_verified(source, target, member)
    if selected:
        raise ValueError("Selected native bottle members missing")


def _copy_build_entry(source: IO[bytes], destination: Path, size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with destination.open("xb") as output:
        while data := source.read(min(1024 * 1024, size - total + 1)):
            total += len(data)
            if total > size:
                raise ValueError("Build archive member exceeds its declared size")
            output.write(data)
    if total != size:
        raise ValueError("Build archive member is incomplete")


def _extract_build_zip(archive_path: Path, destination: Path, prefix: str, *, omit_doc: bool) -> None:
    names: set[str] = set()
    expanded = 0
    files = 0
    with zipfile.ZipFile(archive_path) as archive:
        for entry in archive.infolist():
            name = _relative(entry.filename.rstrip("/"))
            mode = stat.S_IFMT(entry.external_attr >> 16)
            if name.casefold() in names or mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("Unsafe or duplicate build archive entry")
            names.add(name.casefold())
            if entry.is_dir():
                continue
            if mode == stat.S_IFDIR:
                raise ValueError("Invalid build archive member type")
            if not name.startswith(prefix):
                continue
            relative = _relative(name[len(prefix) :])
            if omit_doc and relative.startswith("doc/"):
                continue
            expanded += entry.file_size
            if expanded > MAX_NATIVE_BYTES:
                raise ValueError("Selected build files exceed the existing expanded bound")
            with archive.open(entry) as source:
                _copy_build_entry(source, destination / relative, entry.file_size)
            files += 1
    if not files:
        raise ValueError("Selected build archive is empty")


def _extract_build_source(archive_path: Path, destination: Path) -> None:
    names: set[str] = set()
    expanded = 0
    files = 0
    prefix = "curl-8.23.0/"
    with tarfile.open(archive_path, "r:xz") as archive:
        for entry in archive:
            name = _relative(entry.name.rstrip("/"))
            if name.casefold() in names or not (entry.isdir() or entry.isfile()):
                raise ValueError("Unsafe or duplicate build source entry")
            names.add(name.casefold())
            if entry.isdir() or not name.startswith(prefix):
                continue
            expanded += entry.size
            if expanded > MAX_NATIVE_BYTES:
                raise ValueError("Build source exceeds the existing expanded bound")
            source = archive.extractfile(entry)
            if source is None:
                raise ValueError("Build source member is unavailable")
            with source:
                _copy_build_entry(source, destination / _relative(name[len(prefix) :]), entry.size)
            files += 1
    if not files:
        raise ValueError("Selected build source is empty")


def _windows_recipe(fix: dict[str, object]) -> Path:
    recipe = _object(fix.get("recipe"))
    if recipe.get("source") != ".github/actions/setup-frozen-python/windows_curl.py":
        raise ValueError("Windows curl requires its exact private build owner")
    path = REPO_ROOT / _text(recipe.get("source"))
    if path.is_symlink() or not path.is_file() or path.stat().st_size != _size(recipe.get("size"), MAX_NOTICE_BYTES):
        raise ValueError("Windows curl recipe is missing or altered")
    with path.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != _digest(recipe.get("sha256")):
            raise ValueError("Windows curl recipe digest mismatch")
    return path


def _extract_windows_curl_fix(fix: dict[str, object], staging: Path, destination: Path) -> None:
    if _platform_key() != "windows-x86_64" or fix.get("kind") != "source-build":
        raise ValueError("Windows curl correction requires its exact build/platform selection")
    if fix.get("url") != "https://curl.se/download/curl-8.23.0.tar.xz" or fix.get("version") != "8.23.0":
        raise ValueError("Windows curl requires its frozen official source release")
    recipe = _windows_recipe(fix)
    source_archive = staging / "curl-source.tar.xz"
    _download(fix, source_archive, "curl.se")
    source_root = staging / "curl-source"
    _extract_build_source(source_archive, source_root)
    tools = _object(fix.get("tools"))
    if set(tools) != {"zig", "cmake", "ninja"}:
        raise ValueError("Windows curl build tools differ from its finite recipe")
    programs: dict[str, Path] = {}
    for role, host, prefix, executable in (
        ("zig", "ziglang.org", "zig-windows-x86_64-0.11.0/", "zig.exe"),
        ("cmake", "files.pythonhosted.org", "cmake/data/", "bin/cmake.exe"),
        ("ninja", "github.com", "", "ninja.exe"),
    ):
        artifact = _object(tools[role])
        archive_path = staging / f"{role}.zip"
        _download(artifact, archive_path, host)
        tool_root = staging / role
        _extract_build_zip(archive_path, tool_root, prefix, omit_doc=role == "zig")
        programs[role] = tool_root / executable
        if programs[role].is_symlink() or not programs[role].is_file():
            raise ValueError("Selected Windows build executable is missing")
    spec = importlib.util.spec_from_file_location("_frozen_windows_curl_build", recipe)
    if spec is None or spec.loader is None:
        raise ValueError("Windows curl build owner is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build = cast(Callable[..., Path], module.build_windows_curl)
    built = build(source=source_root, build=staging / "curl-build", **programs)
    outputs = _members(fix.get("members"), "build_path", MAX_CPIO_BYTES)
    member = outputs[0]
    if len(outputs) != 1 or member.source != "libcurl-4.dll" or built.is_symlink() or not built.is_file():
        raise ValueError("Windows curl build output differs from its finite recipe")
    target = destination / member.destination
    target.unlink()
    with built.open("rb") as source:
        _copy_verified(source, target, member)
    (destination / "libssh2-1.dll").unlink()


def _selection() -> NativeSelection:
    with POLICY_FILE.open("rb") as source:
        raw = source.read(MAX_CPIO_BYTES + 1)
    if len(raw) > MAX_CPIO_BYTES:
        raise ValueError("Native selection policy exceeds its fixed bound")
    policy = _object(json.loads(raw))
    release = _object(policy.get("native_semgrep"))
    version = _text(release.get("version"))
    floor = _text(_object(policy.get("minimum_versions")).get("semgrep"))
    if any(re.fullmatch(r"\d+\.\d+\.\d+", value) is None for value in (version, floor)):
        raise ValueError("Native selection requires release versions")
    if tuple(map(int, version.split("."))) < tuple(map(int, floor.split("."))):
        raise ValueError("Native release is below the existing security floor")
    platforms = _object(release.get("platforms"))
    if _platform_key() not in platforms:
        raise ValueError("Unsupported native platform")
    artifact = _object(platforms[_platform_key()])
    members = _members(artifact.get("members"), "archive_path", MAX_NATIVE_BYTES)
    common_notices, platform_notices = release.get("notices"), artifact.get("notices", [])
    if not isinstance(common_notices, list) or not isinstance(platform_notices, list):
        raise ValueError("Native notices must be finite declared lists")
    notices = _members([*common_notices, *platform_notices], "source", MAX_NOTICE_BYTES)
    if sum(member.size for member in (*members, *notices)) > MAX_NATIVE_BYTES:
        raise ValueError("Native payload exceeds its fixed expanded bound")
    fix_keys = [key for key in ("curl_fix", "pcre2_fix") if key in artifact]
    expected_fix = {"linux-x86_64": "curl_fix", "macos-arm64": "pcre2_fix", "windows-x86_64": "curl_fix"}.get(
        _platform_key()
    )
    if len(fix_keys) > 1 or (fix_keys and fix_keys[0] != expected_fix):
        raise ValueError("Vendor correction does not match its selected platform")
    fix = _object(artifact[fix_keys[0]]) if fix_keys else None
    windows_build = bool(fix) and _platform_key() == "windows-x86_64"
    replacements = (
        _members(fix.get("members"), "build_path" if windows_build else "archive_path", MAX_CPIO_BYTES) if fix else ()
    )
    replaced = {member.destination for member in replacements}
    allowed_replacements = {
        "linux-x86_64": {"libs/libcurl.so.4", "LICENSE.libcurl"},
        "macos-arm64": {"libs/libpcre2-8.0.dylib", "LICENSE.pcre2"},
        "windows-x86_64": {"libcurl-4.dll"},
    }
    if fix and replaced != allowed_replacements[_platform_key()]:
        raise ValueError("Vendor correction must select only its exact library and notice")
    removed: set[str] = set()
    if windows_build and fix is not None:
        if fix.get("remove") != ["libssh2-1.dll"] or not any(
            member.destination == "libssh2-1.dll" for member in members
        ):
            raise ValueError("Windows curl must remove only its exact original SSH member")
        _windows_recipe(fix)
        removed = {"libssh2-1.dll"}
    expected = (
        *[member for member in members if member.destination not in replaced | removed],
        *notices,
        *replacements,
    )
    if len({member.destination.casefold() for member in expected}) != len(expected):
        raise ValueError("Native payload and notice destinations conflict")
    engine = "osemgrep.exe" if _platform_key().startswith("windows-") else "osemgrep"
    if sum(member.destination == engine for member in members) != 1 or engine in replaced:
        raise ValueError("Native selection must retain one unmodified engine")
    for notice in notices:
        path = REPO_ROOT / notice.source
        if path.is_symlink() or not path.is_file() or path.stat().st_size != notice.size:
            raise ValueError("Selected native notice is missing or unsafe")
        with path.open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != notice.digest:
                raise ValueError("Selected native notice digest mismatch")
    raw_components = artifact.get("components", [])
    if not isinstance(raw_components, list) or len(raw_components) > 32:
        raise ValueError("Native component list exceeds its fixed member bound")
    components: list[dict[str, object]] = []
    destinations = {member.destination for member in expected}
    for raw_component in raw_components:
        component = _object(raw_component)
        name = _text(component.get("name"))
        paths, notice_paths = component.get("files"), component.get("notice_paths")
        if not isinstance(paths, list) or not 1 <= len(paths) <= 32 or not isinstance(notice_paths, list):
            raise ValueError("Native component requires finite file and notice lists")
        referenced = [_relative(path) for path in [*paths, *notice_paths]]
        if any(path not in destinations for path in referenced):
            raise ValueError("Native component references a file outside the final composition")
        record: dict[str, object] = {
            "name": name,
            "files": [_relative(path) for path in paths],
            "notice_paths": [_relative(path) for path in notice_paths],
            "source_info": _text(component.get("source_info")),
        }
        if "version" in component:
            record["version"] = _text(component["version"])
        if any(existing["name"] == name for existing in components):
            raise ValueError("Native component names must be unique")
        components.append(record)
    return NativeSelection(
        version,
        _platform_key(),
        hashlib.sha256(raw).hexdigest(),
        artifact,
        members,
        notices,
        expected,
        fix,
        tuple(components),
    )


def _installed_inventory() -> dict[str, object]:
    selected = _selection()
    engine = "osemgrep.exe" if selected.platform.startswith("windows-") else "osemgrep"
    executable = shutil.which(engine)
    if executable is None:
        raise ValueError("Selected native scanner is unavailable for delivery evidence")
    destination = Path(executable).absolute().parent
    _verify_installation(destination, selected.expected)
    files: list[dict[str, object]] = []
    for member in selected.expected:
        with (destination / member.destination).open("rb") as source:
            sha1 = hashlib.file_digest(source, lambda: hashlib.sha1(usedforsecurity=False)).hexdigest()
        files.append({"path": member.destination, "sha256": member.digest, "sha1": sha1, "size": member.size})
    return {
        "name": "semgrep-native",
        "version": selected.version,
        "platform": selected.platform,
        "policy_sha256": selected.policy_digest,
        "artifact_url": _text(selected.artifact.get("url")),
        "artifact_sha256": _digest(selected.artifact.get("sha256")),
        "vendor_artifacts": [
            {
                "package": _text(selected.fix.get("package")),
                "version": _text(selected.fix.get("version")),
                "url": _text(selected.fix.get("url")),
                "sha256": _digest(selected.fix.get("sha256")),
                **(
                    {"kind": "source-build", "recipe": selected.fix["recipe"], "build_tools": selected.fix["tools"]}
                    if selected.fix.get("kind") == "source-build"
                    else {}
                ),
            }
        ]
        if selected.fix
        else [],
        "files": files,
        "components": list(selected.components),
    }


def provision_semgrep(destination: Path) -> Path:
    selected = _selection()
    version, artifact = selected.version, selected.artifact
    members, notices, expected, fix = selected.members, selected.notices, selected.expected, selected.fix
    engine = "osemgrep.exe" if selected.platform.startswith("windows-") else "osemgrep"
    if not destination.is_absolute() or destination.is_symlink():
        raise ValueError("Native destination must be an absolute owned directory")
    if destination.exists():
        _verify_installation(destination, expected)
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}-", dir=destination.parent) as temporary:
        staging = Path(temporary)
        output = staging / "native"
        archive = staging / "upstream.whl"
        _download(artifact, archive, "files.pythonhosted.org")
        _extract_wheel(archive, output, version, members)
        if fix:
            if selected.platform == "macos-arm64":
                _extract_pcre2_fix(fix, staging, output)
            elif selected.platform == "windows-x86_64":
                _extract_windows_curl_fix(fix, staging, output)
            else:
                _extract_curl_fix(fix, staging, output)
        for notice in notices:
            with (REPO_ROOT / notice.source).open("rb") as source:
                _copy_verified(source, output / notice.destination, notice)
        for member in expected:
            (output / member.destination).chmod(0o755 if member.destination == engine else 0o644)
        _verify_installation(output, expected)
        if destination.exists() or destination.is_symlink():
            raise ValueError("Native destination appeared during provisioning")
        output.rename(destination)
    return destination


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("Expected the invocation-owned native destination")
        sys.stdout.write(f"{provision_semgrep(Path(sys.argv[1]))}\n")
    except (OSError, ValueError, zipfile.BadZipFile, tarfile.TarError, subprocess.SubprocessError) as error:
        sys.stderr.write(f"Native Semgrep provisioning failed: {error}\n")
        raise SystemExit(1) from error
