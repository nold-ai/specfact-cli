# Contract Extraction Performance Analysis

## Current Performance Bottlenecks

### 1. **AST Parsing Overhead (Primary Bottleneck)**

**Problem**: Each feature processes its files independently, parsing the same files multiple times if they belong to multiple features.

**Current Flow**:
```
For each feature (320 features):
  For each file in feature.source_tracking.implementation_files:
    - Open file (I/O)
    - Read entire file content (I/O)
    - Parse with ast.parse() (CPU-intensive, ~50-200ms per file)
    - Traverse AST multiple times (CPU-intensive)
```

**Impact**: 
- For SQLAlchemy with 320 features sharing ~300 files:
  - Files are parsed **multiple times** (once per feature that references them)
  - If average file is referenced by 2-3 features: **2-3x redundant parsing**
  - Large files (1000+ lines) take 100-500ms to parse

**Example**: 
- File `sqlalchemy/core/engine.py` (5000 lines) parsed 5 times = 2.5 seconds wasted
- 300 files × 2.5 average parses = 750 redundant parses
- At 100ms per parse = **75 seconds wasted on redundant parsing**

### 2. **Multiple AST Traversals**

**Problem**: Each file is traversed multiple times:
1. First pass: Extract Pydantic models and router instances
2. Second pass: Extract endpoints from functions/classes
3. Additional passes for nested structures

**Impact**: 
- Each traversal visits every node in the AST
- For large files (1000+ lines), this adds 50-100ms per traversal
- Total: 150-300ms per file just for traversal

### 3. **No File-Level Caching**

**Problem**: 
- Files are read and parsed fresh for each feature
- No shared cache between features
- Same file content read multiple times from disk

**Impact**:
- Redundant file I/O operations
- Redundant AST parsing
- Memory overhead from duplicate AST trees

### 4. **Complex AST Analysis**

**Problem**: The extraction logic performs deep AST analysis:
- Pydantic model schema extraction (recursive type analysis)
- Decorator pattern matching
- Router prefix resolution
- Path parameter extraction
- Type hint analysis

**Impact**:
- Each operation is CPU-intensive
- For complex files, this can take 200-500ms per file

## Optimization Opportunities

### **High Impact Optimizations**

#### 1. **File-Level AST Caching** (Estimated: 3-5x speedup)

**Strategy**: Parse each file once and cache the AST, reuse for all features.

**Implementation**:
```python
class OpenAPIExtractor:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path.resolve()
        self._lock = Lock()
        self._ast_cache: dict[Path, ast.AST] = {}  # File path -> AST
        self._file_content_cache: dict[Path, str] = {}  # File path -> content
    
    def _get_or_parse_file(self, file_path: Path) -> ast.AST:
        """Get cached AST or parse and cache."""
        if file_path in self._ast_cache:
            return self._ast_cache[file_path]
        
        # Read and parse
        with file_path.open(encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        
        # Cache
        self._ast_cache[file_path] = tree
        self._file_content_cache[file_path] = content
        
        return tree
```

**Benefits**:
- Parse each file only once, regardless of how many features reference it
- For 300 files referenced by 320 features: **300 parses instead of 750+**
- Estimated time savings: **45-75 seconds** for SQLAlchemy

#### 2. **Batch Processing at File Level** (Estimated: 2-3x speedup)

**Strategy**: Process files once, then assign results to features.

**Current**: Feature → Files → Parse → Extract
**Optimized**: Files → Parse → Extract → Assign to Features

**Implementation**:
```python
def _extract_contracts_optimized(features_with_files, repo, contracts_dir):
    # Step 1: Collect all unique files
    file_to_features: dict[Path, list[Feature]] = {}
    for feature in features_with_files:
        for impl_file in feature.source_tracking.implementation_files:
            file_path = repo / impl_file
            if file_path not in file_to_features:
                file_to_features[file_path] = []
            file_to_features[file_path].append(feature)
    
    # Step 2: Process each file once
    extractor = OpenAPIExtractor(repo)
    file_results: dict[Path, dict[str, Any]] = {}
    
    for file_path, features in file_to_features.items():
        # Parse and extract once
        openapi_spec = extractor._extract_from_file(file_path)
        file_results[file_path] = openapi_spec
    
    # Step 3: Merge results into features
    for feature in features_with_files:
        feature_spec = {"paths": {}, "components": {"schemas": {}}}
        for impl_file in feature.source_tracking.implementation_files:
            file_path = repo / impl_file
            if file_path in file_results:
                # Merge file results into feature spec
                merge_openapi_specs(feature_spec, file_results[file_path])
```

**Benefits**:
- Process each file exactly once
- Better parallelization (can parallelize at file level)
- Reduced memory overhead

#### 3. **Early Exit for Non-API Files** (Estimated: 1.5-2x speedup)

**Strategy**: Quickly detect if a file has API endpoints before deep analysis.

**Implementation**:
```python
def _has_api_endpoints(file_path: Path) -> bool:
    """Quick check if file likely has API endpoints."""
    with file_path.open(encoding="utf-8") as f:
        content = f.read(4096)  # Read first 4KB only
    
    # Quick regex check for common patterns
    api_patterns = [
        r'@(app|router)\.(get|post|put|delete|patch)',
        r'@app\.route\(',
        r'APIRouter\(',
        r'FastAPI\(',
    ]
    
    return any(re.search(pattern, content) for pattern in api_patterns)
```

**Benefits**:
- Skip deep AST analysis for files without API endpoints
- For SQLAlchemy: ~70% of files are non-API (models, utilities)
- Estimated time savings: **30-50 seconds**

#### 4. **Optimize AST Traversal** (Estimated: 1.3-1.5x speedup)

**Strategy**: Combine multiple passes into a single pass.

**Current**: 2-3 separate traversals
**Optimized**: Single traversal with state tracking

**Implementation**:
```python
def _extract_from_file_single_pass(self, file_path: Path) -> dict[str, Any]:
    """Single-pass extraction combining all operations."""
    tree = self._get_or_parse_file(file_path)
    
    # State tracking
    pydantic_models = {}
    router_prefixes = {}
    router_tags = {}
    endpoints = []
    
    # Single traversal
    for node in ast.walk(tree):  # More efficient than iter_child_nodes
        if isinstance(node, ast.ClassDef):
            if self._is_pydantic_model(node):
                # Extract model
                pydantic_models[node.name] = self._extract_pydantic_model_schema(node)
            # Check for router
            # ... router detection ...
        
        elif isinstance(node, ast.FunctionDef):
            # Extract endpoints
            # ... endpoint extraction ...
    
    # Build OpenAPI spec from collected data
    return build_openapi_spec(pydantic_models, endpoints, router_prefixes)
```

**Benefits**:
- Single AST walk instead of multiple
- Better cache locality
- Reduced overhead

### **Medium Impact Optimizations**

#### 5. **Parallelize at File Level Instead of Feature Level**

**Current**: Parallelize features (320 tasks)
**Optimized**: Parallelize files (300 tasks, but each faster)

**Benefits**:
- Better load balancing (files vary less in size than features)
- Fewer tasks = less overhead
- Better cache utilization

#### 6. **Incremental Processing**

**Strategy**: Only re-process files that changed (based on hash).

**Implementation**:
- Store file hash with cached AST
- On next run, check hash before using cache
- Only re-parse changed files

**Benefits**:
- For incremental imports: only process changed files
- Massive speedup for small changes

### **Low Impact Optimizations**

#### 7. **Lazy File Reading**

Only read file content when needed (after quick check).

#### 8. **Optimize Pydantic Model Extraction**

Cache schema extraction results.

#### 9. **Use Compiled Regex Patterns**

Pre-compile regex patterns used in extraction.

## Recommended Implementation Order

1. **Phase 1 (Quick Win)**: File-level AST caching (#1)
   - Estimated effort: 2-3 hours
   - Estimated speedup: 3-5x
   - Low risk, high reward

2. **Phase 2 (Medium Effort)**: Early exit for non-API files (#3)
   - Estimated effort: 1-2 hours
   - Estimated speedup: 1.5-2x
   - Low risk

3. **Phase 3 (Larger Refactor)**: Batch processing (#2) + Single-pass traversal (#4)
   - Estimated effort: 4-6 hours
   - Estimated speedup: 2-3x additional
   - Higher risk, requires testing

## Expected Overall Improvement

**Current**: ~8 minutes for 12% (320 features)
**Projected**: ~2-3 minutes for 100% (320 features)

**Breakdown**:
- File-level caching: 3-5x → ~2-3 minutes
- Early exit: 1.5-2x → ~1-2 minutes
- Single-pass traversal: 1.3-1.5x → ~45-90 seconds
- **Combined**: **5-10x speedup** → **~45-90 seconds total**

## Implementation Notes

- Maintain thread-safety for parallel processing
- Ensure cache invalidation on file changes
- Add metrics to track cache hit rates
- Consider memory limits for large codebases
