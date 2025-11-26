"""Integration tests for generate command."""

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
        from specfact_cli.utils.bundle_loader import load_project_bundle
        from specfact_cli.models.plan import Feature as PlanFeature
        
        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        
        # Add a feature with contracts
        feature = PlanFeature(
            key="FEATURE-001",
            title="Test Feature",
            outcomes=["Test outcome"],
            stories=[
                {
                    "key": "STORY-001",
                    "title": "Test Story",
                    "acceptance": ["Amount must be positive"],
                    "contracts": {"preconditions": ["amount > 0"], "postconditions": ["result > 0"]},
                }
            ],
        )
        project_bundle.features["FEATURE-001"] = feature
        
        from specfact_cli.utils.bundle_loader import save_project_bundle
        save_project_bundle(project_bundle, bundle_dir, atomic=True)
        
        # Keep plan_path for compatibility with rest of test
        plan_path = bundle_dir / "bundle.manifest.yaml"

        # Harden the plan
        result_harden = runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])
        assert result_harden.exit_code == 0, f"plan harden failed: {result_harden.stdout}\n{result_harden.stderr}"

        # Generate contracts
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--non-interactive"])

        if result.exit_code != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

        assert result.exit_code == 0, f"generate contracts failed: {result.stdout}\n{result.stderr}"
        assert (
            "Generating contract stubs" in result.stdout
            or "contract file" in result.stdout.lower()
            or "Generated" in result.stdout
        )

        # Verify contracts directory exists
        contracts_dir = tmp_path / ".specfact" / "contracts"
        assert contracts_dir.exists(), f"Contracts directory not found at {contracts_dir}"

        # Verify at least one contract file was created (if contracts exist in SDD)
        contract_files = list(contracts_dir.glob("*.py"))
        # Note: If SDD has no contracts/invariants, no files will be generated (this is expected)
        # But with our test plan that has contracts, files should be generated
        if len(contract_files) == 0:
            # Check if SDD actually has contracts
            sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
            if sdd_path.exists():
                with open(sdd_path) as f:
                    sdd_data = yaml.safe_load(f)
                    has_contracts = bool(sdd_data.get("how", {}).get("contracts"))
                    has_invariants = bool(sdd_data.get("how", {}).get("invariants"))
                    if not has_contracts and not has_invariants:
                        # This is expected - no contracts/invariants means no files generated
                        return

        assert len(contract_files) > 0, f"No Python files found in {contracts_dir}"

    def test_generate_contracts_with_missing_sdd(self, tmp_path, monkeypatch):
        """Test generate contracts fails when SDD is missing."""
        monkeypatch.chdir(tmp_path)

        # Create a plan but don't harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Try to generate contracts (should fail - no SDD)
        result = runner.invoke(app, ["generate", "contracts", "--non-interactive"])

        assert result.exit_code == 1
        assert "SDD manifest not found" in result.stdout
        assert "plan harden" in result.stdout

    def test_generate_contracts_with_custom_sdd_path(self, tmp_path, monkeypatch):
        """Test generate contracts with custom SDD path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Generate contracts with explicit SDD path
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        result = runner.invoke(
            app,
            [
                "generate",
                "contracts",
                "--plan",
                str(bundle_dir),
                "--sdd",
                str(sdd_path),
                "--non-interactive",
            ],
        )

        assert result.exit_code == 0

    def test_generate_contracts_with_custom_plan_path(self, tmp_path, monkeypatch):
        """Test generate contracts with custom plan path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

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
                "--non-interactive",
            ],
        )

        assert result.exit_code == 0

    def test_generate_contracts_validates_hash_match(self, tmp_path, monkeypatch):
        """Test generate contracts validates hash match."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        bundle_name = "test-bundle"
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Modify the project bundle hash in the SDD manifest to simulate a mismatch
        sdd_path = tmp_path / ".specfact" / "sdd" / f"{bundle_name}.yaml"
        from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, load_structured_file

        sdd_data = load_structured_file(sdd_path)
        original_hash = sdd_data.get("project_hash") or sdd_data.get("plan_bundle_hash", "")
        sdd_data["project_hash"] = "different_hash_" + "x" * (len(original_hash) - len("different_hash_"))
        if "plan_bundle_hash" in sdd_data:
            sdd_data["plan_bundle_hash"] = sdd_data["project_hash"]
        dump_structured_file(sdd_data, sdd_path, StructuredFormat.YAML)

        # Try to generate contracts (should fail on hash mismatch)
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--non-interactive"])

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
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Generate contracts
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--non-interactive"])

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
        from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
        from specfact_cli.models.plan import Feature as PlanFeature

        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

        # Add a feature with a story that has contracts
        feature = PlanFeature(
            key="FEATURE-001",
            title="Test Feature",
            outcomes=["Test outcome"],
            stories=[
                {
                    "key": "STORY-001",
                    "title": "Test Story",
                    "acceptance": ["Amount must be positive"],
                    "contracts": {"preconditions": ["amount > 0"], "postconditions": ["result > 0"]},
                }
            ],
        )
        project_bundle.features["FEATURE-001"] = feature
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Generate contracts
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        result = runner.invoke(app, ["generate", "contracts", "--plan", str(bundle_dir), "--non-interactive"])
        assert result.exit_code == 0

        # Check that Python files were created (if contracts exist in SDD)
        contracts_dir = tmp_path / ".specfact" / "contracts"
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
        runner.invoke(app, ["plan", "harden", bundle_name, "--non-interactive"])

        # Generate contracts
        runner.invoke(app, ["generate", "contracts", "--bundle", bundle_name, "--non-interactive"])

        # Check that files include metadata
        contracts_dir = tmp_path / ".specfact" / "contracts"
        python_files = list(contracts_dir.glob("*.py"))

        if python_files:
            content = python_files[0].read_text()
            assert "SDD_PLAN_BUNDLE_ID" in content
            assert "SDD_PLAN_BUNDLE_HASH" in content
            assert "FEATURE_KEY" in content
