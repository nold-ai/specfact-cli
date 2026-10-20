"""Private candidate verification. Runtime success does not authorize publication/adoption."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import platform
import re
import subprocess
import sys
import sysconfig
import tomllib
import urllib.parse
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast, final


ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    "uv_install",
    "pip_install",
    "pip_check",
    "inventory",
    "cli",
    "python_entry",
    "positive_control",
    "negative_control",
    "mcp_stdio",
    "mcp_lifecycle",
    "migration",
    "lineage",
)
RECIPE = ROOT / "ci/semgrep-distribution.json"
RUNTIME = ROOT / "ci/semgrep-runtime.json"
FORK = "specfact-semgrep"
VERSION = "1.179.0.post1"
PYTHONS = ("3.11", "3.12", "3.13")
RECIPE_SHA256 = "bcb7d9ce9cb05fb479069af7c0eaebe816adbea338ceb269642c731de18bcb0c"
SOURCE_FILES = (
    "scripts/semgrep_distribution.py",
    "scripts/candidate_runner.py",
    "ci/semgrep-distribution.json",
    "ci/semgrep-runtime.json",
    ".github/workflows/semgrep-candidate.yml",
    "tools/downstream_semgrep/test_mcp_regressions.py",
    "tools/downstream_semgrep/mcp_lifecycle_defaults.py",
    "tools/downstream_semgrep/candidate-rule.yml",
    "tools/downstream_semgrep/positive.py.txt",
    "tools/downstream_semgrep/negative.py.txt",
    "uv.lock",
)


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in cast(dict[object, object], value)):
        raise ValueError("expected string-keyed object")
    return cast(dict[str, object], value)


def _list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("expected list")
    return cast(list[object], value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("expected nonempty text")
    return value


def _json_object(text: str) -> dict[str, object]:
    return _object(cast(object, json.loads(text)))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


@final
class _Cell:
    def __init__(self, output: Path, report: dict[str, object]):
        self.output = output
        self.report = report
        self.commands: list[dict[str, object]] = []
        self.report["commands"] = self.commands
        self.checks: dict[str, bool] = dict.fromkeys(CHECKS, False)
        self.report["checks"] = self.checks
        self.sequence = 0
        self.environment = {
            key: value for key, value in os.environ.items() if not key.upper().startswith(("UV_", "PIP_", "PYTHON"))
        }
        self.environment.update(
            UV_NO_CONFIG="1",
            UV_DEFAULT_INDEX="https://pypi.org/simple",
            PIP_CONFIG_FILE=os.devnull,
            PIP_INDEX_URL="https://pypi.org/simple",
            SEMGREP_SEND_METRICS="off",
            SEMGREP_ENABLE_VERSION_CHECK="0",
        )
        self.environment["SEMGREP_SETTINGS_FILE"] = str(output / "semgrep-settings.yml")

    def run(
        self,
        label: str,
        command: list[str],
        expected: tuple[int, ...] = (0,),
        timeout: int = 120,
    ) -> subprocess.CompletedProcess[str]:
        self.sequence += 1
        _ = sys.stderr.write(f"{self.sequence:02d} {label}\n")
        stem = self.output / f"{self.sequence:02d}-{label}"
        environment = dict(self.environment)
        if Path(command[0]).name.lower() in {"python", "python.exe"}:
            environment["PATH"] = str(Path(command[0]).parent) + os.pathsep + environment.get("PATH", "")

        def decoded(value: bytes | str | None) -> str:
            text = value.decode("utf-8") if isinstance(value, bytes) else value or ""
            return text.replace("\r\n", "\n").replace("\r", "\n")

        try:
            captured = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            proc = subprocess.CompletedProcess(
                command,
                captured.returncode,
                decoded(captured.stdout),
                decoded(captured.stderr),
            )
        except subprocess.TimeoutExpired as error:
            proc = subprocess.CompletedProcess(
                command,
                124,
                decoded(error.stdout),
                decoded(error.stderr) + "\nExternal process timeout\n",
            )
        stdout, stderr = stem.with_suffix(".stdout"), stem.with_suffix(".stderr")
        _ = stdout.write_text(proc.stdout, encoding="utf-8")
        _ = stderr.write_text(proc.stderr, encoding="utf-8")
        self.commands.append(
            {
                "argv": command,
                "returncode": proc.returncode,
                "stdout_file": stdout.name,
                "stderr_file": stderr.name,
                "stdout_sha256": _digest(stdout),
                "stderr_sha256": _digest(stderr),
            }
        )
        if proc.returncode not in expected:
            raise RuntimeError(f"{label} exited {proc.returncode}; see {stem}")
        return proc


def _musl_runtime() -> list[str]:
    loaders = list(Path("/lib").glob("ld-musl-*.so.1"))
    if len(loaders) != 1:
        raise ValueError("native musl loader unavailable or ambiguous")
    probe = subprocess.run([str(loaders[0])], capture_output=True, text=True, check=False, timeout=30)
    match = re.search(r"Version (\d+)\.(\d+)", probe.stderr + probe.stdout)
    if match is None:
        raise ValueError("musl version unavailable")
    return ["musl", match.group(0)]


def _official_wheel_url(url: str, filename: str) -> urllib.parse.SplitResult:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "files.pythonhosted.org" or parsed.query or parsed.fragment:
        raise ValueError("upstream URL must be an exact files.pythonhosted.org HTTPS artifact")
    if (
        Path(filename).name != filename
        or not filename.endswith(".whl")
        or urllib.parse.unquote(parsed.path).split("/")[-1] != filename
    ):
        raise ValueError("upstream filename mismatch")
    return parsed


def _download(record: dict[str, object], output: Path) -> Path:
    filename = _text(record["filename"])
    parsed = _official_wheel_url(_text(record["upstream_url"]), filename)
    target = output / filename
    connection = http.client.HTTPSConnection("files.pythonhosted.org", timeout=120)
    try:
        connection.request("GET", parsed.path)
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"official wheel HTTP status {response.status}; redirects forbidden")
        with target.open("wb") as stream:
            while chunk := response.read(1024 * 1024):
                _ = stream.write(chunk)
    finally:
        connection.close()
    if _digest(target) != _text(record["upstream_sha256"]):
        raise ValueError("official upstream wheel hash mismatch")
    return target


def _locked_versions() -> dict[str, str]:
    lock = _object(cast(object, tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))))
    versions: dict[str, set[str]] = {}
    for value in _list(lock["package"]):
        package = _object(value)
        key = _name(_text(package["name"]))
        if _object(package.get("source", {})).get("registry") and key not in {
            "semgrep",
            "mcp",
        }:
            versions.setdefault(key, set()).add(_text(package["version"]))
    if any(len(values) != 1 for values in versions.values()):
        raise ValueError("protected uv.lock contains multiple versions; explicit marker-aware constraints required")
    return {key: next(iter(values)) for key, values in versions.items()}


def _constraints(target: Path) -> None:
    versions = _locked_versions()
    _ = target.write_text(
        "".join(f"{package}=={versions[package]}\n" for package in sorted(versions)),
        encoding="utf-8",
    )


def _python_in(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _inventory(cell: _Cell, executable: Path, label: str) -> dict[str, str]:
    program = "import importlib.metadata as m,json,re,sys; d={};\nfor p in m.distributions():\n n=re.sub(r'[-_.]+','-',p.metadata['Name']).lower()\n if n in d: raise RuntimeError('duplicate distribution '+n)\n d[n]=p.version\nsys.stdout.write(json.dumps(d,sort_keys=True))"
    payload = _json_object(cell.run(label, [str(executable), "-c", program]).stdout)
    return {key: _text(value) for key, value in payload.items()}


def _compiled_pins(compiled: Path) -> dict[str, tuple[str, list[str]]]:
    blocks = re.sub(r"\\\r?\n", " ", compiled.read_text(encoding="utf-8")).splitlines()
    pinned: dict[str, tuple[str, list[str]]] = {}
    for line in blocks:
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;]+)(.*)$", line)
        if match is None:
            continue
        package, version, tail = match.groups()
        key = _name(package)
        if key in pinned:
            raise ValueError(f"duplicate compiled identity {key}")
        if ";" in tail:
            raise ValueError("marker-bearing lock requires actual resolver materialization, not marker guessing")
        pinned[key] = (version, re.findall(r"--hash=sha256:([a-f0-9]{64})", tail))
    return pinned


def _uv_wheel(record: dict[str, object], version: str) -> tuple[str, str]:
    filename, sha = _text(record["filename"]), _text(record["sha256"])
    _ = _official_wheel_url(_text(record["url"]), filename)
    architecture = re.search(r"musllinux_\d+_\d+_(aarch64|x86_64)\.whl$", filename)
    if not filename.startswith(f"uv-{version}-py3-none-") or architecture is None:
        raise ValueError("invalid exact uv wheel identity")
    if not re.fullmatch(r"[a-f0-9]{64}", sha):
        raise ValueError("invalid uv wheel hash")
    return sha, architecture.group(1)


def _uv_requirements(recipe_path: Path) -> str:
    bootstrap = _object(_json_object(recipe_path.read_text(encoding="utf-8"))["uv_bootstrap"])
    version = _text(bootstrap["version"])
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("invalid exact uv version")
    wheels = [_uv_wheel(_object(value), version) for value in _list(bootstrap["wheels"])]
    if len(wheels) != 2 or {arch for _, arch in wheels} != {"aarch64", "x86_64"}:
        raise ValueError("exactly two distinct native musl uv wheels required")
    hashes = {sha for sha, _ in wheels}
    if len(hashes) != 2:
        raise ValueError("duplicate uv bootstrap wheel hash")
    return f"uv=={version} " + " ".join(f"--hash=sha256:{sha}" for sha in sorted(hashes)) + "\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict[str, object]:
    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in values:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    return _object(cast(object, json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)))


def write_json(path: Path, value: object) -> None:
    _ = path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_hash(path: Path, expected: str) -> None:
    require(bool(re.fullmatch("[a-f0-9]{64}", expected)), "invalid digest")
    require(path.is_file() and not path.is_symlink(), "artifact must be regular file")
    require(_digest(path) == expected, "artifact hash mismatch: " + path.name)


def matrix(recipe: dict[str, object], runtime: dict[str, object]) -> dict[str, object]:
    source = [_object(row) for row in _list(recipe["wheels"])]
    rows = [_object(row) for row in _list(runtime["wheels"])]
    platforms = [_text(row["platform_tag"]) for row in source]
    keys = [_text(row["platform_tag"]) for row in rows]
    require(
        len(platforms) == len(set(platforms)) == 7,
        "recipe needs seven unique platforms",
    )
    require(
        len(keys) == len(set(keys)) == 7 and set(keys) == set(platforms),
        "runtime platform set differs",
    )
    require(runtime["python_versions"] == list(PYTHONS), "exact Python matrix required")
    cells: list[dict[str, str]] = []
    for row in rows:
        tag = _text(row["platform_tag"])
        containers = _object(row["containers"])
        require(
            set(containers) == (set(PYTHONS) if tag.startswith("musllinux") else set()),
            "container keys differ",
        )
        for version in PYTHONS:
            container = str(containers.get(version, ""))
            if tag.startswith("musllinux"):
                require(
                    bool(
                        re.fullmatch(
                            r"python:" + re.escape(version) + r"-alpine[^@]+@sha256:[a-f0-9]{64}",
                            container,
                        )
                    ),
                    "musl container is not digest pinned",
                )
            cells.append(
                {
                    "platform": tag,
                    "python_version": version,
                    "runner": _text(row["runner"]),
                    "container_image": container,
                }
            )
    return {"include": cells}


def validate_host(tag: str, version: str, observed: dict[str, object]) -> None:
    require(observed["implementation"] == "CPython", "CPython required")
    require(
        str(observed["python_version"]).split(".")[:2] == version.split("."),
        "actual Python differs",
    )
    machine = str(observed["machine"]).lower()
    architecture = (
        "aarch64" if machine in {"arm64", "aarch64"} else "x86_64" if machine in {"amd64", "x86_64"} else machine
    )
    wanted = "aarch64" if tag.endswith(("arm64", "aarch64")) else "x86_64"
    require(architecture == wanted, "actual native architecture differs")
    system = "Windows" if tag == "win_amd64" else "Darwin" if tag.startswith("macosx") else "Linux"
    require(observed["system"] == system, "actual operating system differs")
    if system == "Linux":
        libc = _list(observed["libc"])
        kind = "musl" if tag.startswith("musllinux") else "glibc"
        require(len(libc) == 2 and libc[0] == kind, "actual libc differs")
        numbers = re.search(r"(\d+)\.(\d+)", str(libc[1]))
        if numbers is None:
            raise ValueError("actual libc version unavailable")
        minimum = (1, 2) if kind == "musl" else (2, 34)
        require(tuple(map(int, numbers.groups())) >= minimum, "actual libc below tag floor")


def host(tag: str, version: str) -> dict[str, object]:
    observed: dict[str, object] = {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "libc": _musl_runtime() if tag.startswith("musllinux") else list(platform.libc_ver()),
        "executable": sys.executable,
        "executable_sha256": _digest(Path(sys.executable)),
        "sysconfig_platform": sysconfig.get_platform(),
    }
    validate_host(tag, version, observed)
    return observed


def normalize_inventory(rows: list[dict[str, str]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        name = _name(row["name"])
        require(name not in result, "duplicate normalized distribution")
        result[name] = row["version"]
    return result


def validate_inventory(installed: dict[str, str]) -> None:
    require(
        installed.get(FORK) == VERSION and "semgrep" not in installed,
        "wrong or overlapping scanner ownership",
    )
    require(installed.get("mcp") == "1.30.0", "MCP version differs")
    version = installed.get("certifi", "")
    require(bool(re.fullmatch(r"\d+\.\d+\.\d+", version)), "certifi version unavailable")
    require(
        tuple(map(int, version.split("."))) >= (2026, 10, 19),
        "certifi below approved floor",
    )


def _flat_lock(compiled: Path, installed: dict[str, str], wheel: Path, output: Path) -> None:
    pins = _compiled_pins(compiled)
    direct = re.findall(r"^specfact[-_]semgrep\s*@\s*(\S+)", compiled.read_text(), re.MULTILINE)
    require(len(direct) == 1, "exactly one candidate direct requirement required")
    direct_lines = re.sub(r"\\\r?\n", " ", compiled.read_text()).splitlines()
    candidate_lines = [line for line in direct_lines if re.match(r"^specfact[-_]semgrep\s*@\s*", line)]
    require(
        len(candidate_lines) == 1 and "--hash=sha256:" + _digest(wheel) in candidate_lines[0],
        "compiled candidate hash differs",
    )
    require(installed.get(FORK) == VERSION, "candidate inventory identity differs")
    require(
        set(pins) == set(installed) - {FORK},
        "compiled and actual dependency sets differ",
    )
    lines: list[str] = []
    for name, version in sorted(installed.items()):
        hashes = [_digest(wheel)] if name == FORK else pins[name][1]
        require(
            name == FORK or pins[name][0] == version,
            "compiled inventory version differs",
        )
        require(bool(hashes), "installed dependency lacks artifact hashes")
        lines.append(f"{name}=={version} " + " ".join("--hash=sha256:" + value for value in hashes))
    _ = output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_coverage(expected: dict[str, str], payload: dict[str, object]) -> None:
    actual: dict[str, str] = {}
    for value in _list(payload["dependencies"]):
        row = _object(value)
        name = _name(_text(row["name"]))
        require(
            name not in actual and "skip_reason" not in row,
            "duplicate or skipped audit coverage",
        )
        require(_list(row["vulns"]) == [], "advisory finding remains")
        actual[name] = _text(row["version"])
    require(actual == expected, "audited inventory does not equal expected inventory")


def _validate_report(
    report: dict[str, object], manifest: dict[str, object], wheels: dict[str, dict[str, object]]
) -> None:
    require(
        report["status"] == "runtime-passed" and report["native"] is True,
        "native cell did not pass",
    )
    require(
        report["checks"] == dict.fromkeys(CHECKS, True),
        "missing or failed runtime checks",
    )
    for field in (
        "source_commit",
        "source_files",
        "recipe_sha256",
        "runtime_sha256",
    ):
        require(report[field] == manifest[field], "mixed " + field)
    wheel = wheels[str(report["platform"])]
    require(
        report["candidate_sha256"] == wheel["sha256"] and report["upstream_sha256"] == wheel["upstream_sha256"],
        "mixed wheel bytes",
    )
    validate_inventory(cast(dict[str, str], report["actual_inventory"]))
    require(
        report["audit_status"] == "pending-unpublished-fork",
        "unexpected advisory status",
    )


def aggregate(
    manifest: dict[str, object],
    reports: list[dict[str, object]],
    recipe: dict[str, object],
    runtime: dict[str, object],
) -> dict[str, object]:
    cells = [_object(c) for c in _list(matrix(recipe, runtime)["include"])]
    expected = {(c["platform"], c["python_version"]) for c in cells}
    rows = [_object(w) for w in _list(manifest["wheels"])]
    wheels = {_text(w["platform"]): w for w in rows}
    require(
        len(rows) == len(wheels) == 7 and set(wheels) == {c[0] for c in expected},
        "canonical manifest wheel set differs",
    )
    seen: set[tuple[object, object]] = set()
    pending: set[str] = set()
    for report in reports:
        key = (report["platform"], report["python_version"])
        require(key in expected and key not in seen, "duplicate or unexpected runtime cell")
        seen.add(key)
        _validate_report(report, manifest, wheels)
        pending.update(_text(item) for item in _list(report["pending"]))
    require(seen == expected, "missing native runtime cells")
    require(
        "actual-fork-advisory-lookup" in pending,
        "unpublished identity cannot be called clean",
    )
    return {
        "status": "candidate-runtime-passed-publication-pending",
        "cells": len(seen),
        "source_commit": manifest["source_commit"],
        "recipe_sha256": manifest["recipe_sha256"],
        "wheels": rows,
        "pending": sorted(pending),
        "canonical_security_audit_passed": False,
    }


def source_binding(cell: _Cell, expected: str) -> dict[str, object]:
    commit = cell.run("source-head", ["git", "rev-parse", "HEAD"]).stdout.strip()
    require(
        bool(re.fullmatch("[a-f0-9]{40}", expected)) and commit == expected,
        "source SHA differs",
    )
    require(
        not cell.run("source-clean", ["git", "status", "--porcelain", "--untracked-files=no"]).stdout.strip(),
        "tracked source is dirty",
    )
    tracked = set(cell.run("source-files", ["git", "ls-files", "--", *SOURCE_FILES]).stdout.splitlines())
    require(tracked == set(SOURCE_FILES), "source inputs must all be tracked")
    return {
        "source_commit": commit,
        "source_files": {name: _digest(ROOT / name) for name in SOURCE_FILES},
    }


def canonical_build(recipe_path: Path, runtime_path: Path, output: Path, source: str) -> None:
    require(
        platform.python_version() == "3.13.14"
        and platform.python_implementation() == "CPython"
        and platform.system() == "Linux",
        "canonical producer requires Linux CPython 3.13.14",
    )
    output.mkdir(parents=True, exist_ok=False)
    cell = _Cell(output, {})
    assert_hash(recipe_path, RECIPE_SHA256)
    recipe = read_json(recipe_path)
    _ = matrix(recipe, read_json(runtime_path))
    binding = source_binding(cell, source)
    from semgrep_distribution import build

    wheels: list[dict[str, object]] = []
    upstream_dir = output / "upstream"
    upstream_dir.mkdir()
    for value in _list(recipe["wheels"]):
        row = _object(value)
        upstream = _download(row, upstream_dir)
        first = build(recipe_path, upstream, output / "wheels")
        second = build(recipe_path, upstream, output / "rebuild")
        require(first["sha256"] == second["sha256"], "same-runtime reproducibility failed")
        path = Path(str(first["path"]))
        require(
            path.stat().st_size < 100_000_000,
            "candidate exceeds conservative 100 MB publication budget",
        )
        wheels.append(
            {
                "platform": row["platform_tag"],
                "filename": path.name,
                "sha256": first["sha256"],
                "upstream_sha256": row["upstream_sha256"],
                "bytes": path.stat().st_size,
            }
        )
    manifest = dict(
        binding,
        recipe_sha256=_digest(recipe_path),
        runtime_sha256=_digest(runtime_path),
        python=sys.version,
        zlib=zlib.ZLIB_RUNTIME_VERSION,
        wheels=wheels,
        candidate_only=True,
    )
    write_json(output / "manifest.json", manifest)


def _pip_install_graph(cell: _Cell, lock: Path, flat: Path, installed: dict[str, str]) -> None:
    pip_env = cell.output / "pip-env"
    _ = cell.run("pip-venv", [sys.executable, "-m", "venv", "--without-pip", str(pip_env)])
    pip_python = _python_in(pip_env)
    pip_bootstrap = cell.output / "pip-bootstrap.txt"
    _ = pip_bootstrap.write_text(
        next(line for line in flat.read_text().splitlines() if line.startswith("pip==")) + "\n",
        encoding="utf-8",
    )
    _ = cell.run(
        "pip-bootstrap",
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(pip_python),
            "--require-hashes",
            "--requirement",
            str(pip_bootstrap),
        ],
        timeout=240,
    )
    _ = cell.run(
        "pip-install",
        [
            str(pip_python),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "--requirement",
            str(lock),
        ],
        timeout=1200,
    )
    _ = cell.run("pip-check", [str(pip_python), "-m", "pip", "check"])
    require(
        _inventory(cell, pip_python, "pip-inventory") == installed,
        "normal pip/uv installed graphs differ",
    )
    scanner_checks(cell, pip_python, "pip")
    cell.checks["pip_install"] = True


def prepare(cell: _Cell, wheel: Path, constraints: Path) -> tuple[Path, dict[str, str], Path]:
    environment = cell.output / "uv-env"
    executable = _python_in(environment)
    source = cell.output / "candidate.in"
    versions = _locked_versions()
    _ = source.write_text(
        str(wheel)
        + "\n"
        + "\n".join(f"{tool}=={versions[tool]}" for tool in ("pip", "pip-audit", "icontract", "beartype"))
        + "\ncertifi>=2026.10.19\n",
        encoding="utf-8",
    )
    lock = cell.output / "candidate.locked.txt"
    _ = cell.run("uv-venv", ["uv", "venv", "--python", sys.executable, str(environment)])
    _ = cell.run(
        "uv-compile",
        [
            "uv",
            "pip",
            "compile",
            str(source),
            "--python",
            str(executable),
            "--constraint",
            str(constraints),
            "--generate-hashes",
            "--output-file",
            str(lock),
        ],
        timeout=1200,
    )
    _ = cell.run(
        "uv-install",
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(executable),
            "--require-hashes",
            "--requirement",
            str(lock),
        ],
        timeout=1200,
    )
    _ = cell.run("uv-pip-check", [str(executable), "-m", "pip", "check"])
    installed = _inventory(cell, executable, "uv-inventory")
    validate_inventory(installed)
    flat = cell.output / "actual-hashed.txt"
    _flat_lock(lock, installed, wheel, flat)
    cell.checks.update(uv_install=True, pip_check=True, inventory=True)
    _pip_install_graph(cell, lock, flat, installed)
    return executable, installed, flat


def scanner_checks(cell: _Cell, executable: Path, label: str) -> None:
    directory = ROOT / "tools/downstream_semgrep"
    fixtures = cell.output / "scanner-fixtures"
    fixtures.mkdir(exist_ok=True)
    for filename in ("positive.py", "negative.py"):
        _ = (fixtures / filename).write_bytes((directory / (filename + ".txt")).read_bytes())
    prefixes = {
        "cli": [str(executable.parent / ("semgrep.exe" if os.name == "nt" else "semgrep"))],
        "python_entry": [str(executable), "-m", "semgrep.console_scripts.pysemgrep"],
    }
    for key, prefix in prefixes.items():
        base = [
            *prefix,
            "scan",
            "--metrics=off",
            "--disable-version-check",
            "--json",
            "--error",
            "--config",
            str(directory / "candidate-rule.yml"),
        ]
        positive = cell.run(
            label + "-" + key + "-positive",
            [*base, str(fixtures / "positive.py")],
            expected=(1,),
            timeout=240,
        )
        negative = cell.run(
            label + "-" + key + "-negative",
            [*base, str(fixtures / "negative.py")],
            timeout=240,
        )
        pos, neg = _json_object(positive.stdout), _json_object(negative.stdout)
        require(
            not pos.get("errors") and not neg.get("errors") and neg.get("results") == [],
            "scanner control errors",
        )
        findings = _list(pos["results"])
        require(len(findings) == 1, "scanner positive control missing")
        finding = _object(findings[0])
        require(
            Path(_text(finding["path"])).name == "positive.py"
            and _object(finding["start"])["line"] == 1
            and str(finding["check_id"]).endswith("downstream-positive"),
            "finding identity/path/line differs",
        )
        cell.checks[key] = True
    cell.checks.update(positive_control=True, negative_control=True)


def _upstream_control(cell: _Cell, upstream: Path, constraints: Path) -> Path:
    environment = cell.output / "migration-env"
    python = _python_in(environment)
    versions = _locked_versions()
    _ = cell.run("migration-venv", ["uv", "venv", "--python", sys.executable, str(environment)])
    old_source = cell.output / "migration-old.in"
    _ = old_source.write_text(
        str(upstream)
        + "\n"
        + "\n".join(f"{tool}=={versions[tool]}" for tool in ("pip", "pip-audit", "icontract", "beartype"))
        + "\n",
        encoding="utf-8",
    )
    old_lock = cell.output / "migration-old.locked.txt"
    _ = cell.run(
        "migration-old-compile",
        [
            "uv",
            "pip",
            "compile",
            str(old_source),
            "--python",
            str(python),
            "--constraint",
            str(constraints),
            "--generate-hashes",
            "--output-file",
            str(old_lock),
        ],
        timeout=1200,
    )
    _ = cell.run(
        "migration-old-install",
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--require-hashes",
            "--requirement",
            str(old_lock),
        ],
        timeout=1200,
    )
    before = _inventory(cell, python, "migration-before")
    require(
        before.get("semgrep") == "1.179.0" and FORK not in before and before.get("mcp") == "1.29.0",
        "old environment is not upstream control",
    )
    control = cell.run(
        "migration-old-mcp-regression",
        [str(python), str(ROOT / "tools/downstream_semgrep/test_mcp_regressions.py"), "TestMcpLifecycle"],
        expected=(1,),
        timeout=120,
    )
    require(
        "FAILED (failures=8)" in control.stderr
        and "DELETE retained a registered session" in control.stderr
        and "ERROR:" not in control.stderr,
        "old MCP control failed for an unexpected reason",
    )
    return python


def migration(cell: _Cell, upstream: Path, installed: dict[str, str], constraints: Path) -> None:
    python = _upstream_control(cell, upstream, constraints)
    _ = cell.run(
        "migration-uninstall-upstream",
        [str(python), "-m", "pip", "uninstall", "--yes", "semgrep"],
    )
    require(
        "semgrep" not in _inventory(cell, python, "migration-after-uninstall"),
        "upstream distribution retained",
    )
    _ = cell.run(
        "migration-fork-install",
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "--requirement",
            str(cell.output / "candidate.locked.txt"),
        ],
        timeout=1200,
    )
    _ = cell.run("migration-pip-check", [str(python), "-m", "pip", "check"])
    require(
        _inventory(cell, python, "migration-after") == installed,
        "migration graph differs",
    )
    scanner_checks(cell, python, "migration")
    cell.checks["migration"] = True


def audits(cell: _Cell, executable: Path, installed: dict[str, str], flat: Path, upstream: Path) -> None:
    additive = dict(installed, semgrep="1.179.0")
    write_json(
        cell.output / "advisory-subjects.json",
        {
            "label": "prepublication-additive-lineage-auditor-input",
            "actual_inventory": installed,
            "additional_upstream_code_identity": {"semgrep": "1.179.0"},
            "all_subjects": additive,
            "pending_actual_fork": FORK,
        },
    )
    known = {name: version for name, version in additive.items() if name != FORK}
    known_file = cell.output / "known-lineage-audit.txt"
    lines = [line for line in flat.read_text().splitlines() if not line.startswith(FORK + "==")]
    lines.append("semgrep==1.179.0 --hash=sha256:" + _digest(upstream))
    _ = known_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    proc = cell.run(
        "known-lineage-audit",
        [
            str(executable),
            "-m",
            "pip_audit",
            "--strict",
            "--disable-pip",
            "--requirement",
            str(known_file),
            "--format",
            "json",
        ],
        expected=(0, 1),
        timeout=240,
    )
    audit_coverage(known, _json_object(proc.stdout))
    require(proc.returncode == 0, "known inventory audit returned failure")
    cell.report["audit_status"] = "pending-unpublished-fork"
    cell.report["pending"] = [
        "actual-fork-advisory-lookup",
        "public-registry-discovery",
        "core-analyzer-contract",
        "core-installed-module-contract",
        "redistribution-source-license-review",
        "final-exact-head-human-requirements-authority",
    ]


@dataclass(frozen=True)
class _CellInputs:
    recipe_path: Path
    runtime_path: Path
    bundle: Path
    tag: str
    version: str
    output: Path
    source: str


def _verified_cell_artifacts(cell: _Cell, inputs: _CellInputs) -> tuple[Path, Path]:
    recipe, runtime, manifest = (
        read_json(inputs.recipe_path),
        read_json(inputs.runtime_path),
        read_json(inputs.bundle / "manifest.json"),
    )
    require(
        any(
            _object(c)["platform"] == inputs.tag and _object(c)["python_version"] == inputs.version
            for c in _list(matrix(recipe, runtime)["include"])
        ),
        "cell outside matrix",
    )
    cell.report["runtime"] = host(inputs.tag, inputs.version)
    cell.report["native"] = True
    binding = source_binding(cell, inputs.source)
    require(
        all(binding[key] == manifest[key] for key in binding),
        "canonical source binding differs",
    )
    cell.report.update(binding)
    for key, path in [
        ("recipe_sha256", inputs.recipe_path),
        ("runtime_sha256", inputs.runtime_path),
    ]:
        assert_hash(path, _text(manifest[key]))
        cell.report[key] = manifest[key]
    assert_hash(inputs.recipe_path, RECIPE_SHA256)
    matches = [_object(w) for w in _list(manifest["wheels"]) if _object(w)["platform"] == inputs.tag]
    require(len(matches) == 1, "canonical wheel missing or duplicated")
    row = matches[0]
    filename = _text(row["filename"])
    require(Path(filename).name == filename, "unsafe wheel filename")
    wheel = inputs.bundle / "wheels" / filename
    assert_hash(wheel, _text(row["sha256"]))
    upstream_row = next(_object(w) for w in _list(recipe["wheels"]) if _object(w)["platform_tag"] == inputs.tag)
    upstream = _download(upstream_row, inputs.output)
    require(
        row["upstream_sha256"] == upstream_row["upstream_sha256"],
        "canonical lineage source differs",
    )
    from semgrep_distribution import verify

    verified = verify(inputs.recipe_path, upstream, wheel)
    require(verified["sha256"] == row["sha256"], "semantic verification bytes differ")
    cell.report.update(candidate_sha256=row["sha256"], upstream_sha256=row["upstream_sha256"])
    cell.checks["lineage"] = True
    cell.report["uv_version"] = cell.run("uv-version", ["uv", "--version"]).stdout.strip()
    require(
        str(cell.report["uv_version"]).split()[1] == _object(runtime["uv_bootstrap"])["version"],
        "uv runtime version differs",
    )
    return wheel, upstream


def execute_cell(inputs: _CellInputs) -> int:
    inputs.output.mkdir(parents=True, exist_ok=False)
    report: dict[str, object] = {
        "status": "failed",
        "candidate_only": True,
        "platform": inputs.tag,
        "python_version": inputs.version,
        "native": False,
    }
    cell = _Cell(inputs.output, report)
    try:
        wheel, upstream = _verified_cell_artifacts(cell, inputs)
        constraints = inputs.output / "constraints.txt"
        _constraints(constraints)
        assert_hash(wheel, _text(report["candidate_sha256"]))
        executable, installed, flat = prepare(cell, wheel, constraints)
        report["actual_inventory"] = installed
        scanner_checks(cell, executable, "candidate")
        _ = cell.run(
            "candidate-mcp-regressions",
            [
                str(executable),
                str(ROOT / "tools/downstream_semgrep/test_mcp_regressions.py"),
            ],
            timeout=240,
        )
        cell.checks.update(mcp_stdio=True, mcp_lifecycle=True)
        migration(cell, upstream, installed, constraints)
        audits(cell, executable, installed, flat, upstream)
        require(cell.checks == dict.fromkeys(CHECKS, True), "runtime checks incomplete")
        report["status"] = "runtime-passed"
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as error:
        report["failure"] = f"{type(error).__name__}: {error}"
        return 1
    finally:
        write_json(inputs.output / "report.json", report)


class Arguments(Protocol):
    command: str
    recipe: Path
    runtime: Path
    output: Path
    source_commit: str
    bundle: Path
    platform: str
    python_version: str
    reports: Path


def _report_evidence(reports_root: Path, paths: list[Path], reports: list[dict[str, object]]) -> dict[str, str]:
    evidence: dict[str, str] = {}
    for path, report in zip(paths, reports, strict=True):
        evidence[path.relative_to(reports_root).as_posix()] = _digest(path)
        for value in _list(report["commands"]):
            command = _object(value)
            for stream in ("stdout", "stderr"):
                filename = _text(command[stream + "_file"])
                require(Path(filename).name == filename, "unsafe output filename")
                artifact = path.parent / filename
                assert_hash(artifact, _text(command[stream + "_sha256"]))
                evidence[artifact.relative_to(reports_root).as_posix()] = _digest(artifact)
    return evidence


def _collect_reports(args: Arguments) -> None:
    manifest = read_json(args.bundle / "manifest.json")
    assert_hash(args.recipe, _text(manifest["recipe_sha256"]))
    assert_hash(args.runtime, _text(manifest["runtime_sha256"]))
    for value in _list(manifest["wheels"]):
        wheel = _object(value)
        filename = _text(wheel["filename"])
        require(Path(filename).name == filename, "unsafe manifest wheel path")
        assert_hash(args.bundle / "wheels" / filename, _text(wheel["sha256"]))
    paths = sorted(args.reports.rglob("report.json"))
    reports = [read_json(path) for path in paths]
    result = aggregate(manifest, reports, read_json(args.recipe), read_json(args.runtime))
    result["evidence_sha256"] = _report_evidence(args.reports, paths, reports)
    write_json(args.output, result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--recipe", type=Path, default=RECIPE)
    _ = parser.add_argument("--runtime", type=Path, default=RUNTIME)
    sub = parser.add_subparsers(dest="command", required=True)
    _ = sub.add_parser("matrix")
    _ = sub.add_parser("uv-requirements")
    build = sub.add_parser("build")
    _ = build.add_argument("--output", type=Path, required=True)
    _ = build.add_argument("--source-commit", required=True)
    run = sub.add_parser("cell")
    _ = run.add_argument("--bundle", type=Path, required=True)
    _ = run.add_argument("--platform", required=True)
    _ = run.add_argument("--python-version", required=True)
    _ = run.add_argument("--output", type=Path, required=True)
    _ = run.add_argument("--source-commit", required=True)
    collect = sub.add_parser("aggregate")
    _ = collect.add_argument("--bundle", type=Path, required=True)
    _ = collect.add_argument("--reports", type=Path, required=True)
    _ = collect.add_argument("--output", type=Path, required=True)
    args = cast(Arguments, cast(object, parser.parse_args()))
    if args.command == "matrix":
        print(
            json.dumps(
                matrix(read_json(args.recipe), read_json(args.runtime)),
                separators=(",", ":"),
            )
        )
        return 0
    if args.command == "uv-requirements":
        print(_uv_requirements(args.runtime), end="")
        return 0
    if args.command == "build":
        canonical_build(
            args.recipe.resolve(),
            args.runtime.resolve(),
            args.output.resolve(),
            args.source_commit,
        )
        return 0
    if args.command == "cell":
        return execute_cell(
            _CellInputs(
                recipe_path=args.recipe.resolve(),
                runtime_path=args.runtime.resolve(),
                bundle=args.bundle.resolve(),
                tag=args.platform,
                version=args.python_version,
                output=args.output.resolve(),
                source=args.source_commit,
            )
        )
    _collect_reports(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
