import hashlib
import importlib.util
import io
import json
import os
import platform
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from functools import partial
from pathlib import Path
from types import ModuleType

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]
ACTION = ROOT / ".github/actions/setup-frozen-python"
PREFIX = "semgrep-1.184.0.data/purelib/semgrep/bin/"


def load_provisioner() -> ModuleType:
    path = ACTION / "provision_semgrep.py"
    spec = importlib.util.spec_from_file_location("native_semgrep_provisioning_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, dict[str, object], bytes]:
    module = load_provisioner()
    contents = {PREFIX + "semgrep-core": b"native-engine", PREFIX + "libs/libexample.so.1": b"native-library"}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, data in {**contents, PREFIX + "__init__.py": b"excluded-wrapper"}.items():
            archive.writestr(name, data)
    data = stream.getvalue()
    notice = tmp_path / "tools/semgrep/LICENSE"
    notice.parent.mkdir(parents=True)
    notice.write_bytes(b"supplier notice")
    members = [
        {
            "archive_path": name,
            "installed_path": "osemgrep" if name.endswith("semgrep-core") else "libs/libexample.so.1",
            "size": len(value),
            "sha256": hashlib.sha256(value).hexdigest(),
        }
        for name, value in contents.items()
    ]
    release = {
        "version": "1.184.0",
        "platforms": {
            "linux-x86_64": {
                "url": "https://files.pythonhosted.org/packages/selected.whl",
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "members": members,
            }
        },
        "notices": [
            {
                "source": "tools/semgrep/LICENSE",
                "installed_path": "LICENSE.semgrep",
                "size": notice.stat().st_size,
                "sha256": hashlib.sha256(notice.read_bytes()).hexdigest(),
            }
        ],
    }
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"minimum_versions": {"semgrep": "1.175.0"}, "native_semgrep": release}))
    monkeypatch.setattr(module, "POLICY_FILE", policy)
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")

    class Response(io.BytesIO):
        status = 200

    monkeypatch.setattr(urllib.request, "urlopen", lambda *_args, **_kwargs: Response(data))
    return module, release, data


def test_action_exposes_only_successfully_provisioned_native_directory() -> None:
    action = yaml.safe_load((ACTION / "action.yml").read_text(encoding="utf-8"))
    scripts = [step.get("run", "") for step in action["runs"]["steps"]]
    install = next((script for script in scripts if "provision_semgrep.py" in script), "")
    assert install, "Frozen setup does not provision the native scanner"
    assert '>> "$GITHUB_PATH"' in install
    assert '"$RUNNER_TEMP/' in install


def test_exact_installation_and_reuse(payload: tuple[ModuleType, dict[str, object], bytes], tmp_path: Path) -> None:
    module, _, _ = payload
    destination = tmp_path / "native output"
    assert module.provision_semgrep(destination) == destination
    assert (destination / "osemgrep").read_bytes() == b"native-engine"
    assert (destination / "libs/libexample.so.1").read_bytes() == b"native-library"
    assert (destination / "LICENSE.semgrep").read_bytes() == b"supplier notice"
    assert not (destination / "__init__.py").exists()
    assert module.provision_semgrep(destination) == destination


@pytest.mark.parametrize("problem", ["archive-digest", "member-digest", "missing-member", "unsafe-path", "collision"])
def test_invalid_payload_never_publishes(
    payload: tuple[ModuleType, dict[str, object], bytes], tmp_path: Path, problem: str
) -> None:
    module, release, _ = payload
    policy = json.loads(module.POLICY_FILE.read_text())
    selected = policy["native_semgrep"]["platforms"]["linux-x86_64"]
    match problem:
        case "archive-digest":
            selected["sha256"] = "0" * 64
        case "member-digest":
            selected["members"][0]["sha256"] = "0" * 64
        case "missing-member":
            selected["members"][0]["archive_path"] = PREFIX + "absent"
        case "unsafe-path":
            selected["members"][0]["installed_path"] = "../outside"
        case _:
            selected["members"][1]["installed_path"] = "OSEMGREP"
    module.POLICY_FILE.write_text(json.dumps(policy))
    destination = tmp_path / "native"
    with pytest.raises((ValueError, OSError)):
        module.provision_semgrep(destination)
    assert not destination.exists()
    assert not (tmp_path / "outside").exists()
    assert release["version"] == "1.184.0"


def _damage_existing_sdk(destination: Path, outside: Path, problem: str) -> None:
    target = destination / "osemgrep"
    match problem:
        case "modified":
            target.write_bytes(b"modified")
        case "extra":
            (destination / "unexpected").write_bytes(b"unexpected")
        case "fifo":
            os.mkfifo(destination / "unexpected-fifo")
        case "not-executable":
            target.chmod(0o644)
        case _:
            target.unlink()
            target.symlink_to(outside)


@pytest.mark.parametrize(
    "problem",
    [
        "modified",
        "extra",
        "symlink",
        pytest.param("fifo", marks=pytest.mark.skipif(os.name == "nt", reason="POSIX special files")),
        pytest.param("not-executable", marks=pytest.mark.skipif(os.name == "nt", reason="POSIX execute bits")),
    ],
)
def test_existing_installation_is_never_repaired(
    payload: tuple[ModuleType, dict[str, object], bytes], tmp_path: Path, problem: str
) -> None:
    module, _, _ = payload
    destination = tmp_path / "native"
    module.provision_semgrep(destination)
    _damage_existing_sdk(destination, tmp_path / "not-present", problem)
    target = destination / "osemgrep"
    with pytest.raises((ValueError, OSError)):
        module.provision_semgrep(destination)
    match problem:
        case "modified":
            assert target.read_bytes() == b"modified"
        case "extra":
            assert (destination / "unexpected").read_bytes() == b"unexpected"
        case "symlink":
            assert target.is_symlink()
        case "fifo":
            assert stat.S_ISFIFO((destination / "unexpected-fifo").stat().st_mode)
        case _:
            assert target.stat().st_mode & stat.S_IXUSR == 0


@pytest.mark.parametrize("problem", ["traversal", "duplicate", "symlink"])
def test_malformed_archive_never_escapes_staging(
    payload: tuple[ModuleType, dict[str, object], bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    module, _, original = payload
    stream = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as old, zipfile.ZipFile(stream, "w") as archive:
        for item in old.infolist():
            archive.writestr(item, old.read(item))
        if problem == "duplicate":
            with pytest.warns(UserWarning):
                archive.writestr(PREFIX + "semgrep-core", b"duplicate")
        elif problem == "traversal":
            archive.writestr("../outside", b"escape")
        else:
            link = zipfile.ZipInfo(PREFIX + "link")
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, "../outside")
    data = stream.getvalue()
    policy = json.loads(module.POLICY_FILE.read_text())
    selected = policy["native_semgrep"]["platforms"]["linux-x86_64"]
    selected.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    module.POLICY_FILE.write_text(json.dumps(policy))

    class Response(io.BytesIO):
        status = 200

    monkeypatch.setattr(urllib.request, "urlopen", lambda *_args, **_kwargs: Response(data))
    with pytest.raises(ValueError):
        module.provision_semgrep(tmp_path / "native")
    assert not (tmp_path / "native").exists()
    assert not (tmp_path / "outside").exists()


def test_unsupported_platform_has_no_fallback(
    payload: tuple[ModuleType, dict[str, object], bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, _, _ = payload
    monkeypatch.setattr(platform, "machine", lambda: "unselected")
    with pytest.raises(ValueError, match="platform"):
        module.provision_semgrep(tmp_path / "native")


def _cpio_entry(name: str, data: bytes, mode: int = stat.S_IFREG | 0o644) -> bytes:
    encoded = name.encode() + b"\0"
    fields = [0, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(encoded), 0]
    header = b"070701" + b"".join(f"{value:08x}".encode() for value in fields)
    prefix = header + encoded
    prefix += b"\0" * (-len(prefix) % 4)
    return prefix + data + b"\0" * (-len(data) % 4)


def _curl_fixture_cpio(problem: str, library: bytes, notice: bytes) -> bytes:
    name = "../outside" if problem == "traversal" else "usr/lib64/libcurl.so.4.7.0"
    mode = stat.S_IFLNK | 0o777 if problem == "symlink" else stat.S_IFREG | 0o644
    data = _cpio_entry(name, library, mode)
    if problem == "duplicate":
        data += _cpio_entry(name, library)
    if problem != "missing-member":
        data += _cpio_entry("usr/share/licenses/libcurl-minimal/COPYING", notice)
    if problem != "missing-trailer":
        data += _cpio_entry("TRAILER!!!", b"")
    return data


def _write_synthetic_cpio(data: bytes, command: list[str], **kwargs: object) -> None:
    assert command[:3] == ["zstd", "--decompress", "--stdout"]
    assert kwargs["timeout"] == 30
    output = kwargs["stdout"]
    assert isinstance(output, io.BufferedWriter)
    output.write(data)


@pytest.mark.parametrize(
    "problem",
    ["none", "digest", "traversal", "duplicate", "symlink", "missing-trailer", "missing-member", "size"],
)
def test_vendor_correction_is_verified_before_publication(
    payload: tuple[ModuleType, dict[str, object], bytes],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    problem: str,
) -> None:
    module, _, wheel = payload
    library = b"official vendor library"
    notice = b"official vendor notice"
    data = _curl_fixture_cpio(problem, library, notice)
    rpm = b"header" + bytes.fromhex("28b52ffd") + b"compressed"
    policy = json.loads(module.POLICY_FILE.read_text())
    policy["native_semgrep"]["platforms"]["linux-x86_64"]["curl_fix"] = {
        "url": "https://repo.almalinux.org/selected.rpm",
        "size": len(rpm),
        "sha256": hashlib.sha256(rpm).hexdigest(),
        "payload_offset": 6,
        "cpio_size": len(data),
        "cpio_sha256": "0" * 64 if problem == "digest" else hashlib.sha256(data).hexdigest(),
        "members": [
            {
                "archive_path": "usr/lib64/libcurl.so.4.7.0",
                "installed_path": "libs/libcurl.so.4",
                "size": len(library) + (1 if problem == "size" else 0),
                "sha256": hashlib.sha256(library).hexdigest(),
            },
            {
                "archive_path": "usr/share/licenses/libcurl-minimal/COPYING",
                "installed_path": "LICENSE.libcurl",
                "size": len(notice),
                "sha256": hashlib.sha256(notice).hexdigest(),
            },
        ],
    }
    module.POLICY_FILE.write_text(json.dumps(policy))

    class Response(io.BytesIO):
        status = 200

    def respond(url: str, **_kwargs: object) -> Response:
        return Response(rpm if url.endswith(".rpm") else wheel)

    monkeypatch.setattr(urllib.request, "urlopen", respond)

    monkeypatch.setattr(module.subprocess, "run", partial(_write_synthetic_cpio, data))
    destination = tmp_path / "native"
    if problem == "none":
        module.provision_semgrep(destination)
        assert (destination / "libs/libcurl.so.4").read_bytes() == library
        assert (destination / "LICENSE.libcurl").read_bytes() == notice
        module.provision_semgrep(destination)
    else:
        with pytest.raises(ValueError):
            module.provision_semgrep(destination)
        assert not destination.exists()
        assert not (tmp_path / "outside").exists()


class _NativeResponse(io.BytesIO):
    status = 200


def _pcre2_fixture_bottle(problem: str, library: bytes, notice: bytes) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as tar:
        for name, data in [("pcre2/10.49/lib/libpcre2-8.0.dylib", library), ("pcre2/10.49/LICENCE.md", notice)]:
            if problem == "missing" and name.endswith("LICENCE.md"):
                continue
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            if problem == "symlink" and name.endswith(".dylib"):
                entry.type = tarfile.SYMTYPE
                entry.linkname = "../outside"
                entry.size = 0
            tar.addfile(entry, io.BytesIO(data))
        if problem == "traversal":
            entry = tarfile.TarInfo("../outside")
            entry.size = 1
            tar.addfile(entry, io.BytesIO(b"x"))
    return stream.getvalue()


def _pcre2_download(
    request: str | urllib.request.Request, *, urls: list[str], wheel: bytes, bottle: bytes, **_kwargs: object
) -> _NativeResponse:
    url = request if isinstance(request, str) else request.full_url
    urls.append(url)
    if url.startswith("https://ghcr.io/token?"):
        assert url == "https://ghcr.io/token?service=ghcr.io&scope=repository:homebrew/core/pcre2:pull"
        return _NativeResponse(b'{"token":"public-anonymous-pull"}')
    if url.startswith("https://ghcr.io/v2/"):
        assert isinstance(request, urllib.request.Request)
        assert "Authorization" not in request.headers
        assert request.get_header("Authorization") == "Bearer public-anonymous-pull"
        return _NativeResponse(bottle)
    return _NativeResponse(wheel)


def _pcre2_fix_record(problem: str, bottle: bytes, library: bytes, notice: bytes) -> dict[str, object]:
    return {
        "package": "pcre2",
        "version": "10.49",
        "url": "https://ghcr.io/v2/homebrew/core/pcre2/blobs/sha256:"
        + ("0" * 64 if problem == "archive-digest" else hashlib.sha256(bottle).hexdigest()),
        "size": len(bottle),
        "sha256": "0" * 64 if problem == "archive-digest" else hashlib.sha256(bottle).hexdigest(),
        "members": [
            {
                "archive_path": "pcre2/10.49/lib/libpcre2-8.0.dylib",
                "installed_path": "libs/libpcre2-8.0.dylib",
                "size": len(library),
                "sha256": "0" * 64 if problem == "member-digest" else hashlib.sha256(library).hexdigest(),
            },
            {
                "archive_path": "pcre2/10.49/LICENCE.md",
                "installed_path": "LICENSE.pcre2",
                "size": len(notice),
                "sha256": hashlib.sha256(notice).hexdigest(),
            },
        ],
    }


@pytest.mark.parametrize("problem", ["none", "archive-digest", "member-digest", "symlink", "missing", "traversal"])
def test_macos_fixed_pcre2_is_authenticated_before_publication(
    payload: tuple[ModuleType, dict[str, object], bytes],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    problem: str,
) -> None:

    module, _, wheel = payload
    library, notice = b"fixed native PCRE2", b"PCRE2 supplier notice"
    bottle = _pcre2_fixture_bottle(problem, library, notice)
    policy = json.loads(module.POLICY_FILE.read_text())
    selected = policy["native_semgrep"]["platforms"].pop("linux-x86_64")
    selected["members"][1]["installed_path"] = "libs/libpcre2-8.0.dylib"
    selected["pcre2_fix"] = _pcre2_fix_record(problem, bottle, library, notice)
    policy["native_semgrep"]["platforms"]["macos-arm64"] = selected
    module.POLICY_FILE.write_text(json.dumps(policy))
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform, "machine", lambda: "arm64")

    urls: list[str] = []
    monkeypatch.setattr(urllib.request, "urlopen", partial(_pcre2_download, urls=urls, wheel=wheel, bottle=bottle))
    destination = tmp_path / "native"
    if problem == "none":
        module.provision_semgrep(destination)
        assert (destination / "libs/libpcre2-8.0.dylib").read_bytes() == library
        assert (destination / "LICENSE.pcre2").read_bytes() == notice
        count = len(urls)
        module.provision_semgrep(destination)
        assert len(urls) == count
        assert any(url.startswith("https://ghcr.io/token?") for url in urls)
    else:
        with pytest.raises(ValueError):
            module.provision_semgrep(destination)
        assert not destination.exists()
        assert not (tmp_path / "outside").exists()


def test_windows_selection_removes_ssh_and_binds_preverified_curl(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_provisioner()
    monkeypatch.setattr(module, "_platform_key", lambda: "windows-x86_64")
    selected = module._selection()
    expected = {member.destination: member for member in selected.expected}
    assert "libssh2-1.dll" not in expected, "The selected curl must not retain the affected SSH library"
    assert expected["libcurl-4.dll"].size == 638976
    assert expected["libcurl-4.dll"].digest == "bec7e6f9198d1cf7ca76482bcd2f32878191076d99325c12c92e8cbfa0fabe37"
    assert expected["osemgrep.exe"].digest == "d630d1f1f3178f17680cd438704d2d6dd8669248225c1a904aed1cd746970da2"


@pytest.mark.parametrize("problem", ["unsafe", "duplicate", "link", "expanded-bound"])
def test_build_archive_rejects_unsafe_or_oversized_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    module = load_provisioner()
    path = tmp_path / "build-input.zip"
    with zipfile.ZipFile(path, "w") as archive:
        name = "../escape" if problem == "unsafe" else "sdk/input"
        entry = zipfile.ZipInfo(name)
        if problem == "link":
            entry.create_system = 3
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(entry, b"selected input")
        if problem == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate name"):
                archive.writestr(name, b"duplicate")
    if problem == "expanded-bound":
        monkeypatch.setattr(module, "MAX_NATIVE_BYTES", 4)
    with pytest.raises(ValueError):
        module._extract_build_zip(path, tmp_path / "tool", "sdk/", omit_doc=False)
    assert not (tmp_path.parent / "escape").exists()


def test_build_archive_excludes_documentation_without_expanding_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_provisioner()
    monkeypatch.setattr(module, "MAX_NATIVE_BYTES", 8)
    path = tmp_path / "build-input.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("sdk/zig.exe", b"tool")
        archive.writestr("sdk/doc/unselected", b"not expanded" * 10)
    module._extract_build_zip(path, tmp_path / "tool", "sdk/", omit_doc=True)
    assert (tmp_path / "tool/zig.exe").read_bytes() == b"tool"
    assert not (tmp_path / "tool/doc").exists()


def test_windows_source_identities_survive_git_crlf_materialization(tmp_path: Path) -> None:
    policy = json.loads((ROOT / "ci/security-tool-minimum-versions.json").read_text())
    artifact = policy["native_semgrep"]["platforms"]["windows-x86_64"]
    paths: list[str] = ["ci/security-tool-minimum-versions.json", str(artifact["curl_fix"]["recipe"]["source"])]
    paths.extend(str(notice["source"]) for notice in artifact["notices"])
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    subprocess.run(["git", "init", str(tmp_path)], env=environment, capture_output=True, check=True, timeout=30)
    (tmp_path / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / name).read_bytes())
    subprocess.run(
        ["git", "-c", "core.autocrlf=false", "add", "--", ".gitattributes", *paths],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        check=True,
        timeout=30,
    )
    for name in paths:
        (tmp_path / name).unlink()
    subprocess.run(
        ["git", "-c", "core.autocrlf=true", "checkout-index", "--all", "--force"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert {name: (tmp_path / name).read_bytes() for name in paths} == {
        name: (ROOT / name).read_bytes() for name in paths
    }


def _archive_record(downloads: dict[str, bytes], url: str, data: bytes) -> dict[str, object]:
    downloads[url] = data
    return {"url": url, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _zip_payload(contents: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
    return stream.getvalue()


def _synthetic_windows_wheel(downloads: dict[str, bytes]) -> dict[str, object]:
    original = {"semgrep-core.exe": b"test engine", "libcurl-4.dll": b"old curl", "libssh2-1.dll": b"old ssh"}
    artifact = _archive_record(
        downloads,
        "https://files.pythonhosted.org/packages/selected.whl",
        _zip_payload({PREFIX + k: v for k, v in original.items()}),
    )
    artifact["members"] = [
        {
            "archive_path": PREFIX + name,
            "installed_path": "osemgrep.exe" if name == "semgrep-core.exe" else name,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for name, data in original.items()
    ]
    return artifact


def _synthetic_windows_curl_fix(tmp_path: Path, problem: str | None, downloads: dict[str, bytes]) -> dict[str, object]:
    archive_data = io.BytesIO()
    with tarfile.open(fileobj=archive_data, mode="w:xz") as archive:
        data = b"source notice"
        entry = tarfile.TarInfo("../escape" if problem == "source-path" else "curl-8.23.0/COPYING")
        entry.size = len(data)
        archive.addfile(entry, io.BytesIO(data))
    fix = _archive_record(downloads, "https://curl.se/download/curl-8.23.0.tar.xz", archive_data.getvalue())
    tools: dict[str, object] = {}
    for role, url, name in (
        (
            "zig",
            "https://ziglang.org/download/0.11.0/zig-windows-x86_64-0.11.0.zip",
            "zig-windows-x86_64-0.11.0/zig.exe",
        ),
        ("cmake", "https://files.pythonhosted.org/packages/cmake.whl", "cmake/data/bin/cmake.exe"),
        ("ninja", "https://github.com/ninja-build/ninja/releases/download/v1.13.2/ninja-win.zip", "ninja.exe"),
    ):
        tools[role] = _archive_record(downloads, url, _zip_payload({name: b"synthetic unexecuted tool"}))
    recipe = tmp_path / ".github/actions/setup-frozen-python/windows_curl.py"
    recipe.parent.mkdir(parents=True)
    built = b"wrong test bytes" if problem == "built-bytes" else b"fixed test curl"
    recipe.write_text(
        "def build_windows_curl(*, source, zig, cmake, ninja, build):\n"
        "    build.mkdir()\n    target = build / 'libcurl-4.dll'\n"
        f"    target.write_bytes({built!r})\n    return target\n",
        encoding="utf-8",
    )
    fixed = b"fixed test curl"
    fix.update(
        {
            "kind": "source-build",
            "package": "curl",
            "version": "8.23.0",
            "tools": tools,
            "recipe": {
                "source": recipe.relative_to(tmp_path).as_posix(),
                "size": recipe.stat().st_size,
                "sha256": hashlib.sha256(recipe.read_bytes()).hexdigest(),
            },
            "members": [
                {
                    "build_path": "libcurl-4.dll",
                    "installed_path": "libcurl-4.dll",
                    "size": len(fixed),
                    "sha256": hashlib.sha256(fixed).hexdigest(),
                }
            ],
            "remove": ["osemgrep.exe"] if problem == "remove-engine" else ["libssh2-1.dll"],
        }
    )
    return fix


def _windows_source_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str | None
) -> tuple[ModuleType, list[str], Path]:
    module = load_provisioner()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "_platform_key", lambda: "windows-x86_64")
    requests: list[str] = []
    downloads: dict[str, bytes] = {}
    artifact = _synthetic_windows_wheel(downloads)
    artifact["curl_fix"] = _synthetic_windows_curl_fix(tmp_path, problem, downloads)
    notice = tmp_path / "tools/semgrep/LICENSE"
    notice.parent.mkdir(parents=True)
    notice.write_bytes(b"supplier notice")
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "minimum_versions": {"semgrep": "1.175.0"},
                "native_semgrep": {
                    "version": "1.184.0",
                    "platforms": {"windows-x86_64": artifact},
                    "notices": [
                        {
                            "source": "tools/semgrep/LICENSE",
                            "installed_path": "LICENSE.semgrep",
                            "size": notice.stat().st_size,
                            "sha256": hashlib.sha256(notice.read_bytes()).hexdigest(),
                        }
                    ],
                },
            }
        )
    )
    monkeypatch.setattr(module, "POLICY_FILE", policy)
    if problem == "recipe-drift":
        recipe = tmp_path / ".github/actions/setup-frozen-python/windows_curl.py"
        recipe.write_bytes(recipe.read_bytes() + b"\n# deliberate isolated test drift\n")

    class Response(io.BytesIO):
        status = 200

    def fetch(url: str, **_kwargs: object) -> Response:
        requests.append(url)
        return Response(downloads[url])

    monkeypatch.setattr(urllib.request, "urlopen", fetch)
    return module, requests, tmp_path / "native output"


@pytest.mark.parametrize("problem", ["built-bytes", "recipe-drift", "remove-engine", "source-path"])
def test_invalid_windows_source_composition_does_not_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    module, requests, destination = _windows_source_fixture(tmp_path, monkeypatch, problem)
    with pytest.raises(ValueError):
        module.provision_semgrep(destination)
    assert not destination.exists()
    assert not (tmp_path.parent / "escape").exists()
    if problem in {"recipe-drift", "remove-engine"}:
        assert requests == []


def test_windows_source_composition_is_exact_and_read_only_on_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, requests, destination = _windows_source_fixture(tmp_path, monkeypatch, None)
    assert module.provision_semgrep(destination) == destination
    assert (destination / "osemgrep.exe").read_bytes() == b"test engine"
    assert (destination / "libcurl-4.dll").read_bytes() == b"fixed test curl"
    assert not (destination / "libssh2-1.dll").exists()
    requests.clear()
    assert module.provision_semgrep(destination) == destination
    monkeypatch.setattr(module.shutil, "which", lambda _name: str(destination / "osemgrep.exe"))
    inventory = module._installed_inventory()
    assert inventory["platform"] == "windows-x86_64"
    assert requests == []


def test_component_references_reject_absent_installed_file(
    payload: tuple[ModuleType, dict[str, object], bytes],
) -> None:
    module, _release, _archive = payload
    policy = json.loads(module.POLICY_FILE.read_text())
    policy["native_semgrep"]["platforms"]["linux-x86_64"]["components"] = [
        {"name": "removed-ssh", "files": ["libssh2-1.dll"], "source_info": "negative fixture", "notice_paths": []}
    ]
    module.POLICY_FILE.write_text(json.dumps(policy))
    with pytest.raises(ValueError, match=r"component.*file"):
        module._selection()
