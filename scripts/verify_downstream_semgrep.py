#!/usr/bin/env python3
"""Execute unprivileged downstream candidate evidence; never grant admission."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import tomllib
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from scripts.downstream_semgrep import CandidateWheel


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RECIPE = ROOT / "ci/downstream-semgrep-recipe.json"
_TOOL_NAMES = ("pip-audit", "beartype", "icontract")
CHECKS = ("install", "pip_check", "sast", "positive_control", "negative_control", "mcp_stdio", "mcp_lifecycle")


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
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


class _Cell:
    def __init__(self, output: Path, report: dict[str, object]):
        self.output = output
        self.report = report
        self.commands: list[dict[str, object]] = []
        self.report["commands"] = self.commands
        self.checks: dict[str, bool] = dict.fromkeys(CHECKS, False)
        self.report["checks"] = self.checks
        self.sequence = 0
        self.environment = dict(os.environ, SEMGREP_SEND_METRICS="off", SEMGREP_ENABLE_VERSION_CHECK="0")
        self.environment["SEMGREP_SETTINGS_FILE"] = str(output / "semgrep-settings.yml")

    def _run(
        self, label: str, command: list[str], expected: tuple[int, ...] = (0,), timeout: int = 120
    ) -> subprocess.CompletedProcess[str]:
        self.sequence += 1
        stem = self.output / f"{self.sequence:02d}-{label}"
        environment = dict(self.environment)
        if Path(command[0]).name.lower() in {"python", "python.exe"}:
            environment["PATH"] = str(Path(command[0]).parent) + os.pathsep + environment.get("PATH", "")
        try:
            proc = subprocess.run(
                command, cwd=ROOT, env=environment, text=True, capture_output=True, timeout=timeout, check=False
            )
        except subprocess.TimeoutExpired as error:

            def decoded(value: bytes | str | None) -> str:
                return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""

            proc = subprocess.CompletedProcess(
                command, 124, decoded(error.stdout), decoded(error.stderr) + "\nExternal process timeout\n"
            )
        stdout, stderr = stem.with_suffix(".stdout"), stem.with_suffix(".stderr")
        stdout.write_text(proc.stdout, encoding="utf-8")
        stderr.write_text(proc.stderr, encoding="utf-8")
        self.commands.append(
            {
                "argv": command,
                "returncode": proc.returncode,
                "stdout_sha256": _digest(stdout),
                "stderr_sha256": _digest(stderr),
            }
        )
        if proc.returncode not in expected:
            raise RuntimeError(f"{label} exited {proc.returncode}; see {stem}")
        return proc


def _architecture_matches(tag: str, machine: str) -> bool:
    suffix = "aarch64" if tag.startswith(("manylinux", "musllinux")) else "arm64"
    expected = {"aarch64", "arm64"} if tag.endswith(suffix) else {"x86_64", "amd64"}
    return machine.lower() in expected


def _musl_runtime() -> list[str]:
    loaders = list(Path("/lib").glob("ld-musl-*.so.1"))
    if len(loaders) != 1:
        raise ValueError("native musl loader unavailable or ambiguous")
    probe = subprocess.run([str(loaders[0])], capture_output=True, text=True, check=False, timeout=30)
    match = re.search(r"Version (\d+)\.(\d+)", probe.stderr + probe.stdout)
    if match is None or tuple(map(int, match.groups())) < (1, 2):
        raise ValueError("musl >= 1.2 required")
    return ["musl", match.group(0)]


def _linux_runtime(tag: str) -> list[str]:
    if tag.startswith("musllinux_"):
        return _musl_runtime()
    libc, version = platform.libc_ver()
    minimum = tuple(map(int, tag.split("_")[1:3]))
    if libc != "glibc" or tuple(map(int, version.split(".")[:2])) < minimum:
        raise ValueError("native glibc version does not satisfy wheel tag")
    return [libc, version]


def _runtime(platform_tag: str, python_version: str) -> dict[str, object]:
    system, machine = platform.system(), platform.machine()
    if f"{sys.version_info.major}.{sys.version_info.minor}" != python_version:
        raise ValueError("interpreter mismatch")
    families = {"macosx": "Darwin", "win": "Windows", "manylinux": "Linux", "musllinux": "Linux"}
    family = platform_tag.split("_")[0]
    if families.get(family) != system or not _architecture_matches(platform_tag, machine):
        raise ValueError(f"native platform mismatch: {platform_tag} vs {system}/{machine}")
    libc = _linux_runtime(platform_tag) if system == "Linux" else list(platform.libc_ver())
    return {
        "system": system,
        "machine": machine,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "sysconfig_platform": sysconfig.get_platform(),
        "python_executable_sha256": _digest(Path(sys.executable)),
        "libc": libc,
    }


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
                stream.write(chunk)
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
        if _object(package.get("source", {})).get("registry") and key not in {"semgrep", "mcp"}:
            versions.setdefault(key, set()).add(_text(package["version"]))
    if any(len(values) != 1 for values in versions.values()):
        raise ValueError("protected uv.lock contains multiple versions; explicit marker-aware constraints required")
    return {key: next(iter(values)) for key, values in versions.items()}


def _constraints(target: Path) -> None:
    versions = _locked_versions()
    target.write_text("".join(f"{package}=={versions[package]}\n" for package in sorted(versions)), encoding="utf-8")


def _python_in(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _inventory(cell: _Cell, executable: Path, label: str) -> dict[str, str]:
    program = "import importlib.metadata as m,json,re,sys; d={};\nfor p in m.distributions():\n n=re.sub(r'[-_.]+','-',p.metadata['Name']).lower()\n if n in d: raise RuntimeError('duplicate distribution '+n)\n d[n]=p.version\nsys.stdout.write(json.dumps(d,sort_keys=True))"
    payload = _json_object(cell._run(label, [str(executable), "-c", program]).stdout)
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


def _flat_lock(compiled: Path, installed: dict[str, str], wheel: Path, output: Path) -> None:
    pinned = _compiled_pins(compiled)
    result: list[str] = []
    for package, version in sorted(installed.items()):
        hashes = [_digest(wheel)] if package == "semgrep" else pinned.get(package, ("", []))[1]
        if package != "semgrep" and pinned.get(package, ("", []))[0] != version:
            raise ValueError(f"compiled lock does not bind installed identity {package}=={version}")
        if not hashes:
            raise ValueError(f"compiled lock does not bind installed hash {package}=={version}")
        result.append(f"{package}=={version} " + " ".join(f"--hash=sha256:{value}" for value in hashes))
    if set(pinned) - set(installed) - {"semgrep"}:
        raise ValueError("compiled lock contains uninstalled identities")
    output.write_text("\n".join(result) + "\n", encoding="utf-8")


def _prepare(cell: _Cell, label: str, wheel: Path, constraint: Path) -> tuple[Path, dict[str, str], Path]:
    environment = cell.output / f"{label}-env"
    executable = _python_in(environment)
    source = cell.output / f"{label}.in"
    versions = _locked_versions()
    tools = [f"{tool}=={versions[tool]}" for tool in _TOOL_NAMES]
    source.write_text(str(wheel) + "\n" + "\n".join(tools) + "\n", encoding="utf-8")
    lock = cell.output / f"{label}.locked.txt"
    cell._run(label + "-venv", ["uv", "venv", "--python", sys.executable, str(environment)])
    cell._run(
        label + "-compile",
        [
            "uv",
            "pip",
            "compile",
            str(source),
            "--python",
            str(executable),
            "--constraint",
            str(constraint),
            "--generate-hashes",
            "--output-file",
            str(lock),
        ],
        timeout=1200,
    )
    cell._run(
        label + "-install",
        ["uv", "pip", "install", "--python", str(executable), "--require-hashes", "--requirement", str(lock)],
        timeout=1200,
    )
    cell._run(label + "-pip-check", ["uv", "pip", "check", "--python", str(executable)])
    installed = _inventory(cell, executable, label + "-inventory")
    flat = cell.output / f"{label}.actual-hashed.txt"
    _flat_lock(lock, installed, wheel, flat)
    return executable, installed, flat


def _audit(cell: _Cell, executable: Path, requirements: Path, label: str) -> subprocess.CompletedProcess[str]:
    return cell._run(
        label,
        [
            str(executable),
            "-m",
            "pip_audit",
            "--strict",
            "--disable-pip",
            "--requirement",
            str(requirements),
            "--format",
            "json",
        ],
        expected=(0, 1),
        timeout=120,
    )


def _has_expected_cve(vulnerabilities: object) -> bool:
    found = False
    for value in _list(vulnerabilities):
        vulnerability = _object(value)
        identities = [_text(vulnerability["id"])] + [_text(alias) for alias in _list(vulnerability.get("aliases", []))]
        found = found or "CVE-2026-59951" in identities
    return found


def _control_dependency(value: object, installed: dict[str, str], seen: dict[str, str]) -> bool:
    dependency = _object(value)
    key = _name(_text(dependency["name"]))
    version = _text(dependency.get("version"))
    if key in seen or "skip_reason" in dependency or installed.get(key) != version:
        raise ValueError("control audit coverage mismatch or skipped package")
    seen[key] = version
    has_cve = _has_expected_cve(dependency.get("vulns"))
    return key == "mcp" and has_cve


def _assert_vulnerable_control(proc: subprocess.CompletedProcess[str], installed: dict[str, str]) -> None:
    if proc.returncode != 1:
        raise ValueError("control audit did not fail")
    payload = _json_object(proc.stdout)
    seen: dict[str, str] = {}
    found = False
    for dependency in _list(payload.get("dependencies")):
        expected = _control_dependency(dependency, installed, seen)
        found = found or expected
    if seen != installed or not found:
        raise ValueError("control audit lacks full graph or expected MCP CVE-2026-59951")


def _sast_view(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    payload = _json_object(proc.stdout)
    if payload.get("errors"):
        raise ValueError("SAST reported errors")
    results = _list(payload.get("results"))
    paths = _object(payload.get("paths"))
    _list(paths.get("scanned"))
    return {"results": results, "errors": payload.get("errors", []), "paths": paths}


def _scanners(cell: _Cell, executables: dict[str, Path]) -> None:
    views: dict[str, dict[str, object]] = {}
    rule = cell.output / "control-rule.yml"
    rule.write_text(
        "rules:\n- id: downstream-positive\n  pattern: eval(...)\n  message: positive control\n  severity: ERROR\n  languages: [python]\n",
        encoding="utf-8",
    )
    positive, negative = cell.output / "positive.py", cell.output / "negative.py"
    positive.write_text("eval(user_input)\n", encoding="utf-8")
    negative.write_text("print('safe')\n", encoding="utf-8")
    for label, executable in executables.items():
        base = [
            str(executable.parent / ("semgrep.exe" if os.name == "nt" else "semgrep")),
            "scan",
            "--metrics=off",
            "--disable-version-check",
            "--json",
        ]
        proc = cell._run(label + "-sast", [*base, "--config", "tools/semgrep/sast.yml"], timeout=1200)
        views[label] = _sast_view(proc)
        results = cell.output / f"{label}.sast.json"
        results.write_text(proc.stdout, encoding="utf-8")
        cell._run(
            label + "-sast-gate",
            [
                str(executable),
                "scripts/semgrep_sast_gate.py",
                "--results",
                str(results),
                "--baseline",
                "tools/semgrep/sast-baseline.json",
            ],
        )
        pos = cell._run(label + "-positive", [*base, "--error", "--config", str(rule), str(positive)], expected=(1,))
        neg = cell._run(label + "-negative", [*base, "--error", "--config", str(rule), str(negative)])
        if len(_list(_sast_view(pos)["results"])) != 1 or _sast_view(neg)["results"]:
            raise ValueError("positive/negative scanner findings mismatch")
    if views["candidate"] != views["control"]:
        raise ValueError("candidate/control SAST findings/errors/scanned/skipped paths differ")
    cell.report["sast_paths"] = len(_list(_object(views["candidate"]["paths"])["scanned"]))
    cell.checks.update(sast=True, positive_control=True, negative_control=True)


_SOURCE_FILES = (
    "scripts/downstream_semgrep.py",
    "scripts/verify_downstream_semgrep.py",
    "ci/downstream-semgrep-recipe.json",
    "tools/downstream_semgrep/test_mcp_regressions.py",
    ".github/workflows/downstream-semgrep.yml",
    "uv.lock",
    "tools/semgrep/sast.yml",
    "tools/semgrep/sast-baseline.json",
    "scripts/semgrep_sast_gate.py",
)


@dataclass(frozen=True)
class _Environment:
    python: Path
    inventory: dict[str, str]
    flat: Path


def _source_binding(cell: _Cell) -> None:
    commit = cell._run("source-commit", ["git", "rev-parse", "HEAD"]).stdout.strip()
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("source commit is not full SHA")
    tracked = cell._run("source-status-tracked", ["git", "status", "--porcelain", "--untracked-files=no"]).stdout
    untracked = cell._run(
        "source-status-untracked",
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            *_SOURCE_FILES,
            "tests/unit/scripts/test_downstream_semgrep.py",
        ],
    ).stdout
    diff = cell._run("source-diff", ["git", "diff", "--binary", "HEAD"]).stdout
    cell.report.update(
        source_commit=commit,
        source_dirty=bool(tracked.strip() or untracked.strip()),
        source_files={path: _digest(ROOT / path) for path in _SOURCE_FILES},
        source_diff_sha256=hashlib.sha256(diff.encode("utf-8")).hexdigest(),
    )


def _cell_runtime(cell: _Cell, platform_tag: str, python_version: str) -> None:
    cell.report["runtime"] = _runtime(platform_tag, python_version)
    cell.report["native"] = True
    cell.report["uv_version"] = cell._run("uv-version", ["uv", "--version"]).stdout.strip()
    uv_executable = shutil.which("uv")
    if not uv_executable:
        raise ValueError("uv executable unavailable")
    cell.report["uv_executable_sha256"] = _digest(Path(uv_executable))
    _source_binding(cell)


def _cell_build(cell: _Cell, recipe_path: Path, platform_tag: str, python_version: str) -> tuple[CandidateWheel, Path]:
    from scripts.downstream_semgrep import build_candidate

    recipe = _json_object(recipe_path.read_text(encoding="utf-8"))
    records = [_object(value) for value in _list(recipe["wheels"]) if _object(value)["platform_tag"] == platform_tag]
    if len(records) != 1 or python_version not in _list(recipe["python_versions"]):
        raise ValueError("cell not in recipe")
    upstream = _download(records[0], cell.output)
    first = build_candidate(recipe_path, upstream, cell.output / "build-one")
    second = build_candidate(recipe_path, upstream, cell.output / "build-two")
    if first.sha256 != second.sha256 or first.path.read_bytes() != second.path.read_bytes():
        raise ValueError("independent candidate builds differ")
    cell.report.update(
        upstream_sha256=_digest(upstream), candidate_sha256=first.sha256, recipe_sha256=first.recipe_sha256
    )
    return first, upstream


def _compare_graphs(candidate: _Environment, control: _Environment) -> None:
    expected = ((candidate.inventory, "1.30.0", "1.179.0+specfact.1"), (control.inventory, "1.29.0", "1.179.0"))
    for graph, mcp, semgrep in expected:
        if graph.get("mcp") != mcp or graph.get("semgrep") != semgrep:
            raise ValueError("candidate/control reviewed identities mismatch")

    def remaining(graph: dict[str, str]) -> dict[str, str]:
        return {key: value for key, value in graph.items() if key not in {"semgrep", "mcp"}}

    if remaining(candidate.inventory) != remaining(control.inventory):
        raise ValueError("paired actual graphs differ beyond Semgrep/MCP")


def _cell_install(cell: _Cell, candidate: CandidateWheel, upstream: Path) -> tuple[_Environment, _Environment]:
    constraint = cell.output / "protected-constraints.txt"
    _constraints(constraint)
    actual = _Environment(*_prepare(cell, "candidate", candidate.path, constraint))
    control = _Environment(*_prepare(cell, "control", upstream, constraint))
    _compare_graphs(actual, control)
    cell.report.update(actual_inventory=actual.inventory, control_inventory=control.inventory)
    cell.checks.update(install=True, pip_check=True)
    bound = candidate.candidate_audit_input(actual.flat, cell.output / "candidate.audit.txt")
    bound.assert_complete_result(_audit(cell, actual.python, bound.requirements, "candidate-audit"))
    _assert_vulnerable_control(_audit(cell, control.python, control.flat, "control-audit"), control.inventory)
    cell.report.update(candidate_audit_passed=True, control_expected_cve_confirmed=True)
    return actual, control


def _mcp_regressions(cell: _Cell, candidate: _Environment, control: _Environment) -> None:
    regression = ROOT / "tools/downstream_semgrep/test_mcp_regressions.py"
    cell._run("candidate-mcp-regressions", [str(candidate.python), str(regression)], timeout=240)
    cell.checks.update(mcp_stdio=True, mcp_lifecycle=True)
    proc = cell._run(
        "control-mcp-regression", [str(control.python), str(regression), "TestMcpLifecycle"], expected=(1,), timeout=60
    )
    required = ("FAILED (failures=8)", "DELETE retained a registered session")
    if not all(message in proc.stderr for message in required) or "ERROR:" in proc.stderr:
        raise ValueError("control failed for unexpected MCP regression reason")
    cell.report["control_expected_regression_confirmed"] = True


def _execute_cell(recipe: Path, platform_tag: str, python_version: str, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=False)
    report: dict[str, object] = {
        "platform": platform_tag,
        "python_version": python_version,
        "status": "failed",
        "native": False,
        "candidate_only": True,
        "production_admission": "not_requested",
    }
    cell = _Cell(output, report)
    try:
        _cell_runtime(cell, platform_tag, python_version)
        candidate, upstream = _cell_build(cell, recipe, platform_tag, python_version)
        actual, control = _cell_install(cell, candidate, upstream)
        _scanners(cell, {"candidate": actual.python, "control": control.python})
        _mcp_regressions(cell, actual, control)
        cell.report["status"] = "passed"
        return 0
    except Exception as error:
        cell.report["failure"] = f"{type(error).__name__}: {error}"
        return 1
    finally:
        (output / "report.json").write_text(json.dumps(cell.report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _matrix(recipe_path: Path) -> dict[str, object]:
    from scripts.downstream_semgrep import required_matrix

    recipe = _json_object(recipe_path.read_text(encoding="utf-8"))
    wheels = {_text(_object(value)["platform_tag"]): _object(value) for value in _list(recipe["wheels"])}
    rows: list[dict[str, str]] = []
    for cell in required_matrix(recipe_path):
        record = wheels[cell["platform"]]
        image = _object(record.get("containers", {})).get(cell["python_version"], "")
        if not isinstance(image, str):
            raise ValueError("container image must be text")
        rows.append(dict(cell, runner=_text(record["runner"]), container_image=image))
    return {"include": rows}


def _uv_wheel(record: dict[str, object], version: str) -> tuple[str, str]:
    filename, sha = _text(record["filename"]), _text(record["sha256"])
    _official_wheel_url(_text(record["url"]), filename)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", type=Path, default=RECIPE)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("matrix")
    sub.add_parser("uv-requirements")
    run = sub.add_parser("cell")
    run.add_argument("--platform", required=True)
    run.add_argument("--python-version", required=True)
    run.add_argument("--output", required=True, type=Path)
    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--reports", required=True, type=Path)
    args = parser.parse_args()
    recipe = Path(args.recipe).resolve()
    if args.command == "matrix":
        sys.stdout.write(json.dumps(_matrix(recipe), separators=(",", ":")) + "\n")
        return 0
    if args.command == "uv-requirements":
        sys.stdout.write(_uv_requirements(recipe))
        return 0
    if args.command == "cell":
        return _execute_cell(recipe, str(args.platform), str(args.python_version), Path(args.output).resolve())
    from scripts.downstream_semgrep import aggregate_candidate_reports

    paths = sorted(Path(args.reports).rglob("report.json"))
    reports = [_json_object(path.read_text(encoding="utf-8")) for path in paths]
    sys.stdout.write(json.dumps(aggregate_candidate_reports(recipe, reports), sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
