"""
Tests for signing automation artifacts (arch-06): script and CI workflow.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
SIGN_SCRIPT = REPO_ROOT / "scripts" / "sign-module.sh"
SIGN_PYTHON_SCRIPT = REPO_ROOT / "scripts" / "sign-modules.py"
VERIFY_PYTHON_SCRIPT = REPO_ROOT / "scripts" / "verify-modules-signature.py"
SIGN_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sign-modules.yml"
PR_ORCHESTRATOR_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-orchestrator.yml"


def test_sign_module_script_exists():
    """Signing script scripts/sign-module.sh SHALL exist."""
    assert SIGN_SCRIPT.exists(), "scripts/sign-module.sh must exist for signing automation"


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


def test_sign_modules_py_help_mentions_passphrase_sources():
    """sign-modules.py help SHALL expose passphrase flag and stdin mode."""
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
    assert "--passphrase" in result.stdout
    assert "--passphrase-stdin" in result.stdout
    assert "--allow-same-version" in result.stdout


def test_sign_modules_py_help_mentions_changed_module_automation():
    """sign-modules.py help SHALL expose changed-module automation flags."""
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
    assert "--changed-only" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--bump-version" in result.stdout


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


def test_verify_modules_script_exists():
    """Verification script SHALL exist for CI signature validation."""
    assert VERIFY_PYTHON_SCRIPT.exists(), "scripts/verify-modules-signature.py must exist"


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


def test_pr_orchestrator_contains_verify_module_signatures_job():
    """PR orchestrator SHALL include module signature verification gate."""
    if not PR_ORCHESTRATOR_WORKFLOW.exists():
        pytest.skip("pr-orchestrator workflow not present")
    content = PR_ORCHESTRATOR_WORKFLOW.read_text(encoding="utf-8")
    assert "verify-module-signatures" in content
    assert "verify-modules-signature.py --require-signature" in content
    assert "--enforce-version-bump" in content
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY" in content
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" in content
    assert re.search(
        r"verify-module-signatures:.*?uses: actions/checkout@v4.*?fetch-depth: 0",
        content,
        re.DOTALL,
    )


def test_sign_modules_workflow_uses_private_key_and_passphrase_secrets():
    """sign-modules workflow SHALL use encrypted-key secret and passphrase secret."""
    if not SIGN_WORKFLOW.exists():
        pytest.skip("workflow not present")
    content = SIGN_WORKFLOW.read_text(encoding="utf-8")
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY" in content
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" in content
    assert "--enforce-version-bump" in content


def test_pr_orchestrator_pins_virtualenv_below_21_for_hatch_jobs():
    """PR orchestrator SHALL pin virtualenv<21 when installing hatch in CI jobs."""
    if not PR_ORCHESTRATOR_WORKFLOW.exists():
        pytest.skip("pr-orchestrator workflow not present")
    content = PR_ORCHESTRATOR_WORKFLOW.read_text(encoding="utf-8")
    install_commands = re.findall(r"pip install[^\n]*hatch[^\n]*", content)
    assert install_commands, "Expected at least one pip install hatch command in workflow"
    for command in install_commands:
        assert "virtualenv<21" in command, f"Missing virtualenv<21 pin in command: {command}"
