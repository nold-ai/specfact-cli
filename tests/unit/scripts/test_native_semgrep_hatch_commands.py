import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tomllib
import venv
from pathlib import Path
from typing import Any

import certifi
import pytest
import tomli_w


ROOT = Path(__file__).resolve().parents[3]
CA_SHA = "50f79f98dac192b20dbf73f35c56f0b0c557ab267ff5199d1117cc1180b70785"
CA_REL = Path("tools/certifi") / f"cacert-{CA_SHA}.pem"
NOTICE_REL = Path("tools/certifi/LICENSE")
MISMATCH = "Selected certifi CA data mismatch; no native scan started"
SCANNERS = ["semgrep-sast", "semgrep-full", "scan", "scan-all", "scan-json", "scan-fix"]


@pytest.fixture
def project(tmp_path: Path) -> tuple[Path, str, dict[str, str]]:
    hatch = shutil.which("hatch")
    native = shutil.which("osemgrep")
    if hatch is None or native is None:
        pytest.skip("Hatch and the reviewed native Semgrep executable are required")
    root = tmp_path / "Hatch project"
    root.mkdir()
    prefix = root / ".venv"
    venv.EnvBuilder(with_pip=False).create(prefix)
    python = prefix / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    site = Path(
        subprocess.check_output(
            [str(python), "-I", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"], text=True
        ).strip()
    )
    shutil.copytree(Path(certifi.__file__).parent, site / "certifi")
    source = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["hatch"]["envs"]["default"]
    scripts = {name: source["scripts"][name] for name in SCANNERS}
    scripts["unrelated-probe"] = "python -c \"import os; print(repr(os.environ.get('SSL_CERT_FILE')))\""
    configuration = {
        "project": {"name": "native-hatch-regression", "version": "0.0.0"},
        "tool": {
            "hatch": {
                "envs": {
                    "default": {
                        "detached": True,
                        "path": ".venv",
                        "dependencies": [],
                        "env-vars": source.get("env-vars", {}),
                        "scripts": scripts,
                        "overrides": source.get("overrides", {}),
                    }
                }
            }
        },
    }
    (root / "pyproject.toml").write_text(tomli_w.dumps(configuration), encoding="utf-8")
    target = root / CA_REL
    target.parent.mkdir(parents=True)
    source_data = ROOT / CA_REL
    target.write_bytes(source_data.read_bytes() if source_data.is_file() else Path(certifi.where()).read_bytes())
    rule = (
        "rules:\n  - id: native-hatch-marker\n    languages: [python]\n"
        "    pattern: print(...)\n    message: marker\n    severity: WARNING\n"
    )
    for relative in (
        "tools/semgrep/async.yml",
        "tools/semgrep/sast.yml",
        "packages/specfact-code-review/.semgrep/clean_code.yaml",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rule, encoding="utf-8")
    (root / "example.py").write_text('print("marker")\n', encoding="utf-8")
    (root / "logs").mkdir()
    required_inputs = {
        "HOME",
        "SYSTEMROOT",
        "COMSPEC",
        "PATHEXT",
        "WINDIR",
        "TEMP",
        "TMP",
        "TMPDIR",
        "USERPROFILE",
        "LOCALAPPDATA",
        "APPDATA",
        "PYENV_ROOT",
        "PYENV_VERSION",
        "LANG",
        "LC_ALL",
    }
    environment = {key: value for key, value in os.environ.items() if key in required_inputs}
    environment.update(
        PATH=str(Path(native).parent) + os.pathsep + os.defpath,
        HATCH_DATA_DIR=str(root / "hatch-data"),
        HATCH_CACHE_DIR=str(root / "hatch-cache"),
        HATCH_PYTHON=sys.executable,
    )
    return root, hatch, environment


def _run(project: tuple[Path, str, dict[str, str]], *args: str) -> subprocess.CompletedProcess[str]:
    root, hatch, environment = project
    return subprocess.run(
        [hatch, "run", *args], cwd=root, env=environment, capture_output=True, text=True, timeout=30, check=False
    )


def _read_optional_ca(path: Path) -> bytes | None:
    return path.read_bytes() if path.exists() else None


@pytest.fixture
def ca_input_state(
    project: tuple[Path, str, dict[str, str]], case: str
) -> tuple[Path, Path, bytes | None, bytes | None]:
    root, _, environment = project
    target = root / CA_REL
    original = target.read_bytes()
    explicit = root / "explicit owner CA.pem"
    if case in {"valid", "explicit-missing-default"}:
        explicit.write_bytes(original)
        environment["SSL_CERT_FILE"] = str(explicit)
    elif case == "invalid":
        explicit.write_text("not a certificate\n", encoding="utf-8")
        environment["SSL_CERT_FILE"] = str(explicit)
    elif case == "empty":
        environment["SSL_CERT_FILE"] = ""
    if case in {"default-drift", "explicit-default"}:
        target.write_bytes(original + b"\n# data drift\n")
    if case == "explicit-default":
        environment["SSL_CERT_FILE"] = str(target)
    if case == "installed-drift":
        installed = next((root / ".venv").glob("**/site-packages/certifi/cacert.pem"))
        installed.write_bytes(original + b"\n# data drift\n")
    if case == "explicit-missing-default":
        target.unlink()
    return target, explicit, _read_optional_ca(target), _read_optional_ca(explicit)


@pytest.mark.parametrize(
    ("case", "status"),
    [
        ("unset", 0),
        ("valid", 0),
        ("invalid", 2),
        ("empty", 2),
        ("default-drift", 1),
        ("explicit-default", 0),
        ("installed-drift", 1),
        ("explicit-missing-default", 0),
    ],
)
def test_native_hatch_ca_input_states(
    project: tuple[Path, str, dict[str, str]],
    case: str,
    status: int,
    ca_input_state: tuple[Path, Path, bytes | None, bytes | None],
) -> None:
    target, explicit, before, explicit_before = ca_input_state
    result = _run(project, "scan", "--version")
    assert result.returncode == status, result.stdout + result.stderr
    if status == 0:
        assert result.stdout.strip() == "1.184.0"
    if case in {"default-drift", "installed-drift"}:
        assert MISMATCH in result.stderr.splitlines()
        assert "1.184.0" not in result.stdout
    assert _read_optional_ca(target) == before
    assert _read_optional_ca(explicit) == explicit_before


def test_native_hatch_scan_has_actual_finding(project: tuple[Path, str, dict[str, str]]) -> None:
    result = _run(project, "scan", "--json", "example.py")
    assert result.returncode == 0, result.stdout + result.stderr
    findings = json.loads(result.stdout)["results"]
    assert len(findings) == 1
    assert findings[0]["check_id"].endswith("native-hatch-marker")


def test_other_hatch_commands_keep_original_ssl_environment(project: tuple[Path, str, dict[str, str]]) -> None:
    result = _run(project, "unrelated-probe")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "None"


def test_native_ca_preflight_closes_streams(project: tuple[Path, str, dict[str, str]]) -> None:
    project[2]["PYTHONWARNINGS"] = "error::ResourceWarning"
    result = _run(project, "scan", "--version")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ResourceWarning" not in result.stderr


def _hatch_script_variants() -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    source: dict[str, Any] = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["hatch"][
        "envs"
    ]["default"]
    windows = dict(entry.split("=", 1) for entry in source["overrides"]["platform"]["windows"]["scripts"])
    explicit = dict(
        entry.split("=", 1)
        for entry in source["overrides"]["env"]["SSL_CERT_FILE"]["scripts"]
        if isinstance(entry, str)
    )
    return source, windows, explicit


@pytest.mark.parametrize("name", SCANNERS)
def test_native_hatch_command_branches_preserve_scanner_arguments(name: str) -> None:
    source, windows, explicit = _hatch_script_variants()
    assert "SSL_CERT_FILE" not in source.get("env-vars", {})
    assert "overrides" in source, "Native command branches need explicit CA and platform handling"
    commands = source["scripts"][name]
    assert isinstance(commands, list)
    assert len(commands) == 2
    assert commands[0] == source["scripts"]["scan"][0]
    last_command = commands[-1]
    assert isinstance(last_command, str)
    native = last_command.removeprefix(f"SSL_CERT_FILE={CA_REL.as_posix()} ")
    assert native.startswith("osemgrep scan --experimental --metrics=off --disable-version-check ")
    assert explicit[name] == native
    assert windows[name].rsplit(" && ", 1)[-1] == native


def test_selected_ca_matches_certifi_and_notice() -> None:
    bundle = ROOT / CA_REL
    notice = ROOT / NOTICE_REL
    assert bundle.is_file(), "Reviewed immutable CA data is missing"
    assert notice.is_file(), "Selected certifi notice is missing"
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == CA_SHA
    assert bundle.read_bytes() == Path(certifi.where()).read_bytes()
    distribution = importlib.metadata.distribution("certifi")
    license_file = next(path for path in distribution.files or [] if path.name == "LICENSE")
    assert notice.read_bytes() == Path(str(distribution.locate_file(license_file))).read_bytes()


@pytest.mark.parametrize(
    ("relative", "source_relative"),
    [
        (CA_REL, CA_REL),
        (NOTICE_REL, NOTICE_REL),
        (Path(".github/workflows/specfact.yml"), Path(".github/workflows/specfact.yml")),
        (
            Path("openspec/changes/native-semgrep-cli-remediation/requirements-proof/native-platform-operation.json"),
            Path(".github/workflows/specfact.yml"),
        ),
    ],
)
def test_git_crlf_checkout_preserves_selected_bytes(tmp_path: Path, relative: Path, source_relative: Path) -> None:
    source = ROOT / source_relative
    assert source.is_file(), "Reviewed data must exist before checkout verification"
    payload = source.read_bytes()
    environment = os.environ.copy()
    objects = tmp_path / "git-objects"
    objects.mkdir()
    environment.update(GIT_OBJECT_DIRECTORY=str(objects), GIT_ATTR_NOSYSTEM="1")
    command = ["git", "-C", str(ROOT), "-c", "core.autocrlf=true", "-c", f"core.attributesfile={os.devnull}"]
    digest = (
        subprocess.check_output([*command, "hash-object", "-w", "--stdin"], input=payload, env=environment)
        .decode()
        .strip()
    )
    checkout = subprocess.check_output(
        [*command, "cat-file", "--filters", f"--path={relative.as_posix()}", digest], env=environment
    )
    assert checkout == payload


def _linux_hatch_command(explicit_ca: bool) -> str:
    source: dict[str, Any] = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["hatch"][
        "envs"
    ]["default"]
    assert "LD_LIBRARY_PATH" not in source.get("env-vars", {})
    linux = source["overrides"]["platform"].get("linux", {}).get("scripts", [])
    commands = dict(entry.split("=", 1) for entry in linux)
    assert "scan" in commands, "Linux native scans have no private-library binding"
    command: str = commands["scan"]
    if explicit_ca:
        entries: list[str | dict[str, Any]] = source["overrides"]["env"]["SSL_CERT_FILE"]["scripts"]
        selected = [
            entry
            for entry in entries
            if isinstance(entry, dict) and entry.get("key") == "scan" and entry.get("platform") == ["linux"]
        ]
        assert len(selected) == 1
        command = selected[0]["value"]
    return command


@pytest.mark.skipif(os.name != "posix", reason="Linux command bindings use a POSIX shell")
@pytest.mark.parametrize("explicit_ca", [False, True])
@pytest.mark.parametrize("library", [None, "", "/caller/libraries"])
def test_linux_shell_binding_preserves_loader_inputs(
    project: tuple[Path, str, dict[str, str]], tmp_path: Path, explicit_ca: bool, library: str | None
) -> None:
    command = _linux_hatch_command(explicit_ca)
    probe = tmp_path / "probe" / "osemgrep"
    probe.parent.mkdir()
    probe.write_text('#!/bin/sh\nprintf "%s" "${LD_LIBRARY_PATH-UNSET}"\n', encoding="utf-8")
    probe.chmod(0o755)
    environment = project[2].copy()
    environment["PATH"] = str(probe.parent) + os.pathsep + str(project[0] / ".venv/bin") + os.pathsep + os.defpath
    if explicit_ca:
        environment["SSL_CERT_FILE"] = certifi.where()
    if library is not None:
        environment["LD_LIBRARY_PATH"] = library
    result = subprocess.run(
        ["bash", "-e", "-c", command.replace("{args}", "--version")],
        cwd=project[0],
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ("$ORIGIN/libs" if library is None else library)
