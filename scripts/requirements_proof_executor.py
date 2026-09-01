"""Execute a verified Requirements proof plan without shell interpretation."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from stat import S_ISREG
from typing import Protocol, cast, runtime_checkable

from beartype import beartype
from icontract import ensure


MAX_SELECTORS = 100
MAX_JUNIT_BYTES = 10 * 1024 * 1024
SYSTEMD_SERVICE_TIMEOUT_SECONDS = 630
# systemd PrivateTmp gives the isolated service its own mount at this path.
PRIVATE_SERVICE_TMP = "/tmp"  # nosec B108
SELECTOR_PATTERN = re.compile(r"(?!-)[A-Za-z0-9_./-]+\.py::[^\r\n\x00]+")
SYSTEMD_UNIT_PATTERN = re.compile(r"specfact-proof-[a-f0-9]{16,64}")
FORBIDDEN_SELECTOR_CHARACTERS = frozenset('\r\n\x00$&;|`<>*?(){}!\\"')
PROOF_ENVIRONMENT_KEYS = frozenset(
    {
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "SPECFACT_MODULES_REPO",
        "SPECFACT_MODULES_ROOTS",
        "TMPDIR",
        "VIRTUAL_ENV",
    }
)
PROOF_PYTEST_BOOTSTRAP = (
    "import sys\n"
    "import pytest\n"
    "repo_root = sys.argv.pop(1)\n"
    "sys.path.append(repo_root)\n"
    "raise SystemExit(pytest.main(sys.argv[1:]))\n"
)
PROOF_IDENTITY_PROPERTIES = (
    "specfact.runner",
    "specfact.python",
    "specfact.pytest",
)


@runtime_checkable
class CommandRunner(Protocol):
    """Typed subprocess seam for unit testing the no-shell invocation."""

    def __call__(self, request: ProofCommand) -> int:
        raise NotImplementedError


@dataclass(frozen=True)
class ProofCommand:
    """Core-owned process inputs for one bounded pytest proof invocation."""

    arguments: list[str]
    cwd: Path
    env: dict[str, str]
    shell: bool
    timeout: int


def _validate_plan_state(plan: Mapping[str, object]) -> None:
    """Accept only the released plan report state that authorizes execution."""
    if (
        plan.get("schema_version") != "2"
        or plan.get("gate_decision") != "pass"
        or plan.get("observed_maturity") != "test-authored"
    ):
        raise ValueError("invalid proof plan state")


def _plan_cases(plan: Mapping[str, object]) -> list[Mapping[str, object]]:
    nested_plan = plan.get("plan")
    if not isinstance(nested_plan, Mapping):
        raise ValueError("proof plan must contain a plan object")
    nested_plan = cast(Mapping[str, object], nested_plan)
    cases = nested_plan.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("proof plan must contain nonempty cases")
    if any(not isinstance(case, Mapping) for case in cases):
        raise ValueError("proof plan contains an invalid case")
    return [cast(Mapping[str, object], case) for case in cases if isinstance(case, Mapping)]


def _contains_control_character(value: str) -> bool:
    """Reject terminal and other ASCII controls before invoking pytest."""
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _is_unsafe_node_id(node_id: str) -> bool:
    """Keep paths relative and reject options, controls, and shell metacharacters."""
    test_path, _, _ = node_id.partition("::")
    relative_path = PurePosixPath(test_path)
    return (
        relative_path.is_absolute()
        or ".." in relative_path.parts
        or node_id.startswith("-")
        or _contains_control_character(node_id)
        or any(character in node_id for character in FORBIDDEN_SELECTOR_CHARACTERS)
    )


def _validate_selector(selector: object, repo_root: Path) -> str:
    if not isinstance(selector, Mapping):
        raise ValueError("proof plan contains an invalid pytest selector")
    selector = cast(Mapping[str, object], selector)
    if selector.get("runner") != "pytest":
        raise ValueError("proof plan contains an unsupported runner")
    node_id = selector.get("node_id")
    if not isinstance(node_id, str) or not SELECTOR_PATTERN.fullmatch(node_id):
        raise ValueError("proof plan contains an invalid pytest selector")
    test_path, _, _ = node_id.partition("::")
    relative_path = PurePosixPath(test_path)
    if _is_unsafe_node_id(node_id):
        raise ValueError("proof plan contains an invalid pytest selector")
    resolved_path = (repo_root / relative_path).resolve()
    if not resolved_path.is_relative_to(repo_root.resolve()) or not resolved_path.is_file():
        raise ValueError("proof plan selector must name an existing repository test file")
    return node_id


@beartype
@ensure(lambda result: result and len(result) <= MAX_SELECTORS)
def selectors_from_plan(plan: dict[str, object], repo_root: Path) -> list[str]:
    """Return unique, repository-contained exact pytest selectors from a module plan."""
    _validate_plan_state(plan)
    selectors: list[str] = []
    for case in _plan_cases(plan):
        if case.get("method") != "test":
            continue
        selector = case.get("selector")
        if selector is None:
            raise ValueError("proof plan test case is missing a selector")
        selectors.append(_validate_selector(selector, repo_root))
    if not selectors:
        raise ValueError("proof plan contains no executable test selectors")
    if len(selectors) > MAX_SELECTORS:
        raise ValueError(f"proof plan exceeds the {MAX_SELECTORS} selector limit")
    if len(set(selectors)) != len(selectors):
        raise ValueError("proof plan contains a duplicate pytest selector")
    return selectors


def _planned_selector(raw_selector: str, planned_selectors: Sequence[str]) -> str:
    """Map one concrete parameter case to exactly one planned pytest selector."""
    matches = [
        selector
        for selector in planned_selectors
        if raw_selector == selector or raw_selector.startswith(f"{selector}[")
    ]
    if len(matches) != 1:
        raise ValueError("proof JUnit selector does not match exactly one planned selector")
    return matches[0]


def _case_properties(test_case: ET.Element) -> dict[str, str]:
    """Return the unique proof properties emitted for one collected pytest case."""
    properties: dict[str, str] = {}
    required = {"specfact.selector", *PROOF_IDENTITY_PROPERTIES}
    for property_ in test_case.findall("./properties/property"):
        name = property_.get("name")
        value = property_.get("value")
        if name not in required:
            continue
        if not isinstance(value, str) or name in properties:
            raise ValueError("proof JUnit contains invalid or duplicate properties")
        properties[name] = value
    if not required.issubset(properties):
        raise ValueError("proof JUnit is missing selector or toolchain identity")
    return properties


def _case_outcome(test_case: ET.Element) -> str:
    """Return the single terminal outcome represented by one JUnit case."""
    terminal = [name for name in ("failure", "error", "skipped") if test_case.find(name) is not None]
    if len(terminal) > 1:
        raise ValueError("proof JUnit case has multiple terminal outcomes")
    return terminal[0] if terminal else "passed"


def _aggregate_outcome(outcomes: Sequence[str]) -> str:
    """Collapse parameter outcomes without allowing a passing case to hide a failure."""
    for outcome in ("error", "failure", "skipped"):
        if outcome in outcomes:
            return outcome
    return "passed"


def _observed_results(
    root: ET.Element,
    planned_selectors: Sequence[str],
) -> tuple[dict[str, list[str]], dict[str, dict[str, str]]]:
    """Collect exact planned outcomes and stable toolchain identities."""
    outcomes: dict[str, list[str]] = {selector: [] for selector in planned_selectors}
    identities: dict[str, dict[str, str]] = {}
    concrete_selectors: set[str] = set()
    for test_case in root.iter("testcase"):
        properties = _case_properties(test_case)
        raw_selector = properties["specfact.selector"]
        if raw_selector in concrete_selectors:
            raise ValueError("proof JUnit contains a duplicate concrete selector")
        concrete_selectors.add(raw_selector)
        planned_selector = _planned_selector(raw_selector, planned_selectors)
        identity = {name: properties[name] for name in PROOF_IDENTITY_PROPERTIES}
        if planned_selector in identities and identities[planned_selector] != identity:
            raise ValueError("proof JUnit parameter cases use inconsistent toolchain identities")
        identities[planned_selector] = identity
        outcomes[planned_selector].append(_case_outcome(test_case))
    if any(not values for values in outcomes.values()):
        raise ValueError("proof JUnit did not collect every planned selector")
    return outcomes, identities


def _render_canonical_junit(
    planned_selectors: Sequence[str],
    aggregate: Mapping[str, str],
    identities: Mapping[str, Mapping[str, str]],
) -> bytes:
    """Render deterministic aggregate results for the reconciliation module."""
    canonical = ET.Element("testsuite")
    canonical.set("tests", str(len(planned_selectors)))
    canonical.set("failures", str(sum(outcome == "failure" for outcome in aggregate.values())))
    canonical.set("errors", str(sum(outcome == "error" for outcome in aggregate.values())))
    canonical.set("skipped", str(sum(outcome == "skipped" for outcome in aggregate.values())))
    for selector in planned_selectors:
        test_case = ET.SubElement(canonical, "testcase", name=selector)
        properties = ET.SubElement(test_case, "properties")
        ET.SubElement(properties, "property", name="specfact.selector", value=selector)
        for name in PROOF_IDENTITY_PROPERTIES:
            ET.SubElement(properties, "property", name=name, value=identities[selector][name])
        outcome = aggregate[selector]
        if outcome != "passed":
            ET.SubElement(test_case, outcome)
    return ET.tostring(canonical, encoding="utf-8")


def _canonical_junit(payload: bytes, planned_selectors: Sequence[str]) -> bytes:
    """Return one fail-dominant JUnit case for every exact planned selector."""
    if len(payload) > MAX_JUNIT_BYTES:
        raise ValueError("proof JUnit is too large or contains unsafe XML declarations")
    try:
        xml_text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("proof JUnit must use UTF-8 encoding") from error
    if "<!DOCTYPE" in xml_text.upper() or "<!ENTITY" in xml_text.upper():
        raise ValueError("proof JUnit is too large or contains unsafe XML declarations")
    try:
        # The bounded UTF-8 input has already rejected every DTD/entity declaration.
        root = ET.fromstring(xml_text)  # nosec B314
    except ET.ParseError as error:
        raise ValueError("proof JUnit is malformed") from error
    outcomes, identities = _observed_results(root, planned_selectors)
    aggregate = {selector: _aggregate_outcome(outcomes[selector]) for selector in planned_selectors}
    return _render_canonical_junit(planned_selectors, aggregate, identities)


def _read_junit(junit_path: Path) -> bytes:
    """Read one bounded regular JUnit file without accepting a path substitution."""
    try:
        path_status = os.lstat(junit_path)
        if not S_ISREG(path_status.st_mode):
            raise ValueError("proof JUnit output is not a regular file")
        descriptor = os.open(junit_path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as junit_file:
            file_status = os.fstat(junit_file.fileno())
            if not S_ISREG(file_status.st_mode) or not os.path.samestat(path_status, file_status):
                raise ValueError("proof JUnit output is not a regular file")
            payload = junit_file.read(MAX_JUNIT_BYTES + 1)
    except OSError as error:
        raise ValueError("proof JUnit output is not a regular file") from error
    return payload


def _publish_junit(raw_path: Path, output_path: Path, planned_selectors: Sequence[str]) -> None:
    """Publish canonical aggregates only when the destination remains absent."""
    temporary_path = output_path.with_name(f".{output_path.name}.{secrets.token_hex(12)}.tmp")
    descriptor = -1
    published = False
    try:
        canonical = _canonical_junit(_read_junit(raw_path), planned_selectors)
        descriptor = os.open(temporary_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "r+b") as temporary_file:
            descriptor = -1
            temporary_file.write(canonical)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_status = os.fstat(temporary_file.fileno())
            if not S_ISREG(temporary_status.st_mode):
                raise ValueError("proof JUnit temporary output is not a regular file")
            os.link(temporary_path, output_path)
            output_status = os.lstat(output_path)
            temporary_file.seek(0)
            if not os.path.samestat(temporary_status, output_status) or temporary_file.read() != canonical:
                raise ValueError("proof JUnit output changed during publication")
            published = True
    except OSError as error:
        raise ValueError("proof JUnit output could not be published safely") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if not published:
            with suppress(FileNotFoundError):
                output_path.unlink()
        with suppress(FileNotFoundError):
            temporary_path.unlink()


def _systemd_property(name: str, value: str) -> list[str]:
    """Return one systemd property without shell parsing."""
    return ["--property", f"{name}={value}"]


def _systemd_path(path: Path) -> str:
    """Return one absolute path accepted by the transient-unit property grammar."""
    resolved = str(path.resolve())
    if not resolved.startswith("/") or any(character in resolved for character in "\x00\r\n:\t "):
        raise ValueError("proof isolation paths must be absolute and contain no systemd separators")
    return resolved


def _systemd_isolation_properties(repository: str, handoff: str) -> tuple[tuple[str, str], ...]:
    """Return the fixed fail-closed transient-service security policy."""
    return (
        ("DynamicUser", "yes"),
        ("KillMode", "control-group"),
        ("SendSIGKILL", "yes"),
        ("TimeoutStopSec", "5s"),
        ("RuntimeMaxSec", "600s"),
        ("TasksMax", "256"),
        ("MemoryMax", "4G"),
        ("NoNewPrivileges", "yes"),
        ("RestrictSUIDSGID", "yes"),
        ("CapabilityBoundingSet", ""),
        ("AmbientCapabilities", ""),
        ("ProtectSystem", "strict"),
        ("ProtectHome", "tmpfs"),
        ("PrivateTmp", "yes"),
        ("PrivateDevices", "yes"),
        ("PrivateNetwork", "yes"),
        ("PrivateMounts", "yes"),
        ("ProtectControlGroups", "yes"),
        ("ProtectKernelTunables", "yes"),
        ("ProtectKernelModules", "yes"),
        ("ProtectKernelLogs", "yes"),
        ("ProtectClock", "yes"),
        ("ProtectHostname", "yes"),
        ("ProtectProc", "invisible"),
        ("ProcSubset", "pid"),
        ("StandardOutput", "null"),
        ("StandardError", "null"),
        ("RestrictNamespaces", "yes"),
        ("RestrictRealtime", "yes"),
        ("LockPersonality", "yes"),
        ("UMask", "0022"),
        ("BindReadOnlyPaths", f"{repository}:{repository}:rbind"),
        ("BindPaths", f"{handoff}:{handoff}:norbind"),
        ("ReadWritePaths", handoff),
        ("InaccessiblePaths", f"{repository}/.git"),
        ("InaccessiblePaths", f"-{repository}/specfact-cli-modules/.git"),
        ("InaccessiblePaths", "-/var/run/docker.sock"),
        ("InaccessiblePaths", "-/run/docker.sock"),
    )


def _systemd_service_request(
    request: ProofCommand,
    repo_root: Path,
    handoff_root: Path,
    unit_name: str,
) -> ProofCommand:
    """Wrap exact pytest arguments in a fail-closed transient system service."""
    if not SYSTEMD_UNIT_PATTERN.fullmatch(unit_name):
        raise ValueError("proof isolation unit name is invalid")
    repository = _systemd_path(repo_root)
    handoff = _systemd_path(handoff_root)
    try:
        handoff_root.resolve().relative_to(repo_root.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("proof isolation handoff must be outside the repository")

    arguments = [
        "/usr/bin/sudo",
        "-n",
        "/usr/bin/systemd-run",
        "--quiet",
        "--wait",
        "--collect",
        "--service-type=exec",
        f"--unit={unit_name}",
        f"--working-directory={repository}",
    ]
    for name, value in _systemd_isolation_properties(repository, handoff):
        arguments.extend(_systemd_property(name, value))

    child_environment = dict(request.env)
    child_environment.update(
        {
            "HOME": PRIVATE_SERVICE_TMP,
            "RUNNER_TEMP": PRIVATE_SERVICE_TMP,
            "TMPDIR": PRIVATE_SERVICE_TMP,
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    for key, value in child_environment.items():
        if not key or "=" in key or _contains_control_character(key + value):
            raise ValueError("proof isolation environment contains an invalid value")
    pytest_arguments = request.arguments.copy()
    option_end = pytest_arguments.index("--")
    pytest_arguments[option_end:option_end] = ["-p", "no:cacheprovider"]
    fixed_environment = [
        f"HOME={PRIVATE_SERVICE_TMP}",
        f"RUNNER_TEMP={PRIVATE_SERVICE_TMP}",
        f"TMPDIR={PRIVATE_SERVICE_TMP}",
        *[
            f"{key}={value}"
            for key, value in sorted(child_environment.items())
            if key not in {"HOME", "RUNNER_TEMP", "TMPDIR"}
        ],
    ]
    arguments.extend(["/usr/bin/env", "-i", *fixed_environment, *pytest_arguments])
    return ProofCommand(arguments, repo_root, {}, shell=False, timeout=SYSTEMD_SERVICE_TIMEOUT_SECONDS)


def _terminate_service(unit_name: str) -> None:
    """Best-effort exact-unit cleanup after an outer client timeout."""
    for action in (
        ["kill", "--kill-whom=all", "--signal=SIGKILL", unit_name],
        ["stop", unit_name],
    ):
        subprocess.run(
            ["/usr/bin/sudo", "-n", "/usr/bin/systemctl", *action],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={},
            timeout=15,
        )


def _assert_service_inactive(unit_name: str) -> None:
    """Require systemd to report no live main process after the waited service."""
    result = subprocess.run(
        [
            "/usr/bin/systemctl",
            "show",
            "--property=LoadState",
            "--property=ActiveState",
            "--property=MainPID",
            unit_name,
        ],
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env={},
        timeout=15,
    )
    if result.returncode != 0:
        raise ValueError("proof isolation service state could not be verified")
    state: dict[str, str] = {}
    for line in result.stdout.decode("utf-8", errors="strict").splitlines():
        name, separator, value = line.partition("=")
        if separator:
            state[name] = value
    if state.get("LoadState") == "not-found":
        return
    if state.get("ActiveState") not in {"inactive", "failed"} or state.get("MainPID") != "0":
        raise ValueError("proof isolation service remained active after execution")


def _run_systemd_pytest_proof(
    request: ProofCommand,
    repo_root: Path,
    output_path: Path,
    selectors: Sequence[str],
) -> int:
    """Run pytest in a transient service and canonicalize only after teardown."""
    runner_temp = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())).resolve()
    runner_temp.mkdir(parents=True, exist_ok=True)
    handoff_root = Path(tempfile.mkdtemp(prefix="specfact-proof-handoff-", dir=runner_temp))
    # The unpredictable directory exposes creation, not listing or reads, to the
    # unknown DynamicUser and is deleted immediately after cgroup teardown.
    os.chmod(handoff_root, 0o733)  # nosec B103
    unit_name = f"specfact-proof-{secrets.token_hex(12)}"
    raw_junit_path = handoff_root / "requirements-proof.raw.xml"
    isolated_arguments = request.arguments.copy()
    isolated_arguments[6] = str(raw_junit_path)
    isolated_request = ProofCommand(
        isolated_arguments,
        request.cwd,
        request.env,
        request.shell,
        request.timeout,
    )
    try:
        service_request = _systemd_service_request(
            isolated_request,
            repo_root,
            handoff_root,
            unit_name,
        )
        try:
            process_result = subprocess.run(
                service_request.arguments,
                check=False,
                cwd=service_request.cwd,
                env=service_request.env,
                shell=False,
                close_fds=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=service_request.timeout,
            )
        except subprocess.TimeoutExpired:
            _terminate_service(unit_name)
            raise
        _assert_service_inactive(unit_name)
        _publish_junit(raw_junit_path, output_path, selectors)
        return process_result.returncode
    finally:
        shutil.rmtree(handoff_root, ignore_errors=True)


def _run_pytest_proof(
    request: ProofCommand,
    raw_junit_path: Path,
    output_path: Path,
    selectors: Sequence[str],
) -> int:
    """Run pytest to an isolated raw path, then publish exact planned aggregates."""
    try:
        exit_code = subprocess.run(
            request.arguments,
            check=False,
            cwd=request.cwd,
            env=request.env,
            shell=False,
            close_fds=True,
            timeout=request.timeout,
        ).returncode
        _publish_junit(raw_junit_path, output_path, selectors)
    finally:
        with suppress(FileNotFoundError):
            raw_junit_path.unlink()
    return exit_code


@beartype
@ensure(lambda result: isinstance(result, int))
def execute_plan(
    plan: dict[str, object],
    repo_root: Path,
    junit_path: Path,
    *,
    command_runner: CommandRunner | None = None,
    isolation: str = "direct",
) -> int:
    """Run exact selectors with a deterministic JUnit destination and no shell."""
    selectors = selectors_from_plan(plan, repo_root)
    selected_paths = {(repo_root / selector.partition("::")[0]).resolve() for selector in selectors}
    if junit_path.is_symlink():
        raise ValueError("JUnit destination must not be a symbolic link")
    resolved_junit_path = junit_path.resolve()
    if resolved_junit_path in selected_paths:
        raise ValueError("JUnit destination overlaps a selected repository input")
    try:
        resolved_junit_path.relative_to(repo_root.resolve())
    except ValueError:
        pass
    else:
        if resolved_junit_path.exists():
            raise ValueError("JUnit destination overlaps an existing repository input")
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    junit_path.unlink(missing_ok=True)
    junit_path = resolved_junit_path
    arguments = [
        sys.executable,
        "-P",
        "-c",
        PROOF_PYTEST_BOOTSTRAP,
        str(repo_root.resolve()),
        "--junitxml",
        str(junit_path),
        "-p",
        "scripts.requirements_proof_pytest_plugin",
        "--",
        *selectors,
    ]
    environment = {key: value for key, value in os.environ.items() if key in PROOF_ENVIRONMENT_KEYS}
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    request = ProofCommand(arguments, repo_root, environment, shell=False, timeout=600)
    if command_runner is not None:
        return command_runner(request)
    if isolation == "systemd-service":
        return _run_systemd_pytest_proof(request, repo_root, junit_path, selectors)
    if isolation != "direct":
        raise ValueError("unsupported proof isolation backend")
    raw_junit_path = junit_path.with_name(f".{junit_path.name}.{secrets.token_hex(12)}.raw")
    raw_arguments = request.arguments.copy()
    raw_arguments[6] = str(raw_junit_path)
    raw_request = ProofCommand(raw_arguments, request.cwd, request.env, request.shell, request.timeout)
    return _run_pytest_proof(raw_request, raw_junit_path, junit_path, selectors)


def _read_plan(plan_path: Path) -> dict[str, object]:
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read proof plan: {plan_path}") from error
    if not isinstance(payload, dict):
        raise ValueError("proof plan must contain a JSON object")
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True, help="Module-produced lifecycle plan report.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository containing selected tests.")
    parser.add_argument("--junit", type=Path, required=True, help="Fresh JUnit XML destination.")
    parser.add_argument(
        "--isolation",
        choices=("direct", "systemd-service"),
        default="direct",
        help="Execution backend; blocking Linux CI requires systemd-service.",
    )
    return parser


@beartype
@ensure(lambda result: isinstance(result, int))
def main(argv: Sequence[str] | None = None) -> int:
    """Validate the structured plan and return the selected pytest exit code."""
    arguments = _build_parser().parse_args(argv)
    try:
        if arguments.junit.resolve() == arguments.plan.resolve():
            raise ValueError("JUnit destination overlaps the proof plan")
        return execute_plan(
            _read_plan(arguments.plan),
            arguments.repo_root.resolve(),
            arguments.junit.resolve(),
            isolation=arguments.isolation,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Requirements proof execution rejected: {error}") from error


if __name__ == "__main__":
    raise SystemExit(main())
