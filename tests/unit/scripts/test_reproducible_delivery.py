"""Contract tests for frozen-delivery support scripts."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml
from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_license_scope_policy() -> Any:
    """Load the pure scope predicate from its exact repository path."""
    policy_path = REPO_ROOT / "scripts" / "license_scope_policy.py"
    spec = importlib.util.spec_from_file_location("license_scope_policy_test", policy_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(relative_path: str) -> dict[str, Any]:
    """Load one repository JSON policy document."""
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def _license_allowlist_entry(package: str) -> dict[str, str]:
    """Load one package's unique reviewed entry from repository policy."""
    policy = yaml.safe_load((REPO_ROOT / "scripts" / "license_allowlist.yaml").read_text(encoding="utf-8"))
    entries = [entry for entry in policy["exceptions"] if entry["package"].casefold() == package.casefold()]
    assert len(entries) == 1
    return entries[0]


def _assert_license_scope_predicate_is_used_by_the_gate() -> None:
    checker = (REPO_ROOT / "scripts" / "check_license_compliance.py").read_text(encoding="utf-8")
    matcher = checker[
        checker.index("def _matching_allowlist_entries(") : checker.index("def _emit_allowlist_exception(")
    ]
    assert "environment_allowlist_entry_matches(" in matcher


def _locked_package_versions() -> dict[str, str]:
    """Return the exact package versions selected by the frozen lock."""
    lock = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    return {package["name"]: package["version"] for package in lock["package"]}


def _runtime_dependency_names(project: dict[str, Any]) -> set[str]:
    """Return normalized base runtime dependency names from pyproject.toml."""
    return {Requirement(dependency).name.casefold() for dependency in project["project"]["dependencies"]}


def _assert_semgrep_declarations(project: dict[str, Any]) -> None:
    """Assert every static-analysis tool group selects the reviewed Semgrep floor."""
    optional_dependencies = project["project"]["optional-dependencies"]
    hatch_dependencies = project["tool"]["hatch"]["envs"]["default"]["dependencies"]
    assert "semgrep>=1.175.0" in optional_dependencies["dev"]
    assert "semgrep>=1.175.0" in optional_dependencies["scanning"]
    assert "semgrep>=1.175.0" in hatch_dependencies


def _assert_fixed_semgrep_snapshot(locked_packages: dict[str, str], locked_export: str) -> None:
    """Assert the frozen lock and export select the compatible fixed pair."""
    assert locked_packages["semgrep"] == "1.175.0"
    assert locked_packages["mcp"] == "1.29.0"
    assert "semgrep==1.175.0" in locked_export
    assert "mcp==1.29.0" in locked_export


def _assert_semgrep_security_policy(security_floors: dict[str, Any], exception_register: dict[str, Any]) -> None:
    """Assert vulnerable Semgrep/MCP versions cannot be waived or installed."""
    assert security_floors["minimum_versions"]["semgrep"] == "1.175.0"
    assert security_floors["minimum_versions"]["mcp"] == "1.28.1"
    assert all(item["package"].casefold() != "mcp" for item in exception_register["exceptions"])


def _write_invalid_binding_fixture(module: Any, tmp_path: Path, binding_state: str) -> tuple[Path, Path]:
    """Create an isolated input/lock pair with the requested invalid binding."""
    requirements = tmp_path / "repository" / "requirements" / "code-review"
    requirements.mkdir(parents=True)
    requirements_input = requirements / "requirements.in"
    requirements_input.write_text("pylint>=4\n", encoding="utf-8")
    locked_export = requirements / "locked.txt"
    lock_body = "\n".join(
        line
        for line in module.CODE_REVIEW_LOCKED_EXPORT.read_text(encoding="utf-8").splitlines()
        if not line.startswith("# input-sha256:")
    )
    original_digest = hashlib.sha256(b"pylint==4.0.7\n").hexdigest()
    binding_lines = {
        "missing": "",
        "malformed": "# input-sha256: not-a-digest\n",
        "duplicate": f"# input-sha256: {original_digest}\n# input-sha256: {original_digest}\n",
        "mismatch": f"# input-sha256: {original_digest}\n",
    }
    locked_export.write_text(binding_lines[binding_state] + lock_body, encoding="utf-8")
    return requirements_input, locked_export


def _setup_runtime_dependency_names() -> set[str]:
    setup_tree = ast.parse((REPO_ROOT / "setup.py").read_text(encoding="utf-8"))
    for node in ast.walk(setup_tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "setup":
            continue
        install_requires = next((keyword.value for keyword in node.keywords if keyword.arg == "install_requires"), None)
        if install_requires is None:
            raise AssertionError("setup.py must declare install_requires")
        dependencies = ast.literal_eval(install_requires)
        return {Requirement(dependency).name.casefold() for dependency in dependencies}
    raise AssertionError("setup.py must call setup")


def test_reproducible_delivery_checker_is_versioned() -> None:
    """The lock/export/fixture verifier must be available to local and CI callers."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    assert checker.is_file()


def test_primary_license_scope_excludes_the_code_review_exception() -> None:
    """The primary environment behavior rejects the exact Code Review-only exception."""
    entry = _license_allowlist_entry("pylint")
    policy = _load_license_scope_policy()

    assert not policy.environment_allowlist_entry_matches(
        entry,
        "GPL-2.0-or-later",
        "4.0.7",
        allowlist_scope="dev-only",
    )
    _assert_license_scope_predicate_is_used_by_the_gate()


def test_code_review_license_scope_is_exactly_version_and_environment_bound() -> None:
    """The dedicated Code Review behavior accepts only its exact scoped metadata."""
    entry = _license_allowlist_entry("pylint")
    policy = _load_license_scope_policy()

    assert policy.environment_allowlist_entry_matches(
        entry,
        "GPL-2.0-or-later",
        "4.0.7",
        allowlist_scope="code-review-only",
    )
    assert not policy.environment_allowlist_entry_matches(
        entry,
        "GPL-2.0-or-later",
        "4.0.8",
        allowlist_scope="code-review-only",
    )
    assert not policy.environment_allowlist_entry_matches(
        entry,
        "MIT",
        "4.0.7",
        allowlist_scope="code-review-only",
    )
    _assert_license_scope_predicate_is_used_by_the_gate()


def test_reproducible_delivery_checker_verifies_hashed_export() -> None:
    """The frozen export must be a checked-in, hash-protected install input."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("check_reproducible_delivery", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.LOCKED_EXPORT.is_file()
    module.verify_locked_export()


def test_reproducible_delivery_checker_verifies_code_review_input_lock_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The isolated Code Review lock must be reproducibly compiled from its input."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("check_reproducible_delivery", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.CODE_REVIEW_REQUIREMENTS_INPUT.is_file()
    assert module.CODE_REVIEW_LOCKED_EXPORT.is_file()
    lock = module.CODE_REVIEW_LOCKED_EXPORT.read_text(encoding="utf-8")

    def compile_to_temporary_file(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        output = command[command.index("--output-file") + 1]
        assert output != "-"
        Path(output).write_text(lock, encoding="utf-8")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", compile_to_temporary_file)
    module.verify_code_review_lock()


def test_code_review_lock_verification_constrains_live_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """New transitive releases must not change verification of an unchanged lock."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("check_reproducible_delivery", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lock = module.CODE_REVIEW_LOCKED_EXPORT.read_text(encoding="utf-8")

    def compile_with_committed_constraints(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        constraint = command[command.index("--constraints") + 1]
        assert constraint == str(module.CODE_REVIEW_LOCKED_EXPORT.relative_to(module.REPO_ROOT))
        assert "--upgrade" not in command
        output = command[command.index("--output-file") + 1]
        Path(output).write_text(lock, encoding="utf-8")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", compile_with_committed_constraints)
    module.verify_code_review_lock()


@pytest.mark.parametrize("binding_state", ["missing", "malformed", "duplicate", "mismatch"])
def test_code_review_lock_verification_rejects_invalid_input_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    binding_state: str,
) -> None:
    """The committed lock must bind the exact isolated tooling input once."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("check_reproducible_delivery", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    requirements_input, locked_export = _write_invalid_binding_fixture(module, tmp_path, binding_state)
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path / "repository")
    monkeypatch.setattr(module, "CODE_REVIEW_REQUIREMENTS_INPUT", requirements_input)
    monkeypatch.setattr(module, "CODE_REVIEW_LOCKED_EXPORT", locked_export)

    def compile_matching_lock(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        output = command[command.index("--output-file") + 1]
        Path(output).write_text(locked_export.read_text(encoding="utf-8"), encoding="utf-8")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", compile_matching_lock)

    with pytest.raises(ValueError, match="input SHA-256 binding"):
        module.verify_code_review_lock()


def test_reproducible_delivery_checker_rejects_stale_code_review_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A resolver result that differs from the isolated lock must fail closed."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("check_reproducible_delivery", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lock = module.CODE_REVIEW_LOCKED_EXPORT.read_text(encoding="utf-8")
    stale_result = lock.replace("pylint==4.0.7", "pylint==4.0.8")

    def compile_stale_result(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        output = command[command.index("--output-file") + 1]
        Path(output).write_text(stale_result, encoding="utf-8")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", compile_stale_result)

    with pytest.raises(ValueError, match=r"differs from requirements\.in"):
        module.verify_code_review_lock()


def test_reproducible_delivery_refresh_uses_locked_export_contract() -> None:
    """Refresh is explicit and re-validates the generated delivery inputs."""
    refresh = (REPO_ROOT / "scripts" / "refresh_reproducible_delivery.py").read_text(encoding="utf-8")
    assert '"uv", "lock"' in refresh
    assert '"export",' in refresh
    assert "--locked" in refresh
    assert "--no-emit-project" in refresh
    assert "check_reproducible_delivery.py" in refresh
    assert "timeout=" in refresh
    assert "TimeoutExpired" in refresh


def test_reproducible_delivery_refresh_renders_code_review_input_binding() -> None:
    """The isolated lock refresh must atomically renew its exact input binding."""
    refresh_path = REPO_ROOT / "scripts" / "refresh_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("refresh_reproducible_delivery", refresh_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    input_bytes = b"pylint==4.0.7\n"
    generated = "# temporary uv command\nastroid==4.0.4 \\\n    --hash=sha256:abc\n"

    rendered = module.render_code_review_lock(generated, input_bytes)

    expected_digest = hashlib.sha256(input_bytes).hexdigest()
    assert rendered.startswith(
        "# This file was autogenerated by "
        "`python scripts/refresh_reproducible_delivery.py --code-review`.\n"
        f"# input-sha256: {expected_digest}\n"
    )
    assert rendered.count("# input-sha256:") == 1
    assert "# temporary uv command" not in rendered
    assert "astroid==4.0.4" in rendered


def test_reproducible_delivery_verifier_bounds_uv_commands_and_fails_closed_on_timeout() -> None:
    """Frozen-delivery validation must not hang indefinitely on a stalled uv process."""
    checker = (REPO_ROOT / "scripts" / "check_reproducible_delivery.py").read_text(encoding="utf-8")
    assert checker.count("timeout=") >= 2
    assert "subprocess.TimeoutExpired" in checker


def test_reproducible_delivery_wheel_build_uses_a_locked_backend() -> None:
    """The no-isolation wheel proof must use the backend pinned in delivery inputs."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["build-system"]["requires"] == ["hatchling==1.32.0"]
    assert "hatchling==1.32.0" in project["project"]["optional-dependencies"]["dev"]
    assert "twine>=7.0" in project["project"]["optional-dependencies"]["dev"]
    assert "core-metadata-version" not in project["tool"]["hatch"]["build"]["targets"]["wheel"]

    workflow = (REPO_ROOT / ".github" / "workflows" / "pr-orchestrator.yml").read_text(encoding="utf-8")
    assert "Build package once\n        run: uv build --wheel --no-build-isolation" in workflow


def test_reproducible_delivery_pins_patched_pip_to_tooling_only() -> None:
    """The fixed pip floor must cover tooling without expanding core runtime dependencies."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = project["project"]["optional-dependencies"]["dev"]
    hatch_dependencies = project["tool"]["hatch"]["envs"]["default"]["dependencies"]
    runtime_names = {Requirement(dependency).name.casefold() for dependency in project["project"]["dependencies"]}

    assert "pip>=26.2" in dev_dependencies
    assert "pip>=26.2" in hatch_dependencies
    assert "pip-tools>=7.6.1" in dev_dependencies
    assert "pip-tools>=7.6.1" in hatch_dependencies
    assert "pip" not in runtime_names
    assert "pip" not in _setup_runtime_dependency_names()


def test_reproducible_delivery_pins_semgrep_with_fixed_mcp_without_waiver() -> None:
    """A compatible Semgrep must replace, rather than extend, the vulnerable MCP waiver."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    locked_packages = _locked_package_versions()
    locked_export = (REPO_ROOT / "requirements" / "ci" / "locked.txt").read_text(encoding="utf-8")
    exception_register = _load_json("ci/vulnerability-audit-exceptions.json")
    security_floors = _load_json("ci/security-tool-minimum-versions.json")
    runtime_names = _runtime_dependency_names(project)

    _assert_semgrep_declarations(project)
    _assert_fixed_semgrep_snapshot(locked_packages, locked_export)
    _assert_semgrep_security_policy(security_floors, exception_register)
    assert {"semgrep", "mcp"}.isdisjoint(runtime_names)
    assert {"semgrep", "mcp"}.isdisjoint(_setup_runtime_dependency_names())


def test_reproducible_delivery_pins_pycg_consistently_across_tool_groups() -> None:
    """All development tool groups must select the reviewed PyCG release."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    optional_dependencies = project["project"]["optional-dependencies"]
    hatch_dependencies = project["tool"]["hatch"]["envs"]["default"]["dependencies"]
    hatch_test_dependencies = project["tool"]["hatch"]["envs"]["hatch-test"]["dependencies"]

    assert "pycg==0.0.8" in optional_dependencies["dev"]
    assert "pycg==0.0.8" in optional_dependencies["enhanced-analysis"]
    assert "pycg==0.0.8" in hatch_dependencies
    assert "pycg==0.0.8" in hatch_test_dependencies


def test_reproducible_delivery_refresh_rejects_a_symlinked_output_parent(tmp_path: Path) -> None:
    """Refresh must not write a generated export through a repository symlink."""
    refresh_path = REPO_ROOT / "scripts" / "refresh_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("refresh_reproducible_delivery", refresh_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    requirements = repository / "requirements"
    requirements.symlink_to(outside, target_is_directory=True)
    output = requirements / "ci" / "locked.txt"

    with pytest.raises(OSError, match="symlink"):
        module.validate_locked_export_path(output, repository)


def _render_example_sbom(renderer: Path, tmp_path: Path) -> dict[str, Any]:
    inspect_report = tmp_path / "inspect.json"
    inspect_report.write_text(
        json.dumps(
            {
                "installed": [
                    {"metadata": {"name": "Example-CLI", "version": "2.0.0"}},
                    {"metadata": {"name": "another-package", "version": "1.0.0"}},
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "locked.spdx.json"

    completed = subprocess.run(
        [sys.executable, str(renderer), "--inspect", str(inspect_report), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    return json.loads(output.read_text(encoding="utf-8"))


def test_locked_sbom_renderer_uses_pip_inspect_without_generator_dependency(tmp_path: Path) -> None:
    """Delivery SBOM evidence must be local, deterministic, and dependency-free."""
    renderer = REPO_ROOT / "scripts" / "render_locked_sbom.py"
    assert renderer.is_file()

    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = project["project"]["optional-dependencies"]["dev"]
    assert all("cyclonedx" not in dependency.lower() for dependency in dev_dependencies)

    payload = _render_example_sbom(renderer, tmp_path)
    assert payload["spdxVersion"] == "SPDX-2.3"
    assert payload["creationInfo"]["created"] == "1970-01-01T00:00:00Z"
    assert [(package["name"], package["versionInfo"]) for package in payload["packages"]] == [
        ("another-package", "1.0.0"),
        ("Example-CLI", "2.0.0"),
    ]
    assert payload["packages"][0]["externalRefs"] == [
        {
            "referenceCategory": "PACKAGE-MANAGER",
            "referenceLocator": "pkg:pypi/another-package@1.0.0",
            "referenceType": "purl",
        }
    ]
