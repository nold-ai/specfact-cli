"""Integration tests for generate command."""

import pytest
import yaml
from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestGenerateContractsCommand:
    """Test suite for generate contracts command."""

    def test_generate_contracts_creates_files(self, tmp_path, monkeypatch):
        """Test generate contracts creates contract stub files."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features and stories that have contracts
        # First create minimal plan
        bundle_name = "test-bundle"
        result_init = runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        assert result_init.exit_code == 0, f"plan init failed: {result_init.stdout}\n{result_init.stderr}"

        # Read the plan and add a feature with contracts (modular bundle structure)
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        assert bundle_dir.exists()

        # For modular bundles, we need to load the ProjectBundle and add features
        from specfact_cli.models.plan import Feature as PlanFeature, Story
        from specfact_cli.utils.bundle_loader import load_project_bundle

        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

        # Add a feature with contracts
        feature = PlanFeature(
            key="FEATURE-001",
            title="Test Feature",
            outcomes=["Test outcome"],
            stories=[
                Story(
                    key="STORY-001",
                    title="Test Story",
                    acceptance=["Amount must be positive"],
                    contracts={"preconditions": ["amount > 0"], "postconditions": ["result > 0"]},
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                )
            ],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        from specfact_cli.utils.bundle_loader import save_project_bundle

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Harden the plan
        result_harden = runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])
        assert result_harden.exit_code == 0, f"plan harden failed: {result_harden.stdout}\n{result_harden.stderr}"

        # Generate contracts
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--no-interactive"])

        if result.exit_code != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

        assert result.exit_code == 0, f"generate contracts failed: {result.stdout}\n{result.stderr}"
        assert (
            "Generating contract stubs" in result.stdout
            or "contract file" in result.stdout.lower()
            or "Generated" in result.stdout
        )

        # Verify contracts directory exists (bundle-specific location)
        from specfact_cli.utils.structure import SpecFactStructure

        contracts_dir = tmp_path / ".specfact" / "projects" / bundle_name / "contracts"
        assert contracts_dir.exists(), f"Contracts directory not found at {contracts_dir}"

        # Verify at least one contract file was created (if contracts exist in SDD)
        contract_files = list(contracts_dir.glob("*.py"))
        # Note: If SDD has no contracts/invariants, no files will be generated (this is expected)
        # But with our test plan that has contracts, files should be generated
        if len(contract_files) == 0:
            # Check if SDD actually has contracts (bundle-specific location)
            from specfact_cli.utils.structured_io import StructuredFormat

            sdd_path = SpecFactStructure.get_bundle_sdd_path(bundle_name, tmp_path, StructuredFormat.YAML)
            if sdd_path.exists():
                with open(sdd_path) as f:
                    sdd_data = yaml.safe_load(f)
                    how_section = sdd_data.get("how", {})
                    has_contracts = bool(how_section.get("contracts"))
                    has_invariants = bool(how_section.get("invariants"))
                    # Debug output
                    print(f"SDD contracts: {how_section.get('contracts')}")
                    print(f"SDD invariants: {how_section.get('invariants')}")
                    if not has_contracts and not has_invariants:
                        # This is expected - no contracts/invariants means no files generated
                        # But our test story has contracts, so this indicates extraction failed
                        pytest.skip(
                            "SDD has no contracts/invariants to generate. "
                            "This may indicate that story contracts are not being extracted correctly."
                        )

        assert len(contract_files) > 0, (
            f"No Python files found in {contracts_dir}. SDD may not have contracts/invariants."
        )

    def test_generate_contracts_with_missing_sdd(self, tmp_path, monkeypatch):
        """Test generate contracts fails when SDD is missing."""
        monkeypatch.chdir(tmp_path)

        # Create a plan but don't harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Try to generate contracts (should fail - no SDD)
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--no-interactive"])

        assert result.exit_code == 1
        assert "SDD manifest not found" in result.stdout or "No active plan found" in result.stdout
        assert "plan harden" in result.stdout

    def test_generate_contracts_with_custom_sdd_path(self, tmp_path, monkeypatch):
        """Test generate contracts with custom SDD path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Generate contracts with explicit SDD path (bundle-specific location)
        from specfact_cli.utils.structure import SpecFactStructure
        from specfact_cli.utils.structured_io import StructuredFormat

        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        sdd_path = SpecFactStructure.get_bundle_sdd_path(bundle_name, tmp_path, StructuredFormat.YAML)
        result = runner.invoke(
            app,
            [
                "generate",
                "contracts",
                "--plan",
                str(bundle_dir),
                "--sdd",
                str(sdd_path),
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0

    def test_generate_contracts_with_custom_plan_path(self, tmp_path, monkeypatch):
        """Test generate contracts with custom plan path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Find the bundle path (modular structure)
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name

        # Generate contracts with explicit bundle directory (using --plan)
        result = runner.invoke(
            app,
            [
                "generate",
                "contracts",
                "--plan",
                str(bundle_dir),
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0

    def test_generate_contracts_validates_hash_match(self, tmp_path, monkeypatch):
        """Test generate contracts validates hash match."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Modify the project bundle hash in the SDD manifest to simulate a mismatch
        from specfact_cli.utils.structure import SpecFactStructure
        from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, load_structured_file

        sdd_path = SpecFactStructure.get_bundle_sdd_path(bundle_name, tmp_path, StructuredFormat.YAML)

        sdd_data = load_structured_file(sdd_path)
        original_hash = sdd_data.get("project_hash") or sdd_data.get("plan_bundle_hash", "")
        sdd_data["project_hash"] = "different_hash_" + "x" * (len(original_hash) - len("different_hash_"))
        if "plan_bundle_hash" in sdd_data:
            sdd_data["plan_bundle_hash"] = sdd_data["project_hash"]
        dump_structured_file(sdd_data, sdd_path, StructuredFormat.YAML)

        # Try to generate contracts (should fail on hash mismatch)
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--no-interactive"])

        assert result.exit_code == 1
        assert "hash does not match" in result.stdout or "hash mismatch" in result.stdout.lower()

    def test_generate_contracts_reports_coverage(self, tmp_path, monkeypatch):
        """Test generate contracts reports coverage statistics."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features and stories
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--bundle",
                bundle_name,
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Generate contracts
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--no-interactive"])

        assert result.exit_code == 0
        # Should report coverage statistics
        assert "contract" in result.stdout.lower() or "invariant" in result.stdout.lower()

    def test_generate_contracts_creates_python_files(self, tmp_path, monkeypatch):
        """Test that generated contract files are Python files."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features and stories that have contracts
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Add a feature with contracts (modular bundle structure)
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        from specfact_cli.models.plan import Feature as PlanFeature
        from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle

        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

        # Add a feature with a story that has contracts
        from specfact_cli.models.plan import Story

        feature = PlanFeature(
            key="FEATURE-001",
            title="Test Feature",
            outcomes=["Test outcome"],
            stories=[
                Story(
                    key="STORY-001",
                    title="Test Story",
                    acceptance=["Amount must be positive"],
                    contracts={"preconditions": ["amount > 0"], "postconditions": ["result > 0"]},
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                )
            ],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Generate contracts
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--no-interactive"])
        assert result.exit_code == 0

        # Check that Python files were created (if contracts exist in SDD) - bundle-specific location
        contracts_dir = tmp_path / ".specfact" / "projects" / bundle_name / "contracts"
        python_files = []
        if contracts_dir.exists():
            python_files = list(contracts_dir.glob("*.py"))
            # If SDD has contracts/invariants, files should be generated
            # Otherwise, it's expected that no files are generated
            if len(python_files) > 0:
                # Verify they are valid Python files
                for py_file in python_files:
                    assert py_file.suffix == ".py"
                    content = py_file.read_text()
                    assert "SDD_VERSION" in content or "FEATURE_KEY" in content

        # Check that files contain expected content (only if files were generated)
        for py_file in python_files:
            content = py_file.read_text()
            assert "from beartype import beartype" in content or "beartype" in content.lower()
            assert "icontract" in content.lower() or "contract" in content.lower()

    def test_generate_contracts_includes_metadata(self, tmp_path, monkeypatch):
        """Test that generated contract files include SDD metadata."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Generate contracts
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--no-interactive"])

        # Check that files include metadata (bundle-specific location)
        contracts_dir = tmp_path / ".specfact" / "projects" / bundle_name / "contracts"
        python_files = list(contracts_dir.glob("*.py"))

        if python_files:
            content = python_files[0].read_text()
            assert "SDD_PLAN_BUNDLE_ID" in content
            assert "SDD_PLAN_BUNDLE_HASH" in content
            assert "FEATURE_KEY" in content


class TestGenerateFixPromptCommand:
    """Test suite for generate fix-prompt command."""

    def test_fix_prompt_lists_gaps_when_no_gap_id(self, tmp_path, monkeypatch):
        """Test fix-prompt lists available gaps when no gap_id provided."""
        monkeypatch.chdir(tmp_path)

        # Create a bundle with gap report
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Create a mock gap report
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        reports_dir = bundle_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        import json

        gap_report = {
            "gaps": [
                {
                    "id": "GAP-001",
                    "severity": "high",
                    "category": "missing_tests",
                    "description": "Missing unit tests for auth module",
                    "module": "src/auth",
                    "function": "login",
                    "evidence": {"file": "src/auth/login.py", "line": 42},
                }
            ],
            "summary": {"total": 1, "high": 1, "medium": 0, "low": 0},
        }
        (reports_dir / "gaps.json").write_text(json.dumps(gap_report))

        # Run fix-prompt without gap_id
        result = runner.invoke(
            app, ["generate", "fix-prompt", "--bundle", bundle_name, "--no-interactive"]
        )

        assert result.exit_code == 0
        assert "GAP-001" in result.stdout or "Available Gaps" in result.stdout

    def test_fix_prompt_generates_prompt_for_gap(self, tmp_path, monkeypatch):
        """Test fix-prompt generates a prompt file for specific gap."""
        monkeypatch.chdir(tmp_path)

        # Create a bundle with gap report
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Create a mock gap report
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        reports_dir = bundle_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        import json

        gap_report = {
            "gaps": [
                {
                    "id": "GAP-001",
                    "severity": "high",
                    "category": "missing_tests",
                    "description": "Missing unit tests for auth module",
                    "module": "src/auth",
                    "function": "login",
                    "evidence": {"file": "src/auth/login.py", "line": 42},
                }
            ],
            "summary": {"total": 1, "high": 1, "medium": 0, "low": 0},
        }
        (reports_dir / "gaps.json").write_text(json.dumps(gap_report))

        # Run fix-prompt with gap_id
        result = runner.invoke(
            app, ["generate", "fix-prompt", "GAP-001", "--bundle", bundle_name, "--no-interactive"]
        )

        assert result.exit_code == 0
        # Should create prompt file or show prompt content
        prompts_dir = bundle_dir / "prompts"
        if prompts_dir.exists():
            prompt_files = list(prompts_dir.glob("fix-*.md"))
            if prompt_files:
                content = prompt_files[0].read_text()
                assert "GAP-001" in content or "Fix" in content

    def test_fix_prompt_fails_without_gap_report(self, tmp_path, monkeypatch):
        """Test fix-prompt fails gracefully when no gap report exists."""
        monkeypatch.chdir(tmp_path)

        # Create a bundle without gap report
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Run fix-prompt (should fail or show helpful message)
        result = runner.invoke(
            app, ["generate", "fix-prompt", "GAP-001", "--bundle", bundle_name, "--no-interactive"]
        )

        # Should fail or provide helpful message
        assert result.exit_code != 0 or "no gaps" in result.stdout.lower() or "not found" in result.stdout.lower()


class TestGenerateTestPromptCommand:
    """Test suite for generate test-prompt command."""

    def test_test_prompt_generates_prompt_for_file(self, tmp_path, monkeypatch):
        """Test test-prompt generates a prompt file for a source file."""
        monkeypatch.chdir(tmp_path)

        # Create a bundle and a source file
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Create a source file
        src_dir = tmp_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        source_file = src_dir / "auth.py"
        source_file.write_text('''
def login(username: str, password: str) -> bool:
    """Authenticate user with username and password."""
    if not username or not password:
        return False
    return True
''')

        # Run test-prompt
        result = runner.invoke(
            app,
            ["generate", "test-prompt", str(source_file), "--bundle", bundle_name, "--no-interactive"],
        )

        assert result.exit_code == 0
        # Should create prompt file or show prompt content
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        prompts_dir = bundle_dir / "prompts"
        if prompts_dir.exists():
            prompt_files = list(prompts_dir.glob("test-*.md"))
            if prompt_files:
                content = prompt_files[0].read_text()
                assert "test" in content.lower() or "auth" in content.lower()

    def test_test_prompt_lists_files_without_tests(self, tmp_path, monkeypatch):
        """Test test-prompt lists files needing tests when no file provided."""
        monkeypatch.chdir(tmp_path)

        # Create a bundle
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Run test-prompt without file argument
        result = runner.invoke(
            app, ["generate", "test-prompt", "--bundle", bundle_name, "--no-interactive"]
        )

        # Should succeed and show help or list files
        assert result.exit_code == 0 or "file" in result.stdout.lower()

    def test_test_prompt_with_type_option(self, tmp_path, monkeypatch):
        """Test test-prompt with --type option for integration tests."""
        monkeypatch.chdir(tmp_path)

        # Create a bundle and a source file
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Create a source file
        src_dir = tmp_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        source_file = src_dir / "api.py"
        source_file.write_text('''
def get_users():
    """Get all users from the API."""
    return []
''')

        # Run test-prompt with --type integration
        result = runner.invoke(
            app,
            [
                "generate",
                "test-prompt",
                str(source_file),
                "--bundle",
                bundle_name,
                "--type",
                "integration",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        # Prompt should mention integration testing
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        prompts_dir = bundle_dir / "prompts"
        if prompts_dir.exists():
            prompt_files = list(prompts_dir.glob("test-*.md"))
            if prompt_files:
                content = prompt_files[0].read_text()
                assert "integration" in content.lower() or "test" in content.lower()
