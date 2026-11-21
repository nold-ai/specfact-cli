from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]
CLOCK = (
    "refs/heads/codex/dev786-berlin-clock-signer-20261115",
    "refs/heads/codex/security-dev-berlin-clock-candidate-20261115",
    "e753ac1a3e4bb3bf739bd7203c728a652db6cb90",
)
LEGACY = (
    "refs/heads/codex/dev786-ci-tail-signer-20261104",
    "refs/heads/codex/security-dev-ci-tail-candidate-20261104",
    "b0184ae8c3de2c107d888dc23b0e7402a31d520e",
)


@pytest.fixture
def owner() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_clock_signer_owner", ROOT / "scripts/requirements_late_red_proof.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("origin", [LEGACY, CLOCK])
def test_intent_accepts_only_matching_executor_origin(
    owner: ModuleType, monkeypatch: pytest.MonkeyPatch, origin: tuple[str, str, str]
) -> None:
    program = b"synthetic finite signer"
    pin = (("scripts/dev_security_ci_signer.py", hashlib.sha256(program).hexdigest()),)
    name = "_FIXED_PR786_CLOCK_SIGNER_FILES" if origin == CLOCK else "_FIXED_PR786_SIGNER_FILES"
    monkeypatch.setattr(owner, name, pin)
    intent = {
        "repository_id": 7,
        "repository_full_name": "nold-ai/specfact-cli",
        "actor": {},
        "triggering_actor": {},
        "dev": "9b5ad1e78430cc0b061cb16de42f73de96f4f312",
        "main": "1" * 40,
        "checkpoints": [],
        "auxiliary_ref": origin[0],
        "destination": origin[1],
    }
    raw = json.dumps(intent).encode()
    helper = ModuleType("synthetic_api")
    monkeypatch.setattr(
        helper, "_api_json", lambda *args: ({"id": 7, "full_name": "nold-ai/specfact-cli"}, None), raising=False
    )
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-no-network")
    monkeypatch.setattr(
        owner, "_fixed_pr786_blob", lambda helper, tree, path: raw if str(path).endswith("intent.json") else program
    )
    result = owner._fixed_pr786_intent(helper, {}, hashlib.sha256(raw).hexdigest())
    assert result == intent
    assert owner._fixed_pr786_origin(result) == origin
    intent["destination"] = CLOCK[1] if origin == LEGACY else LEGACY[1]
    raw = json.dumps(intent).encode()
    with pytest.raises(ValueError):
        owner._fixed_pr786_intent(helper, {}, hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize("origin", [LEGACY, CLOCK])
def test_output_chain_stops_at_its_own_authenticated_source_root(
    owner: ModuleType, monkeypatch: pytest.MonkeyPatch, origin: tuple[str, str, str]
) -> None:
    parent = origin[2]
    final = {"sha": "f" * 40, "parents": [{"sha": parent}]}
    checkpoints = [
        {"source_parent": parent, "source_commit": "a" * 40, "source_tree": "b" * 40, "source_message": "normal source"}
    ]
    helper = ModuleType("synthetic_api")
    monkeypatch.setattr(helper, "_api_json", lambda *args: ({"sha": parent}, None), raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-no-network")
    monkeypatch.setattr(owner, "_fixed_pr786_signed", lambda *args: None)
    owner._fixed_pr786_outputs(helper, final, checkpoints, ("c" * 64, "d" * 40, 91))
    monkeypatch.setattr(helper, "_api_json", lambda *args: ({"sha": LEGACY[2] if origin == CLOCK else CLOCK[2]}, None))
    with pytest.raises(ValueError):
        owner._fixed_pr786_outputs(helper, final, checkpoints, ("c" * 64, "d" * 40, 91))


@pytest.mark.parametrize("origin", [LEGACY, CLOCK])
@pytest.mark.parametrize(
    "changed",
    [
        None,
        "scripts/dev_security_ci_signer.py",
        ".github/workflows/specfact.yml",
        "ci/recovery/dev-security-signer-runtime.txt",
    ],
)
def test_executor_requires_every_exact_pinned_file(
    owner: ModuleType, monkeypatch: pytest.MonkeyPatch, origin: tuple[str, str, str], changed: str | None
) -> None:
    files = {
        "scripts/dev_security_ci_signer.py": b'_ALLOWED = frozenset({"only-approved.py"})',
        ".github/workflows/specfact.yml": b"reviewed workflow",
        "ci/recovery/dev-security-signer-runtime.txt": b"reviewed runtime",
    }
    pins = tuple((name, hashlib.sha256(raw).hexdigest()) for name, raw in files.items())
    name = "_FIXED_PR786_CLOCK_SIGNER_FILES" if origin == CLOCK else "_FIXED_PR786_SIGNER_FILES"
    monkeypatch.setattr(owner, name, pins)
    if changed:
        files[changed] += b"tampered"
    helper = ModuleType("synthetic_api")
    monkeypatch.setattr(
        helper, "_api_json", lambda *args: ({"sha": "a" * 40, "tree": {"sha": "b" * 40}}, None), raising=False
    )
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-no-network")
    monkeypatch.setattr(owner, "_fixed_pr786_tree", lambda *args: {})
    monkeypatch.setattr(owner, "_fixed_pr786_blob", lambda helper, tree, path: files[path])
    if changed:
        with pytest.raises(ValueError):
            owner._fixed_pr786_executor_tree(helper, "a" * 40)
    else:
        assert owner._fixed_pr786_executor_tree(helper, "a" * 40) == ({}, {"only-approved.py"})


@pytest.mark.parametrize("origin", [LEGACY, CLOCK])
def test_intent_rejects_the_other_pinned_program(
    owner: ModuleType, monkeypatch: pytest.MonkeyPatch, origin: tuple[str, str, str]
) -> None:
    program = b"other origin"
    intent = {
        "repository_id": 7,
        "repository_full_name": "nold-ai/specfact-cli",
        "actor": {},
        "triggering_actor": {},
        "dev": "9b5ad1e78430cc0b061cb16de42f73de96f4f312",
        "main": "1" * 40,
        "checkpoints": [],
        "auxiliary_ref": origin[0],
        "destination": origin[1],
    }
    raw = json.dumps(intent).encode()
    monkeypatch.setattr(
        owner, "_fixed_pr786_blob", lambda helper, tree, path: raw if str(path).endswith("intent.json") else program
    )
    with pytest.raises(ValueError):
        owner._fixed_pr786_intent(ModuleType("unused_api"), {}, hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize("origin", [LEGACY, CLOCK])
@pytest.mark.parametrize("case", ["valid", "wrong-branch", "attempt-two", "duplicate", "incomplete", "wrong-workflow"])
def test_inline_workflow_authenticates_each_exact_completed_origin(origin: tuple[str, str, str], case: str) -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/requirements-evidence.yml").read_text())
    steps = workflow["jobs"]["requirements-fixed786-origin"]["steps"]
    program = next(step["run"] for step in steps if "expected_run = {" in step.get("run", ""))
    source = program.split("python3 -I -S - <<'PYTHON'\n", 1)[1].split("\nPYTHON", 1)[0]
    nodes = ast.parse(source).body
    assignments = {
        target.id: index
        for index, node in enumerate(nodes)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    selected = ast.Module(body=nodes[assignments["run_id"] : assignments["artifacts"]], type_ignores=[])
    actor = {"id": 7, "login": "synthetic"}
    run = {
        "id": 91,
        "run_attempt": 1,
        "head_sha": "a" * 40,
        "head_branch": origin[0].removeprefix("refs/heads/"),
        "event": "workflow_dispatch",
        "path": ".github/workflows/specfact.yml",
        "workflow_id": 204352514,
        "status": "completed",
        "conclusion": "success",
        "repository": {"full_name": "nold-ai/specfact-cli", "id": 7},
        "actor": actor,
        "triggering_actor": actor,
    }
    if case == "wrong-branch":
        run["head_branch"] = (
            CLOCK[0].removeprefix("refs/heads/") if origin == LEGACY else LEGACY[0].removeprefix("refs/heads/")
        )
    if case == "attempt-two":
        run["run_attempt"] = 2
    if case == "wrong-workflow":
        run["workflow_id"] = 1
    history = {"total_count": 1, "workflow_runs": [dict(run)]}
    if case == "duplicate":
        history = {"total_count": 2, "workflow_runs": [dict(run), {**run, "id": 92}]}
    if case == "incomplete":
        history["total_count"] = 2
    namespace = {
        "get": lambda path: history if "per_page" in path else run,
        "run_text": "91",
        "executor": "a" * 40,
        "intent": {"repository_id": 7, "actor": actor, "triggering_actor": actor, "auxiliary_ref": origin[0]},
    }
    code = compile(ast.fix_missing_locations(selected), "actual-workflow-run-admission", "exec")
    if case == "valid":
        exec(code, namespace)
    else:
        with pytest.raises(ValueError):
            exec(code, namespace)


@pytest.mark.parametrize("policy", ["security_audit_gate", "check_dependency_trust_exceptions"])
@pytest.mark.parametrize("expired", [False, True])
def test_fresh_owner_risk_register_keeps_its_own_expiry(
    policy: str, expired: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import date

    spec = importlib.util.spec_from_file_location("_fresh_risk_" + policy, ROOT / "scripts" / (policy + ".py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if policy == "check_dependency_trust_exceptions":
        register = module.DEFAULT_REGISTER
        errors = module.validate_exception_register(
            register, today=date(2026, 11, 22) if expired else date(2026, 11, 16)
        )
    else:

        class CurrentDate(date):
            @classmethod
            def today(cls) -> date:
                return date(2026, 11, 22) if expired else date(2026, 11, 21)

        monkeypatch.setattr(module, "date", CurrentDate)
        register = ROOT / module.DEFAULT_EXCEPTIONS_FILE
        _, errors = module._load_reviewed_exceptions(register)
    assert bool(errors) is expired
