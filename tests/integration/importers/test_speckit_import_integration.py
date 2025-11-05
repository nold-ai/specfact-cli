"""Integration tests for Spec-Kit import with realistic repositories."""

import tempfile
from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.importers.speckit_converter import SpecKitConverter
from specfact_cli.importers.speckit_scanner import SpecKitScanner
from specfact_cli.models.plan import PlanBundle
from specfact_cli.models.protocol import Protocol
from specfact_cli.utils.yaml_utils import load_yaml


runner = CliRunner()


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

            # Create feature 1: UserService
            feature1_path = specs_path / "user-service"
            feature1_path.mkdir()

            spec1_md = dedent(
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
            (feature1_path / "spec.md").write_text(spec1_md)

            plan1_md = dedent(
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
            (feature1_path / "plan.md").write_text(plan1_md)

            # Create feature 2: PaymentProcessor
            feature2_path = specs_path / "payment-processor"
            feature2_path.mkdir()

            spec2_md = dedent(
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
            (feature2_path / "spec.md").write_text(spec2_md)

            plan2_md = dedent(
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
            (feature2_path / "plan.md").write_text(plan2_md)

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

            # Test scanner
            scanner = SpecKitScanner(repo_path)
            assert scanner.is_speckit_repo() is True

            structure = scanner.scan_structure()
            assert structure["is_speckit"] is True
            assert structure["specs_dir"] is not None
            assert structure["specify_memory_dir"] is not None

            # Test converter
            converter = SpecKitConverter(repo_path)

            # Convert protocol
            protocol = converter.convert_protocol()
            assert isinstance(protocol, Protocol)
            assert len(protocol.states) >= 3  # INIT, at least 2 features, COMPLETE
            assert "INIT" in protocol.states
            assert "COMPLETE" in protocol.states

            # Convert plan
            plan_bundle = converter.convert_plan()
            assert isinstance(plan_bundle, PlanBundle)
            assert len(plan_bundle.features) >= 2  # UserService and PaymentProcessor

            # Verify feature extraction
            feature_keys = [f.key for f in plan_bundle.features]
            assert any("user" in key.lower() for key in feature_keys)
            assert any("payment" in key.lower() for key in feature_keys)

            # Verify stories were extracted
            for feature in plan_bundle.features:
                assert len(feature.stories) > 0

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

            # Run CLI import command
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-spec-kit",
                    "--repo",
                    str(repo_path),
                    "--write",
                ],
            )

            assert result.exit_code == 0
            assert "Import complete" in result.stdout or "complete" in result.stdout.lower()

            # Verify generated files
            protocol_path = repo_path / ".specfact" / "protocols" / "workflow.protocol.yaml"
            plan_path = repo_path / ".specfact" / "plans" / "main.bundle.yaml"

            assert protocol_path.exists()
            assert plan_path.exists()

            # Verify protocol content
            protocol_data = load_yaml(protocol_path)
            assert "states" in protocol_data
            assert "transitions" in protocol_data

            # Verify plan content
            plan_data = load_yaml(plan_path)
            assert plan_data["version"] == "1.0"
            assert "features" in plan_data
            assert len(plan_data["features"]) >= 1

    def test_import_speckit_generates_semgrep_rules(self):
        """Test that Semgrep rules are generated during import."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Spec-Kit structure
            specify_path = repo_path / ".specify"
            specify_path.mkdir()

            specs_path = repo_path / "specs"
            specs_path.mkdir()

            feature_path = specs_path / "test-service"
            feature_path.mkdir()

            (feature_path / "spec.md").write_text(
                "# Feature Specification: Test Service\n\n## User Scenarios\n\n### User Story 1\nAs a user, I want to test the service."
            )

            (feature_path / "plan.md").write_text("# Implementation Plan\n\n## Summary\nTest service.")

            memory_path = specify_path / "memory"
            memory_path.mkdir()
            (memory_path / "constitution.md").write_text("# Project Constitution")

            # Run import
            converter = SpecKitConverter(repo_path)
            converter.convert_protocol()
            converter.convert_plan()

            # Generate Semgrep rules
            semgrep_path = converter.generate_semgrep_rules()

            assert semgrep_path.exists()
            assert semgrep_path.name == "async-anti-patterns.yml"

            # Verify content
            semgrep_content = semgrep_path.read_text()
            assert "rules:" in semgrep_content or "rules" in semgrep_content

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
                    "from-spec-kit",
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

            # Run complete import via CLI
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-spec-kit",
                    "--repo",
                    str(repo_path),
                    "--write",
                ],
            )

            assert result.exit_code == 0

            # Verify all artifacts
            protocol_path = repo_path / ".specfact" / "protocols" / "workflow.protocol.yaml"
            plan_path = repo_path / ".specfact" / "plans" / "main.bundle.yaml"
            semgrep_path = repo_path / ".semgrep" / "async-anti-patterns.yml"
            workflow_path = repo_path / ".github" / "workflows" / "specfact-gate.yml"

            assert protocol_path.exists()
            assert plan_path.exists()
            assert semgrep_path.exists()
            assert workflow_path.exists()

            # Verify protocol has correct states
            protocol_data = load_yaml(protocol_path)
            assert len(protocol_data["states"]) >= 3
            assert "INIT" in protocol_data["states"]
            assert "COMPLETE" in protocol_data["states"]

            # Verify plan has feature with stories
            plan_data = load_yaml(plan_path)
            assert len(plan_data["features"]) >= 1
            feature = plan_data["features"][0]
            assert len(feature["stories"]) > 0
