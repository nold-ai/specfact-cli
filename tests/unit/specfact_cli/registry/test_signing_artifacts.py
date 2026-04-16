"""
Tests for signing automation artifacts (arch-06): script and CI workflow.
"""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
SIGN_SCRIPT = REPO_ROOT / "scripts" / "sign-module.sh"
SIGN_PYTHON_SCRIPT = REPO_ROOT / "scripts" / "sign-modules.py"
VERIFY_PYTHON_SCRIPT = REPO_ROOT / "scripts" / "verify-modules-signature.py"
SIGN_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sign-modules.yml"
PR_ORCHESTRATOR_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-orchestrator.yml"
PUBLISH_PYPI_SCRIPT = REPO_ROOT / ".github" / "workflows" / "scripts" / "check-and-publish-pypi.sh"


def _load_pr_orchestrator_jobs() -> dict[str, dict[str, Any]]:
    """Return the parsed jobs mapping for the PR orchestrator workflow."""
    if not PR_ORCHESTRATOR_WORKFLOW.exists():
        pytest.skip("pr-orchestrator workflow not present")
    data = yaml.safe_load(PR_ORCHESTRATOR_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "Expected mapping at pr-orchestrator workflow root"
    workflow_root = cast(dict[str, Any], data)
    jobs = workflow_root.get("jobs")
    assert isinstance(jobs, dict), "Expected jobs mapping in pr-orchestrator workflow"
    typed_jobs: dict[str, dict[str, Any]] = {}
    for name, job in jobs.items():
        assert isinstance(name, str), "Expected string job names in pr-orchestrator workflow"
        assert isinstance(job, dict), f"Expected mapping definition for job {name}"
        typed_jobs[name] = job
    return typed_jobs


def _read_text_or_skip(path: Path, *, reason: str) -> str:
    """Read a fixture file or skip when the artifact is absent in this checkout."""
    if not path.exists():
        pytest.skip(reason)
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("path", "message"),
    [
        (SIGN_SCRIPT, "scripts/sign-module.sh must exist for signing automation"),
        (VERIFY_PYTHON_SCRIPT, "scripts/verify-modules-signature.py must exist"),
    ],
)
def test_signing_artifacts_exist(path: Path, message: str) -> None:
    """Signing and verification entrypoints SHALL exist."""
    assert path.exists(), message


def test_sign_module_script_invocation_prints_or_produces_checksum(tmp_path: Path):
    """Signing script invocation SHALL produce or emit checksum for manifest integrity."""
    if not SIGN_SCRIPT.exists():
        pytest.skip("sign-module.sh not present")
    manifest = tmp_path / "module-package.yaml"
    manifest.write_text("name: test\nversion: 0.1.0\ncommands: [c]\n", encoding="utf-8")
    import subprocess

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert result.returncode != 0
    assert "--allow-unsigned" in result.stderr or "--key-file" in result.stderr

    allow_unsigned = subprocess.run(
        ["bash", str(SIGN_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert allow_unsigned.returncode == 0
    assert "sha256:" in allow_unsigned.stdout or "checksum" in allow_unsigned.stdout.lower()


def test_sign_module_script_supports_key_file_flag_order(tmp_path: Path):
    """Wrapper SHALL accept --key-file option before manifest and fail clearly on bad key path."""
    if not SIGN_SCRIPT.exists():
        pytest.skip("sign-module.sh not present")
    manifest = tmp_path / "module-package.yaml"
    manifest.write_text("name: test\nversion: 0.1.0\ncommands: [c]\n", encoding="utf-8")

    import subprocess

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), "--key-file", str(tmp_path / "missing.pem"), str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert result.returncode != 0
    assert "No such file or directory" in result.stderr or "missing.pem" in result.stderr


def test_sign_module_script_help_mentions_passphrase_options():
    """Wrapper help SHALL document passphrase options for encrypted private keys."""
    if not SIGN_SCRIPT.exists():
        pytest.skip("sign-module.sh not present")
    import subprocess

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert result.returncode == 0
    assert "--passphrase" in result.stdout
    assert "--passphrase-stdin" in result.stdout


def test_sign_module_script_enforces_version_bump_before_key_validation(tmp_path: Path):
    """Wrapper SHALL fail on unchanged module version even if signing key is missing."""
    if not SIGN_SCRIPT.exists():
        pytest.skip("sign-module.sh not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"
    source.parent.mkdir(parents=True)
    manifest.write_text("name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    # Change module payload without bumping module version.
    source.write_text("print('v2')\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), str(manifest)],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert result.returncode != 0
    assert "Module version must be incremented before signing changed module contents" in result.stderr


def test_sign_modules_py_requires_key_unless_allow_unsigned(tmp_path: Path):
    """sign-modules.py SHALL fail without key unless --allow-unsigned is passed."""
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")
    manifest = tmp_path / "module-package.yaml"
    manifest.write_text("name: test\nversion: 0.1.0\ncommands: [c]\n", encoding="utf-8")
    import subprocess

    no_key = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert no_key.returncode != 0
    assert "--key-file" in no_key.stderr or "--allow-unsigned" in no_key.stderr

    with_override = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert with_override.returncode == 0


@pytest.mark.parametrize(
    ("expected_flags", "description"),
    [
        (("--passphrase", "--passphrase-stdin", "--allow-same-version"), "passphrase sources"),
        (("--changed-only", "--base-ref", "--bump-version"), "changed-module automation"),
        (("--repair-stale-integrity", "--payload-from-filesystem"), "stale checksum repair"),
    ],
)
def test_sign_modules_py_help_mentions_expected_flags(
    expected_flags: tuple[str, ...],
    description: str,
) -> None:
    """sign-modules.py help SHALL document the supported automation flags."""
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")
    import subprocess

    result = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert result.returncode == 0
    for flag in expected_flags:
        assert flag in result.stdout, f"Missing {description} flag {flag!r}"


def test_sign_modules_py_changed_only_auto_bump_and_sign(tmp_path: Path):
    """Changed-only signing SHALL bump changed module version and add checksum metadata."""
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"

    source.parent.mkdir(parents=True)
    manifest.write_text(
        "name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n",
        encoding="utf-8",
    )
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    source.write_text("print('v2')\n", encoding="utf-8")

    result = subprocess.run(
        [
            "python3",
            str(SIGN_PYTHON_SCRIPT),
            "--allow-unsigned",
            "--changed-only",
            "--base-ref",
            "HEAD",
            "--bump-version",
            "patch",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr

    import yaml

    signed = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert signed["version"] == "0.1.1"
    assert signed.get("integrity", {}).get("checksum", "").startswith("sha256:")


def test_sign_modules_py_changed_only_fails_on_invalid_base_ref(tmp_path: Path):
    """Changed-only signing SHALL fail fast when --base-ref does not resolve."""
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"

    source.parent.mkdir(parents=True)
    manifest.write_text(
        "name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n",
        encoding="utf-8",
    )
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    result = subprocess.run(
        [
            "python3",
            str(SIGN_PYTHON_SCRIPT),
            "--allow-unsigned",
            "--changed-only",
            "--base-ref",
            "not-a-real-ref",
            "--bump-version",
            "patch",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert result.returncode != 0
    assert "--base-ref is invalid" in result.stderr


def _git_repo_with_committed_stale_checksum(tmp_path: Path) -> tuple[Path, Path, str]:
    """Build a repo whose HEAD has a wrong integrity.checksum vs payload; return (repo, manifest, bad_checksum)."""
    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"

    source.parent.mkdir(parents=True)
    manifest.write_text(
        "name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n",
        encoding="utf-8",
    )
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    signed = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert signed.returncode == 0, signed.stderr

    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    integrity = raw.get("integrity")
    assert isinstance(integrity, dict)
    checksum = str(integrity.get("checksum", ""))
    assert checksum.startswith("sha256:")
    parts = checksum.split(":", 1)
    assert len(parts) == 2
    bad_digest = "0" * len(parts[1])
    bad_checksum = f"{parts[0]}:{bad_digest}"
    integrity["checksum"] = bad_checksum
    raw["integrity"] = integrity
    manifest.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=False), encoding="utf-8")
    subprocess.run(["git", "add", str(manifest)], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "commit stale checksum"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return repo, manifest, bad_checksum


def test_sign_modules_py_repair_stale_integrity_fixes_checksum_without_git_diff(tmp_path: Path):
    """--repair-stale-integrity SHALL re-sign when checksum is wrong but git diff vs base is empty."""
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")

    repo, manifest, bad_checksum = _git_repo_with_committed_stale_checksum(tmp_path)

    changed_only = subprocess.run(
        [
            "python3",
            str(SIGN_PYTHON_SCRIPT),
            "--allow-unsigned",
            "--changed-only",
            "--base-ref",
            "HEAD",
            "--bump-version",
            "patch",
            "--payload-from-filesystem",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert changed_only.returncode == 0, changed_only.stderr
    combined_co = f"{changed_only.stdout}\n{changed_only.stderr}"
    assert "No module manifests to sign" in combined_co or "resolved empty" in combined_co

    repair = subprocess.run(
        [
            "python3",
            str(SIGN_PYTHON_SCRIPT),
            "--allow-unsigned",
            "--repair-stale-integrity",
            "--base-ref",
            "HEAD",
            "--bump-version",
            "patch",
            "--payload-from-filesystem",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert repair.returncode == 0, repair.stderr

    fixed = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert isinstance(fixed, dict)
    new_checksum = str(fixed.get("integrity", {}).get("checksum", ""))
    assert new_checksum.startswith("sha256:")
    assert new_checksum != bad_checksum


def test_sign_modules_py_repair_stale_integrity_requires_payload_from_filesystem(tmp_path: Path) -> None:
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")

    import subprocess

    repo = tmp_path / "repo"
    (repo / "modules").mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True
    )

    result = subprocess.run(
        [
            "python3",
            str(SIGN_PYTHON_SCRIPT),
            "--allow-unsigned",
            "--repair-stale-integrity",
            "--base-ref",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert result.returncode != 0
    assert "--repair-stale-integrity requires --payload-from-filesystem" in result.stderr


def test_sign_modules_py_checksum_changes_when_module_files_change(tmp_path: Path):
    """Checksum SHALL reflect full module payload, not only manifest metadata."""
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")
    module_dir = tmp_path / "sample-module"
    module_dir.mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    source.parent.mkdir(parents=True)
    manifest.write_text("name: sample\nversion: 0.1.0\ncommands: [sample]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")
    import subprocess

    import yaml

    first = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert first.returncode == 0
    first_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    first_checksum = first_data.get("integrity", {}).get("checksum")
    assert isinstance(first_checksum, str) and first_checksum.startswith("sha256:")

    source.write_text("print('v2')\n", encoding="utf-8")
    second = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert second.returncode == 0
    second_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    second_checksum = second_data.get("integrity", {}).get("checksum")
    assert isinstance(second_checksum, str) and second_checksum.startswith("sha256:")
    assert second_checksum != first_checksum


def test_sign_modules_py_ignores_transient_cache_files(tmp_path: Path):
    """Checksum SHALL ignore generated cache files such as __pycache__/*.pyc."""
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")
    module_dir = tmp_path / "sample-module"
    module_dir.mkdir(parents=True)
    manifest = module_dir / "module-package.yaml"
    source = module_dir / "src" / "main.py"
    source.parent.mkdir(parents=True)
    manifest.write_text("name: sample\nversion: 0.1.0\ncommands: [sample]\n", encoding="utf-8")
    source.write_text("print('stable')\n", encoding="utf-8")

    import subprocess

    import yaml

    first = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert first.returncode == 0
    first_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    first_checksum = first_data.get("integrity", {}).get("checksum")
    assert isinstance(first_checksum, str) and first_checksum.startswith("sha256:")

    cache_dir = module_dir / "src" / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "main.cpython-312.pyc").write_bytes(b"\x00\x01cache")

    second = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert second.returncode == 0
    second_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    second_checksum = second_data.get("integrity", {}).get("checksum")
    assert isinstance(second_checksum, str) and second_checksum.startswith("sha256:")
    assert second_checksum == first_checksum

    logs_dir = module_dir / "logs" / "tests" / "junit"
    logs_dir.mkdir(parents=True)
    (logs_dir / "test-results.xml").write_text("<testsuite name='tmp'/>", encoding="utf-8")

    third = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert third.returncode == 0
    third_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    third_checksum = third_data.get("integrity", {}).get("checksum")
    assert isinstance(third_checksum, str) and third_checksum.startswith("sha256:")
    assert third_checksum == second_checksum


def test_sign_modules_workflow_exists():
    """CI workflow .github/workflows/sign-modules.yml SHALL exist."""
    assert SIGN_WORKFLOW.exists(), "sign-modules.yml workflow must exist"


def test_sign_modules_workflow_valid_yaml():
    """Sign-modules workflow file SHALL be valid YAML."""
    if not SIGN_WORKFLOW.exists():
        pytest.skip("workflow not present")
    import yaml

    data = yaml.safe_load(SIGN_WORKFLOW.read_text(encoding="utf-8"))
    assert data is not None
    assert isinstance(data, dict)


def _sign_modules_on_block(workflow_root: dict[str, Any]) -> dict[str, Any]:
    on_block = workflow_root.get("on")
    if on_block is None:
        on_block = cast(dict[object, Any], workflow_root).get(True)
    assert isinstance(on_block, dict), "sign-modules workflow must define on: mappings"
    return cast(dict[str, Any], on_block)


def _assert_workflow_dispatch_inputs(on_block: dict[str, Any]) -> None:
    dispatch = on_block.get("workflow_dispatch")
    assert isinstance(dispatch, dict), "workflow_dispatch must be configured with inputs"
    inputs = dispatch.get("inputs")
    assert isinstance(inputs, dict)
    assert "base_branch" in inputs
    assert "version_bump" in inputs
    assert "resign_all_manifests" in inputs


def _assert_sign_and_push_job(workflow_root: dict[str, Any]) -> None:
    jobs = workflow_root.get("jobs")
    assert isinstance(jobs, dict)
    sign_push = jobs.get("sign-and-push")
    assert isinstance(sign_push, dict)
    assert sign_push.get("if") == "github.event_name == 'workflow_dispatch'"
    assert sign_push.get("needs") == ["verify"]
    perms = sign_push.get("permissions")
    assert isinstance(perms, dict) and perms.get("contents") == "write"


def _assert_sign_modules_dispatch_inputs_and_triggers(raw: str) -> None:
    assert "github.event.inputs.base_branch" in raw
    assert "github.event.inputs.version_bump" in raw
    assert "github.event.inputs.resign_all_manifests" in raw
    assert "Fetch workflow_dispatch comparison base" in raw
    assert 'elif [ "${{ github.event_name }}" = "workflow_dispatch" ]; then' in raw


def _assert_sign_modules_dispatch_signing_and_merge_base(raw: str) -> None:
    assert "--changed-only" in raw
    assert "--repair-stale-integrity" in raw
    assert "chore(modules): manual workflow_dispatch sign changed modules" in raw
    assert "git merge-base" in raw
    assert "merge-base" in raw
    assert '--base-ref "$MERGE_BASE"' in raw
    assert '--base-ref "${BASE_REF}"' not in raw


def _assert_sign_modules_dispatch_raw_content(raw: str) -> None:
    _assert_sign_modules_dispatch_inputs_and_triggers(raw)
    _assert_sign_modules_dispatch_signing_and_merge_base(raw)


def test_sign_modules_workflow_dispatch_signs_changed_modules_and_pushes():
    """Manual workflow_dispatch SHALL offer base/bump inputs and a sign-and-push job."""
    if not SIGN_WORKFLOW.exists():
        pytest.skip("workflow not present")
    data = yaml.safe_load(SIGN_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    workflow_root = cast(dict[str, Any], data)
    on_block = _sign_modules_on_block(workflow_root)
    _assert_workflow_dispatch_inputs(on_block)
    _assert_sign_and_push_job(workflow_root)
    _assert_sign_modules_dispatch_raw_content(SIGN_WORKFLOW.read_text(encoding="utf-8"))


def test_sign_modules_workflow_dispatch_resign_all_skips_version_check_base() -> None:
    """workflow_dispatch resign-all mode should verify in relaxed mode without base version checks."""
    raw = SIGN_WORKFLOW.read_text(encoding="utf-8")
    assert "github.event.inputs.resign_all_manifests" in raw
    assert "RESIGN_ARGS" in raw
    assert 'python scripts/verify-modules-signature.py "${RESIGN_ARGS[@]}"' in raw
    assert 'python scripts/verify-modules-signature.py "${VERIFY_ARGS[@]}" --version-check-base "$BASE_REF"' in raw
    match = re.search(
        r"inputs\.resign_all_manifests[^;]*\]; then(?P<body>.*?)^\s+else\s*$",
        raw,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, "Expected resign-all arm in sign-modules verify step"
    resign_body = match.group("body")
    assert 'verify-modules-signature.py "${VERIFY_ARGS[@]}" --version-check-base' not in resign_body, (
        "resign-all verify must not run the VERIFY_ARGS+--version-check-base invocation"
    )
    assert 'verify-modules-signature.py "${RESIGN_ARGS[@]}"' in resign_body


def test_sign_modules_workflow_pr_verify_is_relaxed_without_version_bump_check() -> None:
    """PR verification should still compare version bumps against the PR base."""
    raw = SIGN_WORKFLOW.read_text(encoding="utf-8")
    assert 'python scripts/verify-modules-signature.py "${VERIFY_ARGS[@]}" --version-check-base "$BASE_REF"' in raw


def test_sign_modules_reproducibility_runs_only_on_main_push():
    """Re-sign diff check runs on main push only (dev matches lenient verify; PRs unsigned OK)."""
    assert SIGN_WORKFLOW.is_file(), "sign-modules.yml workflow must exist"
    data = yaml.safe_load(SIGN_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    workflow_root = cast(dict[str, Any], data)
    jobs = workflow_root.get("jobs")
    assert isinstance(jobs, dict)
    reproducibility = jobs.get("reproducibility")
    assert isinstance(reproducibility, dict), "Expected reproducibility job in sign-modules workflow"
    assert reproducibility.get("name") == "Assert signing reproducibility"
    repro_if = reproducibility.get("if")
    assert isinstance(repro_if, str)
    assert "github.event_name == 'push'" in repro_if
    assert "github.ref_name == 'main'" in repro_if
    assert "needs.verify.outputs.signing_pr_created != 'true'" in repro_if


def test_verify_script_reports_version_bump_failure_even_when_checksum_fails(tmp_path: Path):
    """Verifier SHALL report version-bump failures independently of checksum/signature failures."""
    if not VERIFY_PYTHON_SCRIPT.exists() or not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("verification/signing scripts not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"
    source.parent.mkdir(parents=True)
    manifest.write_text("name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)

    # Create baseline integrity metadata and commit.
    signed = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert signed.returncode == 0, signed.stderr
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    # Commit payload change without version bump/re-signing -> checksum mismatch + missing bump.
    source.write_text("print('v2')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "change without version bump"], cwd=repo, check=True, capture_output=True, text=True
    )

    result = subprocess.run(
        [
            "python3",
            str(VERIFY_PYTHON_SCRIPT),
            "--enforce-version-bump",
            "--version-check-base",
            "HEAD~1",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}"
    assert "checksum mismatch" in combined
    assert "module version was not incremented" in combined


def test_verify_skip_checksum_still_reports_version_bump_failure(tmp_path: Path) -> None:
    """With --skip-checksum-verification, stale checksum must not mask a missing version bump."""
    if not VERIFY_PYTHON_SCRIPT.exists() or not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("verification/signing scripts not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"
    source.parent.mkdir(parents=True)
    manifest.write_text("name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)

    signed = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert signed.returncode == 0, signed.stderr
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    source.write_text("print('v2')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "change without version bump"], cwd=repo, check=True, capture_output=True, text=True
    )

    result = subprocess.run(
        [
            "python3",
            str(VERIFY_PYTHON_SCRIPT),
            "--enforce-version-bump",
            "--skip-checksum-verification",
            "--version-check-base",
            "HEAD~1",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}"
    assert "checksum mismatch" not in combined
    assert "module version was not incremented" in combined


def test_verify_skip_checksum_passes_when_version_bumped_without_resign(tmp_path: Path) -> None:
    """Non-main local policy: version bump may precede CI re-sign; skip checksum must allow that."""
    if not VERIFY_PYTHON_SCRIPT.exists() or not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("verification/signing scripts not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"
    source.parent.mkdir(parents=True)
    manifest.write_text("name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)

    signed = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert signed.returncode == 0, signed.stderr
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    source.write_text("print('v2')\n", encoding="utf-8")
    bumped = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert isinstance(bumped, dict)
    bumped["version"] = "0.1.1"
    manifest.write_text(
        yaml.safe_dump(bumped, sort_keys=True, allow_unicode=False),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "bump without local re-sign"], cwd=repo, check=True, capture_output=True, text=True
    )

    strict = subprocess.run(
        ["python3", str(VERIFY_PYTHON_SCRIPT), "--version-check-base", "HEAD~1"],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert strict.returncode != 0
    assert "checksum mismatch" in f"{strict.stdout}\n{strict.stderr}"

    relaxed = subprocess.run(
        [
            "python3",
            str(VERIFY_PYTHON_SCRIPT),
            "--skip-checksum-verification",
            "--enforce-version-bump",
            "--version-check-base",
            "HEAD~1",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert relaxed.returncode == 0, (relaxed.stdout, relaxed.stderr)


def test_verify_skip_checksum_passes_without_enforced_version_bump(tmp_path: Path) -> None:
    """Skip-checksum alone should allow changed payloads when version enforcement is not requested."""
    if not VERIFY_PYTHON_SCRIPT.exists() or not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("verification/signing scripts not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"
    source.parent.mkdir(parents=True)
    manifest.write_text("name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)

    signed = subprocess.run(
        ["python3", str(SIGN_PYTHON_SCRIPT), "--allow-unsigned", str(manifest)],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert signed.returncode == 0, signed.stderr
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    source.write_text("print('v2')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "change without version bump"], cwd=repo, check=True, capture_output=True, text=True
    )

    relaxed = subprocess.run(
        [
            "python3",
            str(VERIFY_PYTHON_SCRIPT),
            "--skip-checksum-verification",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert relaxed.returncode == 0, (relaxed.stdout, relaxed.stderr)


def test_verify_skip_checksum_accepts_unsigned_manifest(tmp_path: Path) -> None:
    """Relaxed verification should allow unsigned manifests when checksum verification is skipped."""
    if not VERIFY_PYTHON_SCRIPT.exists():
        pytest.skip("verification script not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    manifest = module_dir / "module-package.yaml"
    module_dir.mkdir(parents=True)
    manifest.write_text(
        "name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n"
        "integrity:\n"
        "  checksum: sha256:0000000000000000000000000000000000000000000000000000000000000000\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(VERIFY_PYTHON_SCRIPT), "--skip-checksum-verification"],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)


def test_verify_modules_signature_rejects_skip_with_require_signature() -> None:
    """--require-signature must remain strict; skip-checksum is for local omit policy only."""
    if not VERIFY_PYTHON_SCRIPT.exists():
        pytest.skip("verification script not present")

    import subprocess

    result = subprocess.run(
        [
            "python3",
            str(VERIFY_PYTHON_SCRIPT),
            "--require-signature",
            "--skip-checksum-verification",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=20,
    )
    assert result.returncode == 2
    combined = f"{result.stdout}\n{result.stderr}"
    assert "cannot be used with --require-signature" in combined


def test_pr_orchestrator_contains_verify_module_signatures_job():
    """PR orchestrator SHALL include bundled module verification (PR = relaxed checksum; push = payload verify)."""
    if not PR_ORCHESTRATOR_WORKFLOW.exists():
        pytest.skip("pr-orchestrator workflow not present")
    content = PR_ORCHESTRATOR_WORKFLOW.read_text(encoding="utf-8")
    assert "verify-module-signatures" in content
    assert "verify-modules-signature.py" in content
    assert "module-verify-policy.sh" in content
    assert "VERIFY_MODULES_PR" in content
    assert "VERIFY_MODULES_PUSH_ORCHESTRATOR" in content
    assert "--require-signature" not in content
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY" in content
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" in content
    assert re.search(
        r"verify-module-signatures:.*?uses: actions/checkout@v4.*?fetch-depth: 0",
        content,
        re.DOTALL,
    )


def test_pr_orchestrator_does_not_require_signatures_on_pr_heads() -> None:
    """PR orchestrator SHALL NOT pass --require-signature; CI auto-signs on dev/main after merge."""
    if not PR_ORCHESTRATOR_WORKFLOW.exists():
        pytest.skip("pr-orchestrator workflow not present")
    content = PR_ORCHESTRATOR_WORKFLOW.read_text(encoding="utf-8")
    assert "verify-modules-signature.py" in content
    assert "--require-signature" not in content


def test_sign_modules_workflow_uses_private_key_and_passphrase_secrets():
    """sign-modules workflow SHALL use encrypted-key secret and passphrase secret."""
    if not SIGN_WORKFLOW.exists():
        pytest.skip("workflow not present")
    content = SIGN_WORKFLOW.read_text(encoding="utf-8")
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY" in content
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" in content
    assert "Auto-sign changed bundled modules" in content
    assert "module-verify-policy.sh" in content
    assert "VERIFY_MODULES_STRICT" in content
    assert "VERIFY_MODULES_PR" in content


def test_module_verify_policy_pr_bundle_skips_version_bump() -> None:
    """PR verification bundle should still enforce version bumps while deferring checksum/signature validation."""
    content = (REPO_ROOT / "scripts" / "module-verify-policy.sh").read_text(encoding="utf-8")
    assert "VERIFY_MODULES_PR=(--enforce-version-bump --skip-checksum-verification)" in content


def test_sign_modules_py_can_auto_bump_explicit_manifest_without_signing(tmp_path: Path) -> None:
    """Version-only remediation should patch-bump changed modules before non-main verification."""
    if not SIGN_PYTHON_SCRIPT.exists():
        pytest.skip("sign-modules.py not present")

    import subprocess

    repo = tmp_path / "repo"
    module_dir = repo / "modules" / "sample"
    source = module_dir / "src" / "sample" / "main.py"
    manifest = module_dir / "module-package.yaml"
    source.parent.mkdir(parents=True)
    manifest.write_text("name: sample\nversion: 0.1.0\npublisher: nold-ai\ncommands: [sample]\n", encoding="utf-8")
    source.write_text("print('v1')\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)

    source.write_text("print('v2')\n", encoding="utf-8")

    result = subprocess.run(
        [
            "python3",
            str(SIGN_PYTHON_SCRIPT),
            "--version-only",
            "--bump-version",
            "patch",
            "--base-ref",
            "HEAD",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=20,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    manifest_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert isinstance(manifest_data, dict)
    assert manifest_data["version"] == "0.1.1"
    assert "integrity" not in manifest_data


def test_pre_commit_verify_modules_omit_policy_auto_bumps_versions() -> None:
    """Non-main pre-commit verification should auto-bump changed module manifests before verifying."""
    content = (REPO_ROOT / "scripts" / "pre-commit-verify-modules.sh").read_text(encoding="utf-8")
    assert "sign-modules.py" in content
    assert "--version-only" in content
    assert "--bump-version patch" in content
    assert "exec hatch run verify-modules-signature-pr" in content


def test_pr_orchestrator_pins_virtualenv_below_21_for_hatch_jobs():
    """PR orchestrator SHALL pin virtualenv<21 when installing hatch in CI jobs."""
    if not PR_ORCHESTRATOR_WORKFLOW.exists():
        pytest.skip("pr-orchestrator workflow not present")
    content = PR_ORCHESTRATOR_WORKFLOW.read_text(encoding="utf-8")
    install_commands = re.findall(r"pip install[^\n]*hatch[^\n]*", content)
    assert install_commands, "Expected at least one pip install hatch command in workflow"
    for command in install_commands:
        assert "virtualenv<21" in command, f"Missing virtualenv<21 pin in command: {command}"


@pytest.mark.parametrize(
    ("job_name", "required_needs"),
    (
        ("compat-py311", {"changes", "verify-module-signatures"}),
        ("contract-first-ci", {"changes", "verify-module-signatures"}),
        ("type-checking", {"changes", "verify-module-signatures"}),
        ("linting", {"changes", "verify-module-signatures"}),
        ("cli-validation", {"changes", "verify-module-signatures"}),
    ),
)
def test_pr_orchestrator_independent_jobs_do_not_wait_for_tests(
    job_name: str,
    required_needs: set[str],
) -> None:
    """Independent validation jobs SHALL start after the shared signature gate, not after tests."""
    jobs = _load_pr_orchestrator_jobs()
    job = jobs.get(job_name)
    assert job is not None, f"Missing {job_name} job"
    needs = job.get("needs")
    assert isinstance(needs, list), f"Expected list needs for {job_name}"
    assert set(needs) == required_needs
    assert "tests" not in needs


def test_pr_orchestrator_quality_gates_still_depends_on_tests_for_coverage() -> None:
    """Coverage-based advisory gate SHALL retain the tests dependency."""
    jobs = _load_pr_orchestrator_jobs()
    job = jobs.get("quality-gates")
    assert job is not None, "Missing quality-gates job"
    needs = job.get("needs")
    assert isinstance(needs, list), "Expected list needs for quality-gates"
    assert set(needs) == {"changes", "tests"}


def test_pr_orchestrator_cache_paths_do_not_restore_hatch_virtualenvs() -> None:
    """PR orchestrator SHALL cache package downloads, not Hatch virtualenv directories."""
    content = _read_text_or_skip(PR_ORCHESTRATOR_WORKFLOW, reason="pr-orchestrator workflow not present")
    assert "~/.cache/uv" in content
    assert "~/.local/share/hatch" not in content


def test_publish_script_pins_virtualenv_below_21_for_hatch_build():
    """PyPI publish script SHALL pin virtualenv<21 when installing hatch."""
    content = _read_text_or_skip(PUBLISH_PYPI_SCRIPT, reason="check-and-publish-pypi.sh not present")
    install_commands = re.findall(r"python -m pip install[^\n]*hatch[^\n]*", content)
    assert install_commands, "Expected hatch install command in check-and-publish-pypi.sh"
    for command in install_commands:
        assert "virtualenv<21" in command, f"Missing virtualenv<21 pin in command: {command}"
