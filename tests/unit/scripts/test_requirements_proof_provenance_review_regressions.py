"""Regression coverage for security-review bypasses outside the retained red selector set."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"


def _load_provenance_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance_review", PROVENANCE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _commit(module: ModuleType, repo_root: Path, message: str) -> str:
    module._git(repo_root, "add", ".").check_returncode()
    module._git(
        repo_root,
        "-c",
        "user.name=Requirements proof",
        "-c",
        "user.email=requirements@example.test",
        "commit",
        "--no-gpg-sign",
        "-m",
        message,
    ).check_returncode()
    result = module._git(repo_root, "rev-parse", "HEAD")
    result.check_returncode()
    return result.stdout.strip()


def _initialize_bound_red_proof(
    module: ModuleType,
    repo_root: Path,
    *,
    pytest_configuration: tuple[str, str] | None = None,
    initial_files: dict[str, str] | None = None,
) -> tuple[Path, str]:
    module._git(repo_root, "init").check_returncode()
    module._git(repo_root, "config", "user.email", "requirements@example.test").check_returncode()
    module._git(repo_root, "config", "user.name", "Requirements proof").check_returncode()
    (repo_root / "README.md").write_text("# proof\n", encoding="utf-8")
    if pytest_configuration is not None:
        config_path, content = pytest_configuration
        (repo_root / config_path).write_text(content, encoding="utf-8")
    for relative_path, content in (initial_files or {}).items():
        target = repo_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    base_ref = _commit(module, repo_root, "base")
    test_path = repo_root / "tests" / "test_proof.py"
    test_path.parent.mkdir(exist_ok=True)
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(module, repo_root, "red test")
    proof_path = repo_root / ".git" / "red.json"
    junit = (
        b'<testsuite><testcase><properties><property name="specfact.selector" '
        b'value="tests/test_proof.py::test_selected"/><property name="specfact.runner" value="pytest"/>'
        b'<property name="specfact.python" value="3.12"/><property name="specfact.pytest" value="9.1"/>'
        b"</properties><failure/></testcase></testsuite>"
    )
    proof_path.with_suffix(".xml").write_bytes(junit)
    mapping_digest = f"sha256:{'a' * 64}"
    plan_digest = f"sha256:{'b' * 64}"
    proof_path.write_text(
        json.dumps(
            {
                "gate_decision": "pass",
                "observed_maturity": "red",
                "mapping_digest": mapping_digest,
                "plan_digest": plan_digest,
                "plan": {
                    "mapping_digest": mapping_digest,
                    "plan_digest": plan_digest,
                    "cases": [
                        {
                            "requirement_id": "openspec:test:capability:requirement",
                            "case_id": "CASE-S01",
                            "touchpoints": [
                                {
                                    "id": "selected-test",
                                    "kind": "test_file",
                                    "locator": "tests/test_proof.py",
                                }
                            ],
                        }
                    ],
                },
                "execution_proof": {
                    "run_stage": "red",
                    "source_ref": red_ref,
                    "selectors": ["tests/test_proof.py::test_selected"],
                    "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
                },
            }
        ),
        encoding="utf-8",
    )
    module.bind_red_proof(proof_path, repo_root, base_ref=base_ref)
    return proof_path, base_ref


def test_pytest_configuration_plugin_changed_after_red_invalidates_proof(tmp_path: Path) -> None:
    """A plugin loaded by red-time addopts remains part of the immutable harness."""
    configurations = (
        ("pytest.ini", "[pytest]\naddopts = -p tests.helpers.hidden\n"),
        ("pytest.toml", '[pytest]\naddopts = ["-p", "tests.helpers.hidden"]\n'),
    )
    for index, configuration in enumerate(configurations):
        module = _load_provenance_module()
        repository = tmp_path / f"repository-{index}"
        repository.mkdir()
        proof_path, base_ref = _initialize_bound_red_proof(module, repository, pytest_configuration=configuration)
        plugin_path = repository / "tests" / "helpers" / "hidden.py"
        plugin_path.parent.mkdir()
        plugin_path.write_text("VALUE = True\n", encoding="utf-8")
        final_ref = _commit(module, repository, "add configured pytest plugin")
        assert module.validate_prior_red_proof(proof_path, repository, base_ref=base_ref, final_ref=final_ref) == [
            "stale-red-proof"
        ]


def test_compact_pytest_plugin_options_changed_after_red_invalidate_proof(tmp_path: Path) -> None:
    """Compact pytest plugin flags retain the same repository plugin inputs."""
    for index, option in enumerate(("-ptests.helpers.hidden", "-p=tests.helpers.hidden")):
        module = _load_provenance_module()
        repository = tmp_path / f"repository-{index}"
        repository.mkdir()
        proof_path, base_ref = _initialize_bound_red_proof(
            module,
            repository,
            pytest_configuration=("pytest.ini", f"[pytest]\naddopts = {option}\n"),
            initial_files={"tests/helpers/hidden.py": "VALUE = 'red'\n"},
        )
        plugin_path = repository / "tests" / "helpers" / "hidden.py"
        plugin_path.write_text("VALUE = 'final'\n", encoding="utf-8")
        final_ref = _commit(module, repository, "change configured pytest plugin")
        assert module.validate_prior_red_proof(proof_path, repository, base_ref=base_ref, final_ref=final_ref) == [
            "stale-red-proof"
        ]


def test_pytest_configuration_added_after_red_invalidates_proof(tmp_path: Path) -> None:
    """A post-red addopts plugin cannot change the selected-test harness."""
    config_paths = (
        "pytest.toml",
        ".pytest.toml",
        "pytest.ini",
        ".pytest.ini",
        "pyproject.toml",
        "tox.ini",
        "setup.cfg",
        "tests/pytest.ini",
    )
    for index, config_path in enumerate(config_paths):
        module = _load_provenance_module()
        repository = tmp_path / f"repository-{index}"
        repository.mkdir()
        proof_path, base_ref = _initialize_bound_red_proof(module, repository)
        (repository / config_path).write_text("[pytest]\naddopts = -p tests.helpers.hidden\n", encoding="utf-8")
        final_ref = _commit(module, repository, "inject pytest plugin")
        assert module.validate_prior_red_proof(proof_path, repository, base_ref=base_ref, final_ref=final_ref) == [
            "stale-red-proof"
        ]


def test_dynamic_repository_import_change_after_red_invalidates_proof(tmp_path: Path) -> None:
    """A dynamically imported helper remains immutable after the red source."""
    module = _load_provenance_module()
    repository = tmp_path / "repository"
    repository.mkdir()
    proof_path, base_ref = _initialize_bound_red_proof(
        module,
        repository,
        initial_files={
            "conftest.py": 'import importlib\nimportlib.import_module("tests.helpers.hidden")\n',
            "tests/helpers/hidden.py": "VALUE = 'red'\n",
        },
    )
    helper = repository / "tests" / "helpers" / "hidden.py"
    helper.write_text("VALUE = 'final'\n", encoding="utf-8")
    final_ref = _commit(module, repository, "change dynamically imported helper")
    assert module.validate_prior_red_proof(
        proof_path,
        repository,
        base_ref=base_ref,
        final_ref=final_ref,
    ) == ["stale-red-proof"]


def test_core_proof_inputs_and_selected_package_initializers_are_retained(tmp_path: Path) -> None:
    """Every fixed producer and implicit package initializer must be freshness-bound."""
    module = _load_provenance_module()
    repository = tmp_path / "repository"
    repository.mkdir()
    proof_path, base_ref = _initialize_bound_red_proof(
        module,
        repository,
        initial_files={
            "tests/__init__.py": "VALUE = 'red'\n",
            "scripts/__init__.py": "VALUE = 'red'\n",
            "uv.lock": "version = 1\n",
            "scripts/requirements_proof_executor.py": "VALUE = 'red'\n",
            "scripts/requirements_proof_pytest_plugin.py": "VALUE = 'red'\n",
        },
    )

    for index, path in enumerate(
        (
            "tests/__init__.py",
            "scripts/__init__.py",
            "uv.lock",
            "scripts/requirements_proof_executor.py",
            "scripts/requirements_proof_pytest_plugin.py",
        )
    ):
        checkout = repository.parent / f"candidate-{index}"
        shutil.copytree(repository, checkout)
        target = checkout / path
        target.write_text(target.read_text(encoding="utf-8") + "VALUE = 'final'\n", encoding="utf-8")
        final_ref = _commit(module, checkout, f"change {path}")
        candidate_proof = checkout / ".git" / "red.json"
        candidate_proof.write_bytes(proof_path.read_bytes())
        candidate_proof.with_suffix(".xml").write_bytes(proof_path.with_suffix(".xml").read_bytes())
        assert module.validate_prior_red_proof(
            candidate_proof,
            checkout,
            base_ref=base_ref,
            final_ref=final_ref,
        ) == ["stale-red-proof"]


def test_external_digest_is_forwarded_during_ordinary_cycle_revalidation(tmp_path: Path) -> None:
    """A derived cycle receipt must revalidate the exact external green binding."""
    module = _load_provenance_module()
    observed: dict[str, object] = {}
    trusted = type(
        "Trusted",
        (),
        {"cycle_base": "a" * 40, "run_id": 42, "artifact_id": 84, "artifact_digest": f"sha256:{'b' * 64}"},
    )()

    class CycleModule:
        CycleBasePaths = staticmethod(lambda **arguments: arguments)
        CycleBaseContext = staticmethod(lambda **arguments: arguments)

        @staticmethod
        def validated_cycle_base(*_arguments: object, **keywords: object) -> object:
            observed.update(keywords)
            return trusted

    module.__dict__["_cycle_module"] = lambda: CycleModule
    context = module.CycleAuthorityContext(
        tmp_path,
        "c" * 40,
        "d" * 40,
        "e" * 40,
        "nold-ai/specfact-cli",
        698,
        "codex/692-computed-owner-red-proof-v2",
        "fix-release-promotion-security-gates",
    )
    external_digest = f"sha256:{'f' * 64}"
    external_receipt = {"authority_digest": external_digest}

    assert (
        module._validated_live_cycle(
            context,
            tmp_path,
            module._LiveCyclePayload("{}", "{}"),
            external_authority_digest=external_digest,
            external_authority_receipt=external_receipt,
        )
        is trusted
    )
    assert observed["external_authority_digest"] == external_digest
    assert observed["external_authority_receipt"] == external_receipt


def test_ordinary_cycle_revalidates_the_live_external_capability(tmp_path: Path) -> None:
    """A public digest in an ordinary hint is not authority without a fresh external receipt."""
    module = _load_provenance_module()
    external_digest = f"sha256:{'a' * 64}"
    observed: list[str] = []
    context = module.CycleAuthorityContext(
        tmp_path,
        "b" * 40,
        "c" * 40,
        "d" * 40,
        "nold-ai/specfact-cli",
        698,
        "codex/692-computed-owner-red-proof-v2",
        "fix-release-promotion-security-gates",
    )
    authority_path = tmp_path / "authority.json"
    authority_path.write_text("{}", encoding="utf-8")
    receipt = tmp_path / "external-receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "kind": module.EXTERNAL_AMENDMENT_KIND,
                "comment_id": module.EXTERNAL_AMENDMENT_COMMENT_ID,
                "authority_version": 3,
                "producer_bypass": "stale-red-proof-only",
                "repository": context.repository,
                "change_id": context.change_id,
                "pull_request": context.pull_request,
                "head_branch": context.head_branch,
                "authority_digest": external_digest,
            }
        ),
        encoding="utf-8",
    )
    module.__dict__["_fetch_external_amendment"] = lambda *_arguments: (
        observed.append("fetched") or SimpleNamespace(receipt=receipt)
    )
    module.__dict__["_external_validator_command"] = lambda *_arguments: ["/usr/bin/true"]
    revalidated_digest, revalidated_receipt = module._revalidated_external_authority(
        context,
        tmp_path / "external-capability",
        external_digest,
    )
    assert revalidated_digest == external_digest
    assert revalidated_receipt["comment_id"] == module.EXTERNAL_AMENDMENT_COMMENT_ID
    assert observed == ["fetched"]
    observed.clear()
    hint = {
        "kind": "verified-pr-run",
        "prior_green_run_id": 42,
        "cycle_base": "e" * 40,
        "prior_green_artifact_id": 84,
        "prior_green_artifact_digest": f"sha256:{'f' * 64}",
        "external_authority_digest": external_digest,
    }
    trusted = type(
        "Trusted",
        (),
        {
            "cycle_base": hint["cycle_base"],
            "run_id": 42,
            "artifact_id": 84,
            "artifact_digest": hint["prior_green_artifact_digest"],
        },
    )()
    module.__dict__["_authority_hint"] = lambda *_arguments: hint
    module.__dict__["_revalidated_external_authority"] = lambda *_arguments: (
        observed.append(external_digest) or (external_digest, json.loads(receipt.read_text(encoding="utf-8")))
    )
    module.__dict__["_fetch_cycle_evidence"] = lambda *_arguments: ("{}", "{}", tmp_path)
    module.__dict__["_validated_live_cycle"] = lambda *_arguments, **_keywords: trusted
    module.__dict__["_cycle_payload_digest"] = lambda *_arguments: f"sha256:{'1' * 64}"

    assert module._read_cycle_authority(authority_path, context) is not None
    assert observed == [external_digest]
