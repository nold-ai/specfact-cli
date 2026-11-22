"""Integration tests for Spec-Kit import with realistic repositories."""

import tempfile
from pathlib import Path
from textwrap import dedent
from typing import cast

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.importers.speckit_converter import SpecKitConverter
from specfact_cli.importers.speckit_scanner import SpecKitScanner
from specfact_cli.models.plan import PlanBundle
from specfact_cli.models.protocol import Protocol
from specfact_cli.utils.yaml_utils import load_yaml


runner = CliRunner()


USER_SERVICE_SPEC = dedent(
    """# Feature Specification: User Service

## User Scenarios & Testing

### User Story 1 - Create User (Priority: P1)
As a user, I want to create a user account so that I can access the system.

**Acceptance Scenarios**:
1. Given valid user data, When I create a user, Then the user is created successfully

### User Story 2 - Update User (Priority: P2)
As a user, I want to update my profile so that I can keep my information current.

**Acceptance Scenarios**:
1. Given I am logged in, When I update my profile, Then my profile is updated

### User Story 3 - Delete User (Priority: P3)
As an administrator, I want to delete user accounts so that I can manage the system.

**Acceptance Scenarios**:
1. Given I am an admin, When I delete a user, Then the user is removed from the system

## Functional Requirements

- FR-001: User creation must validate email format
- FR-002: User updates must preserve existing data
- FR-003: User deletion must remove all associated data

## Success Criteria

- SC-001: Users can create accounts with valid email addresses
- SC-002: Users can update their profiles successfully
- SC-003: Administrators can delete user accounts
"""
)

USER_SERVICE_PLAN = dedent(
    """# Implementation Plan: User Service

## Summary
User management service for account creation, updates, and deletion.

## Architecture
- Python 3.11+
- REST API with FastAPI
- PostgreSQL database
- Redis caching

## Phases
- Phase 1: Core user creation
- Phase 2: Profile updates
- Phase 3: Admin deletion
"""
)

PAYMENT_PROCESSOR_SPEC = dedent(
    """# Feature Specification: Payment Processor

## User Scenarios & Testing

### User Story 1 - Process Payment (Priority: P1)
As a user, I want to process payments so that I can complete transactions.

**Acceptance Scenarios**:
1. Given valid payment data, When I process a payment, Then the payment is processed successfully

### User Story 2 - Refund Payment (Priority: P2)
As a merchant, I want to refund payments so that I can handle customer returns.

**Acceptance Scenarios**:
1. Given a completed payment, When I initiate a refund, Then the refund is processed

## Functional Requirements

- FR-001: Payment processing must handle timeouts gracefully
- FR-002: Refunds must validate original transaction

## Success Criteria

- SC-001: Payments process within 5 seconds
- SC-002: Refunds complete successfully
"""
)

PAYMENT_PROCESSOR_PLAN = dedent(
    """# Implementation Plan: Payment Processor

## Summary
Payment processing service for transactions and refunds.

## Architecture
- Python 3.11+
- REST API
- External payment gateway integration
- Transaction logging

## Phases
- Phase 1: Payment processing
- Phase 2: Refund handling
"""
)


def _write_feature(specs_path: Path, name: str, spec_text: str, plan_text: str) -> None:
    feature_path = specs_path / name
    feature_path.mkdir()
    (feature_path / "spec.md").write_text(spec_text)
    (feature_path / "plan.md").write_text(plan_text)


def _write_constitution(specify_path: Path) -> None:
    # Create memory directory with constitution
    memory_path = specify_path / "memory"
    memory_path.mkdir()

    constitution_md = dedent(
        """# Project Constitution

## Core Principles

### Contract-First Development
All public APIs must have contracts defined before implementation.

### Quality Gates
- Test coverage ≥ 80%
- Contract coverage ≥ 80%
- All tests must pass before merging

## Constraints
- Python 3.11+ required
- No breaking API changes without versioning
"""
    )
    (memory_path / "constitution.md").write_text(constitution_md)


def _write_full_workflow_project(repo_path: Path) -> None:
    specify_path = repo_path / ".specify"
    specify_path.mkdir()

    specs_path = repo_path / "specs"
    specs_path.mkdir()

    feature_path = specs_path / "full-service"
    feature_path.mkdir()

    spec_md = dedent(
        """# Feature Specification: Full Service

## User Scenarios & Testing

### User Story 1 - Start Service (Priority: P1)
As a user, I want to start the service so that it becomes available.

**Acceptance Scenarios**:
1. Given the service is stopped, When I start it, Then it transitions to RUNNING

### User Story 2 - Stop Service (Priority: P2)
As a user, I want to stop the service so that it shuts down gracefully.

**Acceptance Scenarios**:
1. Given the service is running, When I stop it, Then it transitions to STOPPED

### User Story 3 - Handle Error (Priority: P3)
As a system, I want to handle errors so that the service can recover.

**Acceptance Scenarios**:
1. Given an error occurs, When it is handled, Then the service transitions to ERROR state
"""
    )
    (feature_path / "spec.md").write_text(spec_md)

    plan_md = dedent(
        """# Implementation Plan: Full Service

## Summary
Full service with all features including state management.

## Architecture
- Python 3.11+
- State machine
- Error handling
- Logging

## Phases
- Phase 1: Service lifecycle
- Phase 2: Error handling
- Phase 3: State management
"""
    )
    (feature_path / "plan.md").write_text(plan_md)

    memory_path = specify_path / "memory"
    memory_path.mkdir()
    (memory_path / "constitution.md").write_text(
        "# Project Constitution\n\n## Core Principles\n\nContract-First Development"
    )


def _imported_feature_key(bundle_dir: Path) -> str:
    features = load_yaml(bundle_dir / "bundle.manifest.yaml").get("features")
    if isinstance(features, list) and features:
        first = features[0]
        key = cast(dict[str, object], first).get("key") if isinstance(first, dict) else first
    elif isinstance(features, dict) and features:
        key = next(iter(features))
    else:
        feature_files = sorted((bundle_dir / "features").glob("*.yaml"))
        assert feature_files
        key = feature_files[0].stem
    assert isinstance(key, str), f"Expected feature key to be a string, got {key!r}"
    return key


def _assert_full_import_artifacts(repo_path: Path) -> None:
    protocol_path = repo_path / ".specfact" / "protocols" / "workflow.protocol.yaml"
    bundle_dir = repo_path / ".specfact" / "projects" / "main"
    required_artifacts = (
        protocol_path,
        bundle_dir / "bundle.manifest.yaml",
        repo_path / ".semgrep" / "async-anti-patterns.yml",
        repo_path / ".github" / "workflows" / "specfact-gate.yml",
    )
    for artifact in required_artifacts:
        assert artifact.is_file(), f"Missing generated artifact {artifact}"

    states = load_yaml(protocol_path)["states"]
    assert len(states) >= 3
    assert {"INIT", "COMPLETE"} <= set(states)

    feature_path = bundle_dir / "features" / f"{_imported_feature_key(bundle_dir)}.yaml"
    if feature_path.exists():
        feature_data = load_yaml(feature_path)
        assert feature_data["stories"]


def _assert_realistic_plan(plan_bundle: PlanBundle) -> None:
    assert isinstance(plan_bundle, PlanBundle)
    assert len(plan_bundle.features) >= 2
    keys = [feature.key.lower() for feature in plan_bundle.features]
    assert any("user" in key for key in keys)
    assert any("payment" in key for key in keys)
    assert all(feature.stories for feature in plan_bundle.features)


class TestSpecKitImportIntegration:
    """Integration tests for Spec-Kit import with realistic repositories."""

    def test_import_realistic_speckit_repo(self):
        """Test importing a realistic Spec-Kit repository structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure (markdown-based format)
            specify_path = repo_path / ".specify"
            specify_path.mkdir()

            specs_path = repo_path / "specs"
            specs_path.mkdir()

            _write_feature(specs_path, "user-service", USER_SERVICE_SPEC, USER_SERVICE_PLAN)
            _write_feature(specs_path, "payment-processor", PAYMENT_PROCESSOR_SPEC, PAYMENT_PROCESSOR_PLAN)
            _write_constitution(specify_path)

            # Test scanner
            scanner = SpecKitScanner(repo_path)
            assert scanner.is_speckit_repo() is True

            structure = scanner.scan_structure()
            assert structure["is_speckit"] is True
            assert all(structure[field] is not None for field in ("specs_dir", "specify_memory_dir"))

            # Test converter
            converter = SpecKitConverter(repo_path)

            # Convert protocol
            protocol = converter.convert_protocol()
            assert isinstance(protocol, Protocol)
            assert len(protocol.states) >= 3  # INIT, at least 2 features, COMPLETE
            assert {"INIT", "COMPLETE"} <= set(protocol.states)

            _assert_realistic_plan(converter.convert_plan())

    def test_import_speckit_via_cli_command(self):
        """Test importing Spec-Kit repository via CLI command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure (markdown-based)
            specify_path = repo_path / ".specify"
            specify_path.mkdir()

            specs_path = repo_path / "specs"
            specs_path.mkdir()

            feature_path = specs_path / "order-service"
            feature_path.mkdir()

            spec_md = dedent(
                """# Feature Specification: Order Service

## User Scenarios & Testing

### User Story 1 - Create Order (Priority: P1)
As a user, I want to create an order so that I can purchase items.

**Acceptance Scenarios**:
1. Given valid order data, When I create an order, Then the order is created

### User Story 2 - Fulfill Order (Priority: P2)
As a merchant, I want to fulfill orders so that customers receive their items.

**Acceptance Scenarios**:
1. Given an order exists, When I fulfill it, Then the order status is updated
"""
            )
            (feature_path / "spec.md").write_text(spec_md)

            plan_md = dedent(
                """# Implementation Plan: Order Service

## Summary
Order management service for creating and fulfilling orders.

## Architecture
- Python 3.11+
- REST API
- Database storage

## Phases
- Phase 1: Order creation
- Phase 2: Order fulfillment
"""
            )
            (feature_path / "plan.md").write_text(plan_md)

            # Create memory
            memory_path = specify_path / "memory"
            memory_path.mkdir()
            (memory_path / "constitution.md").write_text(
                "# Project Constitution\n\n## Core Principles\n\nContract-First Development"
            )

            # Run CLI import command (using bridge adapter)
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-bridge",
                    "--adapter",
                    "speckit",
                    "--repo",
                    str(repo_path),
                    "--write",
                ],
            )

            assert result.exit_code == 0
            assert "Import complete" in result.stdout or "complete" in result.stdout.lower()

            # Verify generated files (modular bundle structure)
            # Note: Import now creates modular project bundles, not monolithic plans
            projects_dir = repo_path / ".specfact" / "projects"
            assert projects_dir.exists()

            # Find the created bundle (usually auto-named or first bundle)
            bundle_dirs = list(projects_dir.iterdir())
            assert len(bundle_dirs) > 0, "No project bundle created"
            bundle_dir = bundle_dirs[0]

            manifest_path = bundle_dir / "bundle.manifest.yaml"
            assert manifest_path.exists()

            # Protocol is in separate location (not in bundle)
            protocol_path = repo_path / ".specfact" / "protocols" / "workflow.protocol.yaml"
            assert protocol_path.exists(), f"Protocol not found at {protocol_path}"

            # Verify protocol content
            protocol_data = load_yaml(protocol_path)
            assert "states" in protocol_data
            assert "transitions" in protocol_data

            # Verify bundle manifest content (modular structure)
            manifest_data = load_yaml(manifest_path)
            assert "versions" in manifest_data
            # Features are now in separate files, check manifest index
            if "features" in manifest_data:
                assert len(manifest_data["features"]) >= 1
            else:
                # Features may be in features/ directory
                features_dir = bundle_dir / "features"
                if features_dir.exists():
                    feature_files = list(features_dir.glob("*.yaml"))
                    assert len(feature_files) >= 1

    def test_import_speckit_generates_github_action(self):
        """Test that GitHub Action workflow is generated during import."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure
            specify_path = repo_path / ".specify"
            specify_path.mkdir()

            specs_path = repo_path / "specs"
            specs_path.mkdir()

            feature_path = specs_path / "test-service"
            feature_path.mkdir()

            (feature_path / "spec.md").write_text("# Feature Specification: Test Service")
            (feature_path / "plan.md").write_text("# Implementation Plan")

            memory_path = specify_path / "memory"
            memory_path.mkdir()
            (memory_path / "constitution.md").write_text("# Project Constitution")

            # Run import
            converter = SpecKitConverter(repo_path)
            converter.convert_protocol()
            converter.convert_plan()
            assert not (repo_path / ".semgrep").exists()

            # Generate GitHub Action
            workflow_path = converter.generate_github_action(repo_name="test-repo")

            assert workflow_path.exists()
            assert workflow_path.name == "specfact-gate.yml"

            # Verify content
            workflow_content = workflow_path.read_text()
            assert "name:" in workflow_content or "name" in workflow_content.lower()

    def test_import_speckit_with_multiple_components(self):
        """Test importing Spec-Kit with multiple features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            specify_path = repo_path / ".specify"
            specify_path.mkdir()

            specs_path = repo_path / "specs"
            specs_path.mkdir()

            # Create three features
            for feature_name in ["auth-service", "data-service", "notification-service"]:
                feature_path = specs_path / feature_name
                feature_path.mkdir()

                spec_md = dedent(
                    f"""# Feature Specification: {feature_name.replace("-", " ").title()}

## User Scenarios & Testing

### User Story 1 (Priority: P1)
As a user, I want to use the {feature_name} so that I can complete my tasks.

**Acceptance Scenarios**:
1. Given the service is available, When I use it, Then it works correctly
"""
                )
                (feature_path / "spec.md").write_text(spec_md)

                plan_md = dedent(
                    f"""# Implementation Plan: {feature_name.replace("-", " ").title()}

## Summary
Service implementation for {feature_name}.

## Architecture
- Python 3.11+
- REST API

## Phases
- Phase 1: Core functionality
"""
                )
                (feature_path / "plan.md").write_text(plan_md)

            memory_path = specify_path / "memory"
            memory_path.mkdir()
            (memory_path / "constitution.md").write_text("# Project Constitution")

            converter = SpecKitConverter(repo_path)
            plan_bundle = converter.convert_plan()

            # Should have 3 features
            assert len(plan_bundle.features) == 3

            feature_titles = [f.title.lower() for f in plan_bundle.features]
            assert any("auth" in title for title in feature_titles)
            assert any("data" in title for title in feature_titles)
            assert any("notification" in title for title in feature_titles)

    def test_import_speckit_with_state_machines(self):
        """Test importing Spec-Kit with state machine definitions in tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            specify_path = repo_path / ".specify"
            specify_path.mkdir()

            specs_path = repo_path / "specs"
            specs_path.mkdir()

            feature_path = specs_path / "workflow-engine"
            feature_path.mkdir()

            spec_md = dedent(
                """# Feature Specification: Workflow Engine

## User Scenarios & Testing

### User Story 1 - Start Workflow (Priority: P1)
As a user, I want to start a workflow so that tasks can be executed.

**Acceptance Scenarios**:
1. Given a workflow is defined, When I start it, Then it transitions to IN_PROGRESS

### User Story 2 - Pause Workflow (Priority: P2)
As a user, I want to pause a workflow so that I can resume it later.

**Acceptance Scenarios**:
1. Given a workflow is running, When I pause it, Then it transitions to PAUSED

### User Story 3 - Complete Workflow (Priority: P3)
As a user, I want to complete a workflow so that all tasks are finished.

**Acceptance Scenarios**:
1. Given a workflow is running, When I complete it, Then it transitions to COMPLETED
"""
            )
            (feature_path / "spec.md").write_text(spec_md)

            plan_md = dedent(
                """# Implementation Plan: Workflow Engine

## Summary
Workflow execution engine with state management.

## Architecture
- Python 3.11+
- State machine implementation
- Event-driven architecture

## Phases
- Phase 1: State machine core
- Phase 2: Event handling
- Phase 3: Workflow execution
"""
            )
            (feature_path / "plan.md").write_text(plan_md)

            memory_path = specify_path / "memory"
            memory_path.mkdir()
            (memory_path / "constitution.md").write_text("# Project Constitution")

            converter = SpecKitConverter(repo_path)
            protocol = converter.convert_protocol()

            # Verify states (at least INIT, feature states, COMPLETE)
            assert len(protocol.states) >= 3
            assert "INIT" in protocol.states
            assert "COMPLETE" in protocol.states

            # Verify start state
            assert protocol.start == "INIT"

            # Note: Markdown-based format doesn't include state machine transitions in the same way
            # The converter generates a minimal protocol with states but transitions are optional
            # The protocol structure is valid even without transitions

    def test_import_speckit_with_nested_structure(self):
        """Test importing Spec-Kit with nested feature structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            specify_path = repo_path / ".specify"
            specify_path.mkdir()

            specs_path = repo_path / "specs"
            specs_path.mkdir()

            # Create main service feature
            main_path = specs_path / "main-service"
            main_path.mkdir()

            spec_md = dedent(
                """# Feature Specification: Main Service

## User Scenarios & Testing

### User Story 1 (Priority: P1)
As a user, I want to use the main service so that I can access sub-services.

**Acceptance Scenarios**:
1. Given the main service is available, When I use it, Then it works correctly
"""
            )
            (main_path / "spec.md").write_text(spec_md)

            plan_md = dedent(
                """# Implementation Plan: Main Service

## Summary
Main service with sub-services.

## Architecture
- Python 3.11+
- Modular design

## Phases
- Phase 1: Core service
"""
            )
            (main_path / "plan.md").write_text(plan_md)

            memory_path = specify_path / "memory"
            memory_path.mkdir()
            (memory_path / "constitution.md").write_text("# Project Constitution")

            converter = SpecKitConverter(repo_path)
            plan_bundle = converter.convert_plan()

            # Should extract main service
            assert len(plan_bundle.features) >= 1
            assert any("main" in f.title.lower() or "main" in f.key.lower() for f in plan_bundle.features)

    def test_import_speckit_handles_missing_components_yaml(self):
        """Test that import handles missing .specify directory gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create specs directory but no .specify
            specs_path = repo_path / "specs"
            specs_path.mkdir()

            scanner = SpecKitScanner(repo_path)
            # Should return False since .specify is required
            assert scanner.is_speckit_repo() is False

    def test_import_speckit_dry_run_mode(self):
        """Test dry-run mode for import command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            specify_path = repo_path / ".specify"
            specify_path.mkdir()

            specs_path = repo_path / "specs"
            specs_path.mkdir()

            feature_path = specs_path / "test-service"
            feature_path.mkdir()

            (feature_path / "spec.md").write_text(
                "# Feature Specification: Test Service\n\n## User Scenarios\n\n### User Story 1\nAs a user, I want to test."
            )

            (feature_path / "plan.md").write_text("# Implementation Plan\n\n## Summary\nTest service.")

            memory_path = specify_path / "memory"
            memory_path.mkdir()
            (memory_path / "constitution.md").write_text("# Project Constitution")

            # Run dry-run
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-bridge",
                    "--adapter",
                    "speckit",
                    "--repo",
                    str(repo_path),
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0
            assert "dry run" in result.stdout.lower() or "preview" in result.stdout.lower()

            # Should not create files
            protocol_path = repo_path / ".specfact" / "protocols" / "workflow.protocol.yaml"
            assert not protocol_path.exists()

    def test_import_speckit_with_full_workflow(self):
        """Test complete import workflow including all generated artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            _write_full_workflow_project(repo_path)

            # Run complete import via CLI
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-bridge",
                    "--adapter",
                    "speckit",
                    "--repo",
                    str(repo_path),
                    "--write",
                ],
            )

            assert result.exit_code == 0

            _assert_full_import_artifacts(repo_path)
