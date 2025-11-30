# Code2Spec Analysis Logic: How It Works

> **TL;DR**: SpecFact CLI uses **AI-first approach** via AI IDE integration (Cursor, CoPilot, etc.) for semantic understanding, with **AST-based fallback** for CI/CD mode. The AI IDE's native LLM understands the codebase semantically, then calls the SpecFact CLI for structured analysis. This avoids separate LLM API setup, langchain, or additional API keys while providing high-quality, semantic-aware analysis that works with all languages and generates Spec-Kit compatible artifacts.

---

## Overview

The `code2spec` command analyzes existing codebases and reverse-engineers them into plan bundles (features, stories, tasks). It uses **two approaches** depending on operational mode:

### **Mode 1: AI-First (CoPilot Mode)** - Recommended

Uses **AI IDE's native LLM** for semantic understanding via pragmatic integration:

**Workflow**:

1. **AI IDE's LLM** understands codebase semantically (via slash command prompt)
2. **AI calls SpecFact CLI** (`specfact import from-code <bundle-name>`) for structured analysis
3. **AI enhances results** with semantic understanding (priorities, constraints, unknowns)
4. **CLI handles structured work** (file I/O, YAML generation, validation)

**Benefits**:

- ✅ **No separate LLM setup** - Uses AI IDE's existing LLM (Cursor, CoPilot, etc.)
- ✅ **No additional API costs** - Leverages existing IDE infrastructure
- ✅ **Simpler architecture** - No langchain, API keys, or complex integration
- ✅ **Multi-language support** - Works with Python, TypeScript, JavaScript, PowerShell, Go, Rust, etc.

- ✅ **Semantic understanding** - AI understands business logic, not just structure
- ✅ **High-quality output** - Generates meaningful priorities, constraints, unknowns
- ✅ **Spec-Kit compatible** - Produces artifacts that pass `/speckit.analyze` validation
- ✅ **Bidirectional sync** - Preserves semantics during Spec-Kit ↔ SpecFact sync

**Why this approach?**

- ✅ **Pragmatic** - Uses existing IDE infrastructure, no extra setup
- ✅ **Cost-effective** - No additional API costs
- ✅ **Streamlined** - Native IDE integration, better developer experience
- ✅ **Maintainable** - Simpler architecture, less code to maintain

### **Mode 2: AST+Semgrep Hybrid (CI/CD Mode)** - Enhanced Fallback

Uses **Python's AST + Semgrep pattern matching** for comprehensive structural analysis when LLM is unavailable:

1. **AST Parsing** - Python's built-in Abstract Syntax Tree for structural analysis
2. **Semgrep Pattern Detection** - Framework-aware pattern matching (API endpoints, models, CRUD, auth)
3. **Pattern Matching** - Heuristic-based method grouping enhanced with Semgrep findings
4. **Confidence Scoring** - Evidence-based quality metrics combining AST + Semgrep evidence
5. **Code Quality Assessment** - Anti-pattern detection and maturity scoring
6. **Deterministic Algorithms** - No randomness, 100% reproducible

**Why AST+Semgrep hybrid?**

- ✅ **Fast** - Analyzes thousands of lines in seconds (parallelized)
- ✅ **Deterministic** - Same code always produces same results
- ✅ **Offline** - No cloud services or API calls
- ✅ **Framework-Aware** - Detects FastAPI, Flask, SQLAlchemy, Pydantic patterns
- ✅ **Enhanced Detection** - API endpoints, database models, CRUD operations, auth patterns
- ✅ **Code Quality** - Identifies anti-patterns and code smells
- ✅ **Multi-language Ready** - Semgrep supports TypeScript, JavaScript, Go (patterns ready)
- ⚠️ **Python-Focused** - Currently optimized for Python (other languages pending)

---

## Architecture

```mermaid
flowchart TD
    A["code2spec Command<br/>specfact import from-code my-project --repo . --confidence 0.5"] --> B{Operational Mode}
    
    B -->|CoPilot Mode| C["AnalyzeAgent (AI-First)<br/>• LLM semantic understanding<br/>• Multi-language support<br/>• Semantic extraction (priorities, constraints, unknowns)<br/>• High-quality Spec-Kit artifacts"]
    
    B -->|CI/CD Mode| D["CodeAnalyzer (AST+Semgrep Hybrid)<br/>• AST parsing (Python's built-in ast module)<br/>• Semgrep pattern detection (API, models, CRUD, auth)<br/>• Pattern matching (method name + Semgrep findings)<br/>• Confidence scoring (AST + Semgrep evidence)<br/>• Code quality assessment (anti-patterns)<br/>• Story point calculation (Fibonacci sequence)"]
    
    C --> E["Features with Semantic Understanding<br/>• Actual priorities from code context<br/>• Actual constraints from code/docs<br/>• Actual unknowns from code analysis<br/>• Meaningful scenarios from acceptance criteria"]
    
    D --> F["Features from Structure + Patterns<br/>• Framework-aware outcomes (API endpoints, models)<br/>• CRUD operation detection<br/>• Code quality constraints (anti-patterns)<br/>• Enhanced confidence scores<br/>• Python-focused (multi-language ready)"]
    
    style A fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#fff
    style C fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#fff
    style D fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#fff
    style E fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#fff
    style F fill:#FF5722,stroke:#E64A19,stroke-width:2px,color:#fff
```

---

## Step-by-Step Process

### Step 1: File Discovery and Filtering

```python
# Find all Python files
python_files = repo_path.rglob("*.py")

# Skip certain directories
skip_patterns = [
    "__pycache__", ".git", "venv", ".venv", 
    "env", ".pytest_cache", "htmlcov",
    "dist", "build", ".eggs"
]

# Test files: Included by default for comprehensive analysis
# Use --exclude-tests flag to skip test files for faster processing (~30-50% speedup)
# Rationale: Test files are consumers of production code (one-way dependency),
# so skipping them doesn't affect production dependency graph
```

**Rationale**: Only analyze production code, not test files or dependencies.

---

### Step 2: AST Parsing + Semgrep Pattern Detection

For each Python file, we use **two complementary approaches**:

#### 2.1 AST Parsing

```python
content = file_path.read_text(encoding="utf-8")
tree = ast.parse(content)  # Built-in Python AST parser
```

**What AST gives us:**

- ✅ Class definitions (`ast.ClassDef`)
- ✅ Function/method definitions (`ast.FunctionDef`)
- ✅ Import statements (`ast.Import`, `ast.ImportFrom`)
- ✅ Docstrings (via `ast.get_docstring()`)
- ✅ Method signatures and bodies

**Why AST?**

- Built into Python (no dependencies)
- Preserves exact structure (not text parsing)
- Handles all Python syntax correctly
- Extracts metadata (docstrings, names, structure)

#### 2.2 Semgrep Pattern Detection

```python
# Run Semgrep for pattern detection (parallel-safe)
semgrep_findings = self._run_semgrep_patterns(file_path)
```

**What Semgrep gives us:**

- ✅ **API Endpoints**: FastAPI, Flask, Express, Gin routes (method + path)
- ✅ **Database Models**: SQLAlchemy, Django, Pydantic, TortoiseORM, Peewee
- ✅ **CRUD Operations**: Function naming patterns (create_*, get_*, update_*, delete_*)
- ✅ **Authentication**: Auth decorators, permission checks
- ✅ **Framework Patterns**: Async/await, context managers, type hints
- ✅ **Code Quality**: Anti-patterns, code smells, security vulnerabilities

**Why Semgrep?**

- Framework-aware pattern detection
- Multi-language support (Python, TypeScript, JavaScript, Go)
- Fast pattern matching (parallel execution)
- Rule-based (no hardcoded logic)

---

### Step 3: Feature Extraction from Classes (AST + Semgrep Enhanced)

**Rule**: Each public class (not starting with `_`) becomes a potential feature.

```python
def _extract_feature_from_class(node: ast.ClassDef, file_path: Path) -> Feature | None:
    # Skip private classes
    if node.name.startswith("_") or node.name.startswith("Test"):
        return None
    
    # Generate feature key: FEATURE-CLASSNAME
    feature_key = f"FEATURE-{node.name.upper()}"
    
    # Extract docstring as outcome
    docstring = ast.get_docstring(node)
    if docstring:
        outcomes = [docstring.split("\n\n")[0].strip()]
    else:
        outcomes = [f"Provides {humanize_name(node.name)} functionality"]
```

**Example**:

- `EnforcementConfig` class → `FEATURE-ENFORCEMENTCONFIG` feature
- Docstring "Configuration for contract enforcement" → Outcome
- Methods grouped into stories (see Step 4)

---

### Step 4: Story Extraction from Methods

**Key Insight**: Methods are grouped by **functionality patterns**, not individually.

#### 4.1 Method Grouping (Pattern Matching)

Methods are grouped using **keyword matching** on method names:

```python
def _group_methods_by_functionality(methods: list[ast.FunctionDef]) -> dict[str, list]:
    groups = defaultdict(list)
    
    for method in public_methods:
        name_lower = method.name.lower()
        
        # CRUD Operations
        if any(crud in name_lower for crud in ["create", "add", "insert", "new"]):
            groups["Create Operations"].append(method)
        elif any(read in name_lower for read in ["get", "read", "fetch", "find", "list"]):
            groups["Read Operations"].append(method)
        elif any(update in name_lower for update in ["update", "modify", "edit"]):
            groups["Update Operations"].append(method)
        elif any(delete in name_lower for delete in ["delete", "remove", "destroy"]):
            groups["Delete Operations"].append(method)
        
        # Validation
        elif any(val in name_lower for val in ["validate", "check", "verify"]):
            groups["Validation"].append(method)
        
        # Processing
        elif any(proc in name_lower for proc in ["process", "compute", "transform"]):
            groups["Processing"].append(method)
        
        # Analysis
        elif any(an in name_lower for an in ["analyze", "parse", "extract"]):
            groups["Analysis"].append(method)
        
        # ... more patterns
```

**Pattern Groups**:

| Group | Keywords | Example Methods |
|-------|----------|----------------|
| **Create Operations** | `create`, `add`, `insert`, `new` | `create_user()`, `add_item()` |
| **Read Operations** | `get`, `read`, `fetch`, `find`, `list` | `get_user()`, `list_items()` |
| **Update Operations** | `update`, `modify`, `edit`, `change` | `update_profile()`, `modify_settings()` |
| **Delete Operations** | `delete`, `remove`, `destroy` | `delete_user()`, `remove_item()` |
| **Validation** | `validate`, `check`, `verify` | `validate_input()`, `check_permissions()` |
| **Processing** | `process`, `compute`, `transform` | `process_data()`, `transform_json()` |
| **Analysis** | `analyze`, `parse`, `extract` | `analyze_code()`, `parse_config()` |
| **Generation** | `generate`, `build`, `make` | `generate_report()`, `build_config()` |
| **Comparison** | `compare`, `diff`, `match` | `compare_plans()`, `diff_files()` |
| **Configuration** | `setup`, `configure`, `initialize` | `setup_logger()`, `configure_db()` |

**Why Pattern Matching?**

- ✅ Fast - Simple string matching, no ML overhead
- ✅ Deterministic - Same patterns always grouped together
- ✅ Interpretable - You can see why methods are grouped
- ✅ Customizable - Easy to add new patterns

---

#### 4.2 Story Creation from Method Groups

Each method group becomes a **user story**:

```python
def _create_story_from_method_group(group_name, methods, class_name, story_number):
    # Generate story key: STORY-CLASSNAME-001
    story_key = f"STORY-{class_name.upper()}-{story_number:03d}"
    
    # Create user-centric title
    title = f"As a user, I can {group_name.lower()} {class_name}"
    
    # Extract tasks (method names)
    tasks = [f"{method.name}()" for method in methods]
    
    # Extract acceptance from docstrings (Phase 4: Simple text format)
    acceptance = []
    for method in methods:
        docstring = ast.get_docstring(method)
        if docstring:
            # Phase 4: Use simple text description (not verbose GWT)
            # Examples are stored in OpenAPI contracts, not in feature YAML
            first_line = docstring.split("\n")[0].strip()
            # Convert to simple format: "Feature works correctly (see contract examples)"
            method_name = method.name.replace("_", " ").title()
            acceptance.append(f"{method_name} works correctly (see contract examples)")
    
    # Calculate story points and value points
    story_points = _calculate_story_points(methods)
    value_points = _calculate_value_points(methods, group_name)
```

**Example** (Phase 4 Format):

```python
# EnforcementConfig class has methods:
# - validate_input()
# - check_permissions()
# - verify_config()

# → Grouped into "Validation" story:
{
    "key": "STORY-ENFORCEMENTCONFIG-001",
    "title": "As a developer, I can validate EnforcementConfig data",
    "tasks": ["validate_input()", "check_permissions()", "verify_config()"],
    "acceptance": [
        "Validate Input works correctly (see contract examples)",
        "Check Permissions works correctly (see contract examples)",
        "Verify Config works correctly (see contract examples)"
    ],
    "contract": "contracts/enforcement-config.openapi.yaml",  # Examples stored here
    "story_points": 5,
    "value_points": 3
}
```

**Phase 4 & 5 Changes (GWT Elimination + Test Pattern Extraction)**:

- ❌ **BEFORE**: Verbose GWT format ("Given X, When Y, Then Z") - one per test function
- ✅ **AFTER Phase 4**: Simple text format ("Feature works correctly (see contract examples)")
- ✅ **AFTER Phase 5**: Limited to 1-3 high-level acceptance criteria per story, all detailed test patterns in OpenAPI contracts
- ✅ **Benefits**: 81% bundle size reduction (18MB → 3.4MB, 5.3x smaller), examples in OpenAPI contracts for Specmatic integration
- ✅ **Quality**: All test patterns preserved in contract files, no information loss

---

### Step 3: Feature Enhancement with Semgrep

After extracting features from AST, we enhance them with Semgrep findings:

```python
def _enhance_feature_with_semgrep(feature, semgrep_findings, file_path, class_name):
    """Enhance feature with Semgrep pattern detection results."""
    for finding in semgrep_findings:
        # API endpoint detection → +0.1 confidence, add "API" theme
        # Database model detection → +0.15 confidence, add "Database" theme
        # CRUD operation detection → +0.1 confidence, add to outcomes
        # Auth pattern detection → +0.1 confidence, add "Security" theme
        # Anti-pattern detection → -0.05 confidence, add to constraints
        # Security issues → -0.1 confidence, add to constraints
```

**Semgrep Enhancements**:

- **API Endpoints**: Adds `"Exposes API endpoints: GET /users, POST /users"` to outcomes
- **Database Models**: Adds `"Defines data models: UserModel, ProductModel"` to outcomes
- **CRUD Operations**: Adds `"Provides CRUD operations: CREATE user, GET user"` to outcomes
- **Code Quality**: Adds constraints like `"Code quality: Bare except clause detected - antipattern"`
- **Confidence Adjustments**: Framework patterns increase confidence, anti-patterns decrease it

---

### Step 5: Confidence Scoring (AST + Semgrep Evidence)

**Goal**: Determine how confident we are that this is a real feature (not noise), combining AST and Semgrep evidence.

```python
def _calculate_feature_confidence(node: ast.ClassDef, stories: list[Story]) -> float:
    score = 0.3  # Base score (30%)
    
    # Has docstring (+20%)
    if ast.get_docstring(node):
        score += 0.2
    
    # Has stories (+20%)
    if stories:
        score += 0.2
    
    # Has multiple stories (+20%)
    if len(stories) > 2:
        score += 0.2
    
    # Stories are well-documented (+10%)
    documented_stories = sum(1 for s in stories if s.acceptance and len(s.acceptance) > 1)
    if stories and documented_stories > len(stories) / 2:
        score += 0.1
    
    return min(score, 1.0)  # Cap at 100%
```

**Confidence Factors**:

| Factor | Weight | Rationale |
|--------|--------|-----------|
| **Base Score** | 30% | Every class starts with baseline |
| **Has Docstring** | +20% | Documented classes are more likely real features |
| **Has Stories** | +20% | Methods grouped into stories indicate functionality |
| **Multiple Stories** | +20% | More stories = more complete feature |
| **Well-Documented Stories** | +10% | Docstrings in methods indicate intentional design |

**Example**:

- `EnforcementConfig` with docstring + 3 well-documented stories → **0.9 confidence** (90%)
- `InternalHelper` with no docstring + 1 story → **0.5 confidence** (50%)

**Filtering**: Features below `--confidence` threshold (default 0.5) are excluded.

**Semgrep Confidence Enhancements** (Systematic Evidence-Based Scoring):

| Semgrep Finding | Confidence Adjustment | Rationale |
|----------------|----------------------|-----------|
| **API Endpoint Detected** | +0.1 | Framework patterns indicate real features |
| **Database Model Detected** | +0.15 | Data models are core features |
| **CRUD Operations Detected** | +0.1 | Complete CRUD indicates well-defined feature |
| **Auth Pattern Detected** | +0.1 | Security features are important |
| **Framework Patterns Detected** | +0.05 | Framework usage indicates intentional design |
| **Test Patterns Detected** | +0.1 | Tests indicate validated feature |
| **Anti-Pattern Detected** | -0.05 | Code quality issues reduce maturity |
| **Security Issue Detected** | -0.1 | Security vulnerabilities are critical |

**How It Works**:

1. **Evidence Extraction**: Semgrep findings are categorized into evidence flags (API endpoints, models, CRUD, etc.)
2. **Confidence Calculation**: Base AST confidence (0.3-0.9) is adjusted with Semgrep evidence weights
3. **Systematic Scoring**: Each pattern type has a documented weight, ensuring consistent confidence across features
4. **Quality Assessment**: Anti-patterns and security issues reduce confidence, indicating lower code maturity

**Example**:

- `UserService` with API endpoints + CRUD operations → **Base 0.6 + 0.1 (API) + 0.1 (CRUD) = 0.8 confidence**
- `BadService` with anti-patterns → **Base 0.6 - 0.05 (anti-pattern) = 0.55 confidence**

---

### Step 6: Story Points Calculation

**Goal**: Estimate complexity using **Fibonacci sequence** (1, 2, 3, 5, 8, 13, 21...)

```python
def _calculate_story_points(methods: list[ast.FunctionDef]) -> int:
    method_count = len(methods)
    
    # Count total lines
    total_lines = sum(len(ast.unparse(m).split("\n")) for m in methods)
    avg_lines = total_lines / method_count if method_count > 0 else 0
    
    # Heuristic: complexity based on count and size
    if method_count <= 2 and avg_lines < 20:
        base_points = 2  # Small
    elif method_count <= 5 and avg_lines < 40:
        base_points = 5  # Medium
    elif method_count <= 8:
        base_points = 8  # Large
    else:
        base_points = 13  # Extra Large
    
    # Return nearest Fibonacci number
    return min(FIBONACCI, key=lambda x: abs(x - base_points))
```

**Heuristic Table**:

| Methods | Avg Lines | Base Points | Fibonacci Result |
|---------|-----------|-------------|------------------|
| 1-2 | < 20 | 2 | **2** |
| 3-5 | < 40 | 5 | **5** |
| 6-8 | Any | 8 | **8** |
| 9+ | Any | 13 | **13** |

**Why Fibonacci?**

- ✅ Industry standard (Scrum/Agile)
- ✅ Non-linear (reflects uncertainty)
- ✅ Widely understood by teams

---

### Step 7: Value Points Calculation

**Goal**: Estimate **business value** (not complexity, but importance).

```python
def _calculate_value_points(methods: list[ast.FunctionDef], group_name: str) -> int:
    # CRUD operations are high value
    crud_groups = ["Create Operations", "Read Operations", "Update Operations", "Delete Operations"]
    if group_name in crud_groups:
        base_value = 8  # High business value
    
    # User-facing operations
    elif group_name in ["Processing", "Analysis", "Generation", "Comparison"]:
        base_value = 5  # Medium-high value
    
    # Developer/internal operations
    elif group_name in ["Validation", "Configuration"]:
        base_value = 3  # Medium value
    
    else:
        base_value = 3  # Default
    
    # Adjust for public API exposure
    public_count = sum(1 for m in methods if not m.name.startswith("_"))
    if public_count >= 3:
        base_value = min(base_value + 2, 13)
    
    return min(FIBONACCI, key=lambda x: abs(x - base_value))
```

**Value Hierarchy**:

| Group Type | Base Value | Rationale |
|------------|------------|-----------|
| **CRUD Operations** | 8 | Direct user value (create, read, update, delete) |
| **User-Facing** | 5 | Processing, analysis, generation - users see results |
| **Developer/Internal** | 3 | Validation, configuration - infrastructure |
| **Public API Bonus** | +2 | More public methods = higher exposure = more value |

---

### Step 8: Theme Detection from Imports

**Goal**: Identify what kind of application this is (API, CLI, Database, etc.).

```python
def _extract_themes_from_imports(tree: ast.AST) -> None:
    theme_keywords = {
        "fastapi": "API",
        "flask": "API",
        "django": "Web",
        "typer": "CLI",
        "click": "CLI",
        "pydantic": "Validation",
        "redis": "Caching",
        "postgres": "Database",
        "mysql": "Database",
        "asyncio": "Async",
        "pytest": "Testing",
        # ... more keywords
    }
    
    # Scan all imports
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Match keywords in import names
            for keyword, theme in theme_keywords.items():
                if keyword in import_name.lower():
                    self.themes.add(theme)
```

**Example**:

- `import typer` → Theme: **CLI**
- `import pydantic` → Theme: **Validation**
- `from fastapi import FastAPI` → Theme: **API**

---

## Why AI-First?

### ✅ Advantages of AI-First Approach

| Aspect | AI-First (CoPilot Mode) | AST-Based (CI/CD Mode) |
|-------|------------------------|------------------------|
| **Language Support** | ✅ All languages | ❌ Python only |
| **Semantic Understanding** | ✅ Understands business logic | ❌ Structure only |
| **Priorities** | ✅ Actual from code context | ⚠️ Generic (hardcoded) |
| **Constraints** | ✅ Actual from code/docs | ⚠️ Generic (hardcoded) |
| **Unknowns** | ✅ Actual from code analysis | ⚠️ Generic (hardcoded) |
| **Scenarios** | ✅ Actual from acceptance criteria | ⚠️ Generic (hardcoded) |
| **Spec-Kit Compatibility** | ✅ High-quality artifacts | ⚠️ Low-quality artifacts |
| **Bidirectional Sync** | ✅ Semantic preservation | ⚠️ Structure-only |

### When AST Fallback Is Used

AST-based analysis is used in **CI/CD mode** when:

- LLM is unavailable (no API access)
- Fast, deterministic analysis is required
- Offline analysis is needed
- Python-only codebase analysis is sufficient

**Trade-offs**:

- ✅ Fast and deterministic
- ✅ Works offline
- ❌ Python-only
- ❌ Generic content (hardcoded fallbacks)

---

## Accuracy and Limitations

### ✅ AI-First Approach (CoPilot Mode)

**What It Does Well**:

1. **Semantic Understanding**: Understands business logic and domain concepts
2. **Multi-language Support**: Works with Python, TypeScript, JavaScript, PowerShell, Go, Rust, etc.

3. **Semantic Extraction**: Extracts actual priorities, constraints, unknowns from code context
4. **High-quality Artifacts**: Generates Spec-Kit compatible artifacts with semantic content
5. **Bidirectional Sync**: Preserves semantics during Spec-Kit ↔ SpecFact sync

**Limitations**:

1. **Requires LLM Access**: Needs CoPilot API or IDE integration
2. **Variable Response Time**: Depends on LLM API response time
3. **Token Costs**: May incur API costs for large codebases
4. **Non-deterministic**: May produce slightly different results on repeated runs

### ⚠️ AST-Based Fallback (CI/CD Mode)

**What It Does Well**:

1. **Structural Analysis**: Classes, methods, imports are 100% accurate (AST parsing)
2. **Pattern Recognition**: CRUD, validation, processing patterns are well-defined
3. **Confidence Scoring**: Evidence-based (docstrings, stories, documentation)
4. **Deterministic**: Same code always produces same results
5. **Fast**: Analyzes thousands of lines in seconds
6. **Offline**: Works without API access

**Limitations**:

1. **Python-only**: Cannot analyze TypeScript, JavaScript, PowerShell, etc.

2. **Generic Content**: Produces generic priorities, constraints, unknowns (hardcoded fallbacks)
3. **No Semantic Understanding**: Cannot understand business logic or domain concepts
4. **Method Name Dependency**: If methods don't follow naming conventions, grouping may be less accurate
5. **Docstring Dependency**: Features/stories without docstrings have lower confidence
6. **False Positives**: Internal helper classes might be detected as features

---

## Real Example: EnforcementConfig

Let's trace how `EnforcementConfig` class becomes a feature:

```python
class EnforcementConfig:
    """Configuration for contract enforcement and quality gates."""
    
    def __init__(self, preset: EnforcementPreset):
        ...
    
    def should_block_deviation(self, severity: str) -> bool:
        ...
    
    def get_action(self, severity: str) -> EnforcementAction:
        ...
```

**Step-by-Step Analysis**:

1. **AST Parse** → Finds `EnforcementConfig` class with 3 methods
2. **Feature Extraction**:
   - Key: `FEATURE-ENFORCEMENTCONFIG`
   - Title: `Enforcement Config` (humanized)
   - Outcome: `"Configuration for contract enforcement and quality gates."`
3. **Method Grouping**:
   - `__init__()` → **Configuration** group
   - `should_block_deviation()` → **Validation** group (has "check" pattern)
   - `get_action()` → **Read Operations** group (has "get" pattern)
4. **Story Creation**:
   - Story 1: "As a developer, I can configure EnforcementConfig" (Configuration group)
   - Story 2: "As a developer, I can validate EnforcementConfig data" (Validation group)
   - Story 3: "As a user, I can view EnforcementConfig data" (Read Operations group)
5. **Confidence**: 0.9 (has docstring + 3 stories + well-documented)
6. **Story Points**: 5 (3 methods, medium complexity)
7. **Value Points**: 3 (Configuration group = medium value)

**Result**:

```yaml
feature:
  key: FEATURE-ENFORCEMENTCONFIG
  title: Enforcement Config
  confidence: 0.9
  stories:
    - key: STORY-ENFORCEMENTCONFIG-001
      title: As a developer, I can configure EnforcementConfig
      story_points: 2
      value_points: 3
      tasks: ["__init__()"]
    - key: STORY-ENFORCEMENTCONFIG-002
      title: As a developer, I can validate EnforcementConfig data
      story_points: 2
      value_points: 3
      tasks: ["should_block_deviation()"]
    - key: STORY-ENFORCEMENTCONFIG-003
      title: As a user, I can view EnforcementConfig data
      story_points: 2
      value_points: 5
      tasks: ["get_action()"]
```

---

## Validation and Quality Assurance

### Built-in Validations

1. **Plan Bundle Schema**: Generated plans are validated against JSON schema
2. **Confidence Threshold**: Low-confidence features are filtered
3. **AST Error Handling**: Invalid Python files are skipped gracefully
4. **File Filtering**: Test files and dependencies are excluded

### How to Improve Accuracy

1. **Add Docstrings**: Increases confidence scores
2. **Use Descriptive Names**: Follow naming conventions (CRUD patterns)
3. **Group Related Methods**: Co-locate related functionality in same class
4. **Adjust Confidence Threshold**: Use `--confidence 0.7` for stricter filtering

---

## Performance

### Benchmarks

| Repository Size | Files | Time | Throughput | Notes |
|----------------|-------|------|------------|-------|
| **Small** (10 files) | 10 | ~10-30s | ~0.3-1 files/sec | AST + Semgrep analysis |
| **Medium** (50 files) | 50 | ~1-2 min | ~0.4-0.8 files/sec | AST + Semgrep analysis |
| **Large** (100+ files) | 100+ | 2-3 min | ~0.5-0.8 files/sec | AST + Semgrep analysis |
| **Large with Contracts** (100+ files) | 100+ | 15-30+ min | Varies | With contract extraction, graph analysis, and parallel processing (8 workers) |

**SpecFact CLI on itself**: 19 files in ~30-60 seconds = **~0.3-0.6 files/second** (AST + Semgrep analysis)

**Note**:

- **Basic analysis** (AST + Semgrep): Takes **2-3 minutes** for large codebases (100+ files) even without contract extraction
- **With contract extraction** (default in `import from-code`): The process uses parallel workers to extract OpenAPI contracts, relationships, and graph dependencies. For large codebases, this can take **15-30+ minutes** even with 8 parallel workers

### Bundle Size Optimization (2025-11-30)

- ✅ **81% Reduction**: 18MB → 3.4MB (5.3x smaller) via test pattern extraction to OpenAPI contracts
- ✅ **Acceptance Criteria**: Limited to 1-3 high-level items per story (detailed examples in contract files)
- ✅ **Quality Preserved**: All test patterns preserved in contract files (no information loss)
- ✅ **Specmatic Integration**: Examples in OpenAPI format enable contract testing

### Optimization Opportunities

1. ✅ **Parallel Processing**: Contract extraction uses 8 parallel workers (implemented)
2. ✅ **Interruptible Operations**: All parallel operations support Ctrl+C for immediate cancellation (implemented)
3. **Caching**: Cache AST parsing results (future enhancement)
4. **Incremental Analysis**: Only analyze changed files (future enhancement)

---

## Conclusion

The `code2spec` analysis is **deterministic, fast, and transparent** because it uses:

1. ✅ **Python AST** - Built-in, reliable parsing
2. ✅ **Pattern Matching** - Simple, interpretable heuristics
3. ✅ **Confidence Scoring** - Evidence-based quality metrics
4. ✅ **Fibonacci Estimation** - Industry-standard story/value points

**No AI required** - just solid engineering principles and proven algorithms.

---

## Further Reading

- [Python AST Documentation](https://docs.python.org/3/library/ast.html)
- [Scrum Story Points](https://www.scrum.org/resources/blog/what-are-story-points)
- [Dogfooding Example](../examples/dogfooding-specfact-cli.md) - See it in action

---

**Questions or improvements?** Open an issue or PR on GitHub!
