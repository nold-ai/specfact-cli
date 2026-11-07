"""Contract tests for frozen-delivery support scripts."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest
from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[3]


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
    stale_result = lock.replace("pylint==4.0.9", "pylint==4.0.8")
    assert stale_result != lock

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
    assert project["build-system"]["requires"] == ["hatchling==1.32.4"]
    assert "hatchling==1.32.4" in project["project"]["optional-dependencies"]["dev"]
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

    spec = importlib.util.spec_from_file_location("python_sbom_renderer_test", renderer)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = module.render_sbom(json.loads(inspect_report.read_text(encoding="utf-8")))
    output.write_text(json.dumps(payload), encoding="utf-8")
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


def test_smoke_lock_rejects_unreviewed_input_change(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A changed smoke seed cannot reuse the old reviewed lock binding."""
    checker = REPO_ROOT / "scripts/check_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("check_reproducible_delivery", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    altered = tmp_path / "requirements.in"
    altered.write_text("lz4==0.0.0\n")
    monkeypatch.setattr(module, "RUNTIME_SMOKE_REQUIREMENTS_INPUT", altered, raising=False)
    with pytest.raises(ValueError, match="input SHA-256 binding does not match"):
        module.verify_runtime_smoke_lock()


@pytest.fixture
def native_sbom_example() -> tuple[Any, dict[str, Any], dict[str, Any]]:
    renderer = REPO_ROOT / "scripts/render_locked_sbom.py"
    spec = importlib.util.spec_from_file_location("native_sbom_renderer_test", renderer)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inventory = {
        "name": "semgrep-native",
        "version": "1.184.0",
        "platform": "linux-x86_64",
        "policy_sha256": "a" * 64,
        "artifact_url": "https://files.pythonhosted.org/selected.whl",
        "artifact_sha256": "b" * 64,
        "files": [
            {"path": "osemgrep", "sha256": "c" * 64, "sha1": "c" * 40, "size": 12},
            {"path": "libs/libcurl.so.4", "sha256": "d" * 64, "sha1": "d" * 40, "size": 20},
            {"path": "THIRD_PARTY_NOTICES.html", "sha256": "e" * 64, "sha1": "e" * 40, "size": 30},
        ],
    }
    first = module.render_sbom({"installed": []})
    module._append_native_inventory(first, inventory)
    return module, inventory, first


def test_native_sbom_preserves_sdk_package_claims(
    native_sbom_example: tuple[Any, dict[str, Any], dict[str, Any]],
) -> None:
    _module, _inventory, first = native_sbom_example
    assert [(p["name"], p["versionInfo"], p["filesAnalyzed"]) for p in first["packages"]] == [
        ("semgrep-native", "1.184.0", True)
    ]
    assert "supplier attribution" in first["packages"][0]["comment"]
    assert "linux-x86_64" in first["packages"][0]["comment"]
    assert first["documentDescribes"] == ["SPDXRef-Package-semgrep-native"]
    assert first["packages"][0]["downloadLocation"] == "NOASSERTION"
    assert first["packages"][0]["supplier"] == "NOASSERTION"
    assert first["packages"][0]["licenseDeclared"] == "NOASSERTION"
    assert first["packages"][0]["licenseInfoFromFiles"] == ["NOASSERTION"]
    assert (
        first["packages"][0]["packageVerificationCode"]["packageVerificationCodeValue"]
        == hashlib.sha1(("c" * 40 + "d" * 40 + "e" * 40).encode("ascii"), usedforsecurity=False).hexdigest()
    )


def test_native_sbom_retains_source_identity(native_sbom_example: tuple[Any, dict[str, Any], dict[str, Any]]) -> None:
    _module, _inventory, first = native_sbom_example
    assert (
        "upstream Semgrep wheel https://files.pythonhosted.org/selected.whl SHA256 " + "b" * 64
        in first["packages"][0]["sourceInfo"]
    )


def test_native_sbom_records_verified_files(native_sbom_example: tuple[Any, dict[str, Any], dict[str, Any]]) -> None:
    _module, inventory, first = native_sbom_example
    assert [(f["fileName"], f["checksums"]) for f in first["files"]] == [
        (
            "./native/" + f["path"],
            [
                {"algorithm": "SHA256", "checksumValue": f["sha256"]},
                {"algorithm": "SHA1", "checksumValue": f["sha1"]},
            ],
        )
        for f in inventory["files"]
    ]
    assert all(f["licenseConcluded"] == "NOASSERTION" for f in first["files"])
    assert len(first["relationships"]) == 3


def test_native_sbom_namespace_binds_final_bytes(
    native_sbom_example: tuple[Any, dict[str, Any], dict[str, Any]],
) -> None:
    module, inventory, first = native_sbom_example
    assert first["documentNamespace"] != module.render_sbom({"installed": []})["documentNamespace"]
    inventory["files"][1]["sha256"] = "f" * 64
    second = module.render_sbom({"installed": []})
    module._append_native_inventory(second, inventory)
    assert first["documentNamespace"] != second["documentNamespace"]


@pytest.mark.parametrize(
    "name,version", [("pcre2", "10.49"), ("libcurl-minimal", "7.76.1-40.el9_8.9"), ("curl", "8.23.0")]
)
def test_native_sbom_exposes_corrected_component_version(name: str, version: str) -> None:
    spec = importlib.util.spec_from_file_location("component_sbom_test", REPO_ROOT / "scripts/render_locked_sbom.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inventory = {
        "name": "semgrep-native",
        "version": "1.184.0",
        "platform": "test",
        "policy_sha256": "a" * 64,
        "artifact_url": "https://example.invalid/upstream.whl",
        "artifact_sha256": "b" * 64,
        "files": [{"path": "library", "sha256": "c" * 64, "sha1": "d" * 40, "size": 10}],
        "components": [
            {
                "name": name,
                "version": version,
                "files": ["library"],
                "source_info": "frozen correction source",
                "notice_paths": [],
            }
        ],
    }
    document = module.render_sbom({"installed": []})
    module._append_native_inventory(document, inventory)
    component = next(item for item in document["packages"] if item["name"] == name)
    assert component["versionInfo"] == version
    assert component["licenseDeclared"] == "NOASSERTION"
    assert component["licenseConcluded"] == "NOASSERTION"
    assert component["sourceInfo"] == "frozen correction source"
    assert {
        "spdxElementId": component["SPDXID"],
        "relationshipType": "CONTAINS",
        "relatedSpdxElement": document["files"][0]["SPDXID"],
    } in document["relationships"]
