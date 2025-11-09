# Testing Guide

This document provides comprehensive guidance on testing the SpecFact CLI, including examples of how to test the `.specfact/` directory structure.

## Table of Contents

- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [End-to-End Tests](#end-to-end-tests)
- [Testing Operational Modes](#testing-operational-modes)
- [Testing Sync Operations](#testing-sync-operations)
- [Testing Directory Structure](#testing-directory-structure)
- [Test Fixtures](#test-fixtures)
- [Best Practices](#best-practices)

## Test Organization

Tests are organized into three layers:

```bash
tests/
├── unit/               # Unit tests for individual modules
│   ├── analyzers/      # Code analyzer tests
│   ├── comparators/    # Plan comparator tests
│   ├── generators/     # Generator tests
│   ├── models/         # Data model tests
│   ├── utils/          # Utility tests
│   └── validators/     # Validator tests
├── integration/        # Integration tests for CLI commands
│   ├── analyzers/      # Analyze command tests
│   ├── comparators/    # Plan compare command tests
│   └── test_directory_structure.py  # Directory structure tests
└── e2e/                # End-to-end workflow tests
    ├── test_complete_workflow.py
    └── test_directory_structure_workflow.py
```

## Running Tests

### All Tests

```bash
# Run all tests with coverage
hatch test --cover -v

# Run specific test file
hatch test --cover -v tests/integration/test_directory_structure.py

# Run specific test class
hatch test --cover -v tests/integration/test_directory_structure.py::TestDirectoryStructure

# Run specific test method
hatch test --cover -v tests/integration/test_directory_structure.py::TestDirectoryStructure::test_ensure_structure_creates_directories
```

### Contract-First Testing

```bash
# Run contract tests
hatch run contract-test

# Run contract validation
hatch run contract-test-contracts

# Run scenario tests
hatch run contract-test-scenarios
```

## Unit Tests

Unit tests focus on individual modules and functions.

### Example: Testing CodeAnalyzer

```python
def test_code_analyzer_extracts_features(tmp_path):
    """Test that CodeAnalyzer extracts features from classes."""
    # Create test file
    code = '''
class UserService:
    """User management service."""
    
    def create_user(self, name):
        """Create new user."""
        pass
'''
    repo_path = tmp_path / "src"
    repo_path.mkdir()
    (repo_path / "service.py").write_text(code)
    
    # Analyze
    analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
    plan = analyzer.analyze()
    
    # Verify
    assert len(plan.features) > 0
    assert any("User" in f.title for f in plan.features)
```

### Example: Testing PlanComparator

```python
def test_plan_comparator_detects_missing_feature():
    """Test that PlanComparator detects missing features."""
    # Create plans
    feature = Feature(
        key="FEATURE-001",
        title="Auth",
        outcomes=["Login works"],
        acceptance=["Users can login"],
    )
    
    manual_plan = PlanBundle(
        version="1.0",
        idea=None,
        business=None,
        product=Product(themes=[], releases=[]),
        features=[feature],
    )
    
    auto_plan = PlanBundle(
        version="1.0",
        idea=None,
        business=None,
        product=Product(themes=[], releases=[]),
        features=[],  # Missing feature
    )
    
    # Compare
    comparator = PlanComparator()
    report = comparator.compare(manual_plan, auto_plan)
    
    # Verify
    assert report.total_deviations == 1
    assert report.high_count == 1
    assert "FEATURE-001" in report.deviations[0].description
```

## Integration Tests

Integration tests verify CLI commands work correctly.

### Example: Testing `import from-code`

```python
def test_analyze_code2spec_basic_repository():
    """Test analyzing a basic Python repository."""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample code
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir()
        
        code = '''
class PaymentProcessor:
    """Process payments."""
    def process_payment(self, amount):
        """Process a payment."""
        pass
'''
        (src_dir / "payment.py").write_text(code)
        
        # Run command
        result = runner.invoke(
            app,
            [
                "analyze",
                "code2spec",
                "--repo",
                tmpdir,
            ],
        )
        
        # Verify
        assert result.exit_code == 0
        assert "Analysis complete" in result.stdout
        
        # Verify output in .specfact/
        brownfield_dir = Path(tmpdir) / ".specfact" / "reports" / "brownfield"
        assert brownfield_dir.exists()
        reports = list(brownfield_dir.glob("auto-derived.*.yaml"))
        assert len(reports) > 0
```

### Example: Testing `plan compare`

```python
def test_plan_compare_with_smart_defaults(tmp_path):
    """Test plan compare finds plans using smart defaults."""
    # Create manual plan
    manual_plan = PlanBundle(
        version="1.0",
        idea=Idea(title="Test", narrative="Test"),
        business=None,
        product=Product(themes=[], releases=[]),
        features=[],
    )
    
    manual_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
    manual_path.parent.mkdir(parents=True)
    dump_yaml(manual_plan.model_dump(exclude_none=True), manual_path)
    
    # Create auto-derived plan
    brownfield_dir = tmp_path / ".specfact" / "reports" / "brownfield"
    brownfield_dir.mkdir(parents=True)
    auto_path = brownfield_dir / "auto-derived.2025-01-01T10-00-00.bundle.yaml"
    dump_yaml(manual_plan.model_dump(exclude_none=True), auto_path)
    
    # Run compare with --repo only
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "plan",
            "compare",
            "--repo",
            str(tmp_path),
        ],
    )
    
    assert result.exit_code == 0
    assert "No deviations found" in result.stdout
```

## End-to-End Tests

E2E tests verify complete workflows from start to finish.

### Example: Complete Greenfield Workflow

```python
def test_greenfield_workflow_with_scaffold(tmp_path):
    """
    Test complete greenfield workflow:
    1. Init project with scaffold
    2. Verify structure created
    3. Edit plan manually
    4. Validate plan
    """
    runner = CliRunner()
    
    # Step 1: Initialize project with scaffold
    result = runner.invoke(
        app,
        [
            "plan",
            "init",
            "--repo",
            str(tmp_path),
            "--title",
            "E2E Test Project",
            "--scaffold",
        ],
    )
    
    assert result.exit_code == 0
    assert "Scaffolded .specfact directory structure" in result.stdout
    
    # Step 2: Verify structure
    specfact_dir = tmp_path / ".specfact"
    assert (specfact_dir / "plans" / "main.bundle.yaml").exists()
    assert (specfact_dir / "protocols").exists()
    assert (specfact_dir / "reports" / "brownfield").exists()
    assert (specfact_dir / ".gitignore").exists()
    
    # Step 3: Load and verify plan
    plan_path = specfact_dir / "plans" / "main.bundle.yaml"
    plan_data = load_yaml(plan_path)
    assert plan_data["version"] == "1.0"
    assert plan_data["idea"]["title"] == "E2E Test Project"
```

### Example: Complete Brownfield Workflow

```python
def test_brownfield_analysis_workflow(tmp_path):
    """
    Test complete brownfield workflow:
    1. Analyze existing codebase
    2. Verify plan generated in .specfact/plans/
    3. Create manual plan in .specfact/plans/
    4. Compare plans
    5. Verify comparison report in .specfact/reports/comparison/
    """
    runner = CliRunner()
    
    # Step 1: Create sample codebase
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    (src_dir / "users.py").write_text('''
class UserService:
    """Manages user operations."""
    def create_user(self, name, email):
        """Create a new user account."""
        pass
    def get_user(self, user_id):
        """Retrieve user by ID."""
        pass
''')
    
    # Step 2: Run brownfield analysis
    result = runner.invoke(
        app,
        ["analyze", "code2spec", "--repo", str(tmp_path)],
    )
    assert result.exit_code == 0
    
    # Step 3: Verify auto-derived plan
    brownfield_dir = tmp_path / ".specfact" / "reports" / "brownfield"
    auto_reports = list(brownfield_dir.glob("auto-derived.*.yaml"))
    assert len(auto_reports) > 0
    
    # Step 4: Create manual plan
    # ... (create and save manual plan)
    
    # Step 5: Run comparison
    result = runner.invoke(
        app,
        ["plan", "compare", "--repo", str(tmp_path)],
    )
    assert result.exit_code == 0
    
    # Step 6: Verify comparison report
    comparison_dir = tmp_path / ".specfact" / "reports" / "comparison"
    comparison_reports = list(comparison_dir.glob("report-*.md"))
    assert len(comparison_reports) > 0
```

## Testing Operational Modes

SpecFact CLI supports two operational modes that should be tested:

### Testing CI/CD Mode

```python
def test_analyze_cicd_mode(tmp_path):
    """Test analyze command in CI/CD mode."""
    runner = CliRunner()
    
    # Create sample code
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "service.py").write_text('''
class UserService:
    """User management service."""
    def create_user(self, name):
        """Create new user."""
        pass
''')
    
    # Run in CI/CD mode
    result = runner.invoke(
        app,
        [
            "--mode",
            "cicd",
            "analyze",
            "code2spec",
            "--repo",
            str(tmp_path),
        ],
    )
    
    assert result.exit_code == 0
    assert "Analysis complete" in result.stdout
    
    # Verify deterministic output
    brownfield_dir = tmp_path / ".specfact" / "reports" / "brownfield"
    reports = list(brownfield_dir.glob("auto-derived.*.yaml"))
    assert len(reports) > 0
```

### Testing CoPilot Mode

```python
def test_analyze_copilot_mode(tmp_path):
    """Test analyze command in CoPilot mode."""
    runner = CliRunner()
    
    # Create sample code
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "service.py").write_text('''
class UserService:
    """User management service."""
    def create_user(self, name):
        """Create new user."""
        pass
''')
    
    # Run in CoPilot mode
    result = runner.invoke(
        app,
        [
            "--mode",
            "copilot",
            "analyze",
            "code2spec",
            "--repo",
            str(tmp_path),
            "--confidence",
            "0.7",
        ],
    )
    
    assert result.exit_code == 0
    assert "Analysis complete" in result.stdout
    
    # CoPilot mode may provide enhanced prompts
    # (behavior depends on CoPilot availability)
```

### Testing Mode Auto-Detection

```python
def test_mode_auto_detection(tmp_path):
    """Test that mode is auto-detected correctly."""
    runner = CliRunner()
    
    # Without explicit mode, should auto-detect
    result = runner.invoke(
        app,
        ["analyze", "code2spec", "--repo", str(tmp_path)],
    )
    
    assert result.exit_code == 0
    # Default to CI/CD mode if CoPilot not available
```

## Testing Sync Operations

Sync operations require thorough testing for bidirectional synchronization:

### Testing Spec-Kit Sync

```python
def test_sync_speckit_one_way(tmp_path):
    """Test one-way Spec-Kit sync (import)."""
    # Create Spec-Kit structure
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    (spec_dir / "components.yaml").write_text('''
states:
  - INIT
  - PLAN
transitions:
  - from_state: INIT
    on_event: start
    to_state: PLAN
''')
    
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "sync",
            "spec-kit",
            "--repo",
            str(tmp_path),
        ],
    )
    
    assert result.exit_code == 0
    # Verify SpecFact artifacts created
    plan_path = tmp_path / ".specfact" / "plans" / "main.bundle.yaml"
    assert plan_path.exists()
```

### Testing Bidirectional Sync

```python
def test_sync_speckit_bidirectional(tmp_path):
    """Test bidirectional Spec-Kit sync."""
    # Create Spec-Kit structure
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    (spec_dir / "components.yaml").write_text('''
states:
  - INIT
  - PLAN
transitions:
  - from_state: INIT
    on_event: start
    to_state: PLAN
''')
    
    # Create SpecFact plan
    plans_dir = tmp_path / ".specfact" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "main.bundle.yaml").write_text('''
version: "1.0"
features:
  - key: FEATURE-001
    title: "Test Feature"
''')
    
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "sync",
            "spec-kit",
            "--repo",
            str(tmp_path),
            "--bidirectional",
        ],
    )
    
    assert result.exit_code == 0
    # Verify both directions synced
```

### Testing Repository Sync

```python
def test_sync_repository(tmp_path):
    """Test repository sync."""
    # Create sample code
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "service.py").write_text('''
class UserService:
    """User management service."""
    def create_user(self, name):
        """Create new user."""
        pass
''')
    
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "sync",
            "repository",
            "--repo",
            str(tmp_path),
            "--target",
            ".specfact",
        ],
    )
    
    assert result.exit_code == 0
    # Verify plan artifacts updated
    brownfield_dir = tmp_path / ".specfact" / "reports" / "sync"
    assert brownfield_dir.exists()
```

### Testing Watch Mode

```python
import time
from unittest.mock import patch

def test_sync_watch_mode(tmp_path):
    """Test watch mode for continuous sync."""
    # Create sample code
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "service.py").write_text('''
class UserService:
    """User management service."""
    def create_user(self, name):
        """Create new user."""
        pass
''')
    
    runner = CliRunner()
    
    # Test watch mode with short interval
    with patch('time.sleep') as mock_sleep:
        result = runner.invoke(
            app,
            [
                "sync",
                "repository",
                "--repo",
                str(tmp_path),
                "--watch",
                "--interval",
                "1",
            ],
            input="\n",  # Press Enter to stop after first iteration
        )
        
        # Watch mode should run at least once
        assert mock_sleep.called
```

## Testing Directory Structure

The `.specfact/` directory structure is a core feature that requires thorough testing.

### Testing Directory Creation

```python
def test_ensure_structure_creates_directories(tmp_path):
    """Test that ensure_structure creates all required directories."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    # Ensure structure
    SpecFactStructure.ensure_structure(repo_path)
    
    # Verify all directories exist
    specfact_dir = repo_path / ".specfact"
    assert specfact_dir.exists()
    assert (specfact_dir / "plans").exists()
    assert (specfact_dir / "protocols").exists()
    assert (specfact_dir / "reports" / "brownfield").exists()
    assert (specfact_dir / "reports" / "comparison").exists()
    assert (specfact_dir / "gates" / "results").exists()
    assert (specfact_dir / "cache").exists()
```

### Testing Scaffold Functionality

```python
def test_scaffold_project_creates_full_structure(tmp_path):
    """Test that scaffold_project creates complete directory structure."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    # Scaffold project
    SpecFactStructure.scaffold_project(repo_path)
    
    # Verify directories
    specfact_dir = repo_path / ".specfact"
    assert (specfact_dir / "plans").exists()
    assert (specfact_dir / "protocols").exists()
    assert (specfact_dir / "reports" / "brownfield").exists()
    assert (specfact_dir / "gates" / "config").exists()
    
    # Verify .gitignore
    gitignore = specfact_dir / ".gitignore"
    assert gitignore.exists()
    
    gitignore_content = gitignore.read_text()
    assert "reports/" in gitignore_content
    assert "gates/results/" in gitignore_content
    assert "cache/" in gitignore_content
```

### Testing Smart Defaults

```python
def test_analyze_default_paths(tmp_path):
    """Test that analyze uses .specfact/ paths by default."""
    # Create sample code
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "test.py").write_text('''
class TestService:
    """Test service."""
    def test_method(self):
        """Test method."""
        pass
''')
    
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["analyze", "code2spec", "--repo", str(tmp_path)],
    )
    
    assert result.exit_code == 0
    
    # Verify files in .specfact/
    brownfield_dir = tmp_path / ".specfact" / "reports" / "brownfield"
    assert brownfield_dir.exists()
    reports = list(brownfield_dir.glob("auto-derived.*.yaml"))
    assert len(reports) > 0
```

## Test Fixtures

Use pytest fixtures to reduce code duplication.

### Common Fixtures

```python
@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary repository with .specfact structure."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    SpecFactStructure.scaffold_project(repo_path)
    return repo_path

@pytest.fixture
def sample_plan():
    """Create a sample plan bundle."""
    return PlanBundle(
        version="1.0",
        idea=Idea(title="Test Project", narrative="Test"),
        business=None,
        product=Product(themes=["Testing"], releases=[]),
        features=[],
    )

@pytest.fixture
def sample_code(tmp_path):
    """Create sample Python code for testing."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    code = '''
class SampleService:
    """Sample service for testing."""
    def sample_method(self):
        """Sample method."""
        pass
'''
    (src_dir / "sample.py").write_text(code)
    return tmp_path
```

### Using Fixtures

```python
def test_with_fixtures(tmp_repo, sample_plan):
    """Test using fixtures."""
    # Use pre-configured repository
    manual_path = tmp_repo / ".specfact" / "plans" / "main.bundle.yaml"
    dump_yaml(sample_plan.model_dump(exclude_none=True), manual_path)
    
    assert manual_path.exists()
```

## Best Practices

### 1. Test Isolation

Ensure tests don't depend on each other or external state:

```python
def test_isolated(tmp_path):
    """Each test gets its own tmp_path."""
    # Use tmp_path for all file operations
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    # Test logic...
```

### 2. Clear Test Names

Use descriptive test names that explain what is being tested:

```python
def test_plan_compare_detects_missing_feature_in_auto_plan():
    """Good: Clear what is being tested."""
    pass

def test_compare():
    """Bad: Unclear what is being tested."""
    pass
```

### 3. Arrange-Act-Assert Pattern

Structure tests clearly:

```python
def test_example():
    # Arrange: Setup test data
    plan = create_test_plan()
    
    # Act: Execute the code being tested
    result = process_plan(plan)
    
    # Assert: Verify results
    assert result.success is True
```

### 4. Test Both Success and Failure Cases

```python
def test_valid_plan_passes_validation():
    """Test success case."""
    plan = create_valid_plan()
    report = validate_plan_bundle(plan)
    assert report.passed is True

def test_invalid_plan_fails_validation():
    """Test failure case."""
    plan = create_invalid_plan()
    report = validate_plan_bundle(plan)
    assert report.passed is False
    assert len(report.deviations) > 0
```

### 5. Use Assertions Effectively

```python
def test_with_good_assertions():
    """Use specific assertions with helpful messages."""
    result = compute_value()
    
    # Good: Specific assertion
    assert result == 42, f"Expected 42, got {result}"
    
    # Good: Multiple specific assertions
    assert result > 0, "Result should be positive"
    assert result < 100, "Result should be less than 100"
```

### 6. Mock External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mocking():
    """Mock external API calls."""
    with patch('module.external_api_call') as mock_api:
        mock_api.return_value = {"status": "success"}
        
        result = function_that_calls_api()
        
        assert result.status == "success"
        mock_api.assert_called_once()
```

## Running Specific Test Suites

```bash
# Run only unit tests
hatch test --cover -v tests/unit/

# Run only integration tests
hatch test --cover -v tests/integration/

# Run only E2E tests
hatch test --cover -v tests/e2e/

# Run tests matching a pattern
hatch test --cover -v -k "directory_structure"

# Run tests with verbose output
hatch test --cover -vv tests/

# Run tests and stop on first failure
hatch test --cover -v -x tests/
```

## Coverage Goals

- **Unit tests**: Target 90%+ coverage for individual modules
- **Integration tests**: Cover all CLI commands and major workflows
- **E2E tests**: Cover complete user journeys
- **Operational modes**: Test both CI/CD and CoPilot modes
- **Sync operations**: Test bidirectional sync, watch mode, and conflict resolution

## Continuous Integration

Tests run automatically on:

- Every commit
- Pull requests
- Before releases

CI configuration ensures:

- All tests pass
- Coverage thresholds met
- No linter errors

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Typer testing guide](https://typer.tiangolo.com/tutorial/testing/)
- [Python testing best practices](https://docs.python-guide.org/writing/tests/)
