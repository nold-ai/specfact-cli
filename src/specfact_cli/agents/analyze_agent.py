"""
Analyze Agent - AI-first brownfield analysis with semantic understanding.

This module provides the AnalyzeAgent for brownfield code analysis using
AI (LLM) to understand codebase semantics and generate Spec-Kit/SpecFact
compatible artifacts. This replaces the AST-based approach for better
multi-language support and semantic understanding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.agents.base import AgentMode
from specfact_cli.models.plan import Idea, Metadata, PlanBundle, Product


class AnalyzeAgent(AgentMode):
    """
    AI-first brownfield analysis agent with semantic understanding.

    Provides enhanced prompts for brownfield analysis operations using
    AI (LLM) to understand codebase semantics and generate Spec-Kit/SpecFact
    compatible artifacts. This approach enables:
    - Multi-language support (Python, TypeScript, JavaScript, PowerShell, etc.)
    - Semantic understanding (priorities, constraints, unknowns, scenarios)
    - High-quality Spec-Kit artifact generation
    - Proper bidirectional sync with semantic preservation

    Falls back to AST-based analysis in CI/CD mode when LLM is unavailable.
    """

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: isinstance(result, str) and bool(result), "Prompt must be non-empty string")
    def generate_prompt(self, command: str, context: dict[str, Any] | None = None) -> str:
        """
        Generate enhanced prompt for brownfield analysis.

        This prompt instructs the AI IDE's LLM to:
        1. Understand the codebase semantically
        2. Call the SpecFact CLI for structured analysis
        3. Enhance results with semantic understanding

        Args:
            command: CLI command being executed (e.g., "import from-code")
            context: Context dictionary with current file, selection, workspace

        Returns:
            Enhanced prompt optimized for AI IDE (Cursor, CoPilot, etc.)

        Examples:
            >>> agent = AnalyzeAgent()
            >>> prompt = agent.generate_prompt("import from-code", {"current_file": "src/main.py"})
            >>> "specfact import from-code" in prompt.lower()
            True
        """
        if context is None:
            context = {}

        current_file = context.get("current_file", "")
        selection = context.get("selection", "")
        workspace = context.get("workspace", "")

        # Load codebase context for AI analysis
        repo_path = Path(workspace) if workspace else Path(".")
        codebase_context = self._load_codebase_context(repo_path)

        prompt = f"""
You are helping analyze a codebase and generate a SpecFact plan bundle using AI-first semantic understanding.

## Repository Context

- **Directory structure**: {codebase_context.get("structure", "N/A")}
- **Code files**: {len(codebase_context.get("files", []))} files analyzed
- **Languages detected**: {", ".join({f.suffix for f in [Path(f) for f in codebase_context.get("files", [])[:20]]})}
- **Dependencies**: {", ".join(codebase_context.get("dependencies", [])[:10])}
- **Current file**: {current_file or "None"}
- **Selection**: {selection or "None"}

## Your Task

### Step 1: Semantic Understanding (Use Your AI Capabilities)

Use your AI capabilities to understand the codebase:

1. **Read and understand** the repository structure and codebase
2. **Identify features** from business logic (not just class structure)
3. **Extract user stories** from code intent (not just method patterns)
4. **Infer priorities** from code context (comments, docs, structure, usage patterns)
5. **Identify constraints** from code/docs (technical limitations, requirements)
6. **Identify unknowns** from code analysis (missing information, unclear decisions)
7. **Generate scenarios** from acceptance criteria (Primary, Alternate, Exception, Recovery)
8. **Extract technology stack** from dependencies and imports

### Step 2: Generate Plan Bundle Directly

**Generate a PlanBundle structure directly** using your semantic understanding:

1. **Create PlanBundle structure** (as a Python dict matching the Pydantic model):
   - `version: "1.0"`
   - `idea` with `title` set to the provided plan name (from `--name` argument) instead of "Unknown Project"
   - `product` with `themes: []` and `releases: []`
   - `features: []` with Feature objects containing:
     - `key`, `title`, `outcomes`, `acceptance`, `constraints`
     - `confidence`, `draft`, `stories: []`
   - `metadata` with `stage: "draft"`

2. **Convert to YAML** using proper YAML formatting (2-space indentation, no flow style)

3. **Write to file**: `.specfact/plans/<name>-<timestamp>.bundle.yaml`
   - If no name provided, ask user for a meaningful plan name (e.g., "API Client v2", "User Authentication", "Payment Processing")
   - Name will be automatically sanitized (lowercased, spaces/special chars removed) for filesystem persistence
   - Use ISO 8601 timestamp format: `YYYY-MM-DDTHH-MM-SS`
   - Ensure directory exists: `.specfact/plans/`
   - Example: `.specfact/plans/api-client-v2.2025-11-04T22-17-22.bundle.yaml`

### Step 3: Present Results

**Present the generated plan bundle** to the user:

- Plan bundle location and summary
- Feature/story counts with confidence scores
- Semantic insights and recommendations

## Key Principles

- **Semantic understanding first**: Use AI to understand business logic and intent
- **Direct generation**: Generate the plan bundle directly as YAML, don't call the CLI
- **Multi-language support**: Works with Python, TypeScript, JavaScript, PowerShell, etc.
- **Spec-Kit compatibility**: Generate artifacts that work with `/speckit.analyze`, `/speckit.implement`, `/speckit.checklist`

Focus on semantic understanding, not just structural parsing. Generate the plan bundle directly using your AI capabilities.
"""
        return prompt.strip()

    @beartype
    @require(lambda command: bool(command), "Command must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Result must be a dictionary")
    def execute(
        self, command: str, args: dict[str, Any] | None = None, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute brownfield analysis with enhanced prompts.

        Args:
            command: CLI command being executed (e.g., "import from-code")
            args: Command arguments (e.g., {"repo": ".", "confidence": 0.7})
            context: Context dictionary with current file, selection, workspace

        Returns:
            Command result with enhanced output

        Examples:
            >>> agent = AnalyzeAgent()
            >>> result = agent.execute("import from-code", {"repo": "."}, {"current_file": "src/main.py"})
            >>> isinstance(result, dict)
            True
        """
        if args is None:
            args = {}
        if context is None:
            context = {}

        # Generate enhanced prompt
        prompt = self.generate_prompt(command, context)

        # For Phase 4.1, return structured result with prompt
        # In Phase 4.2+, this will route to actual command execution with agent mode
        return {
            "type": "analysis",
            "command": command,
            "prompt": prompt,
            "args": args,
            "context": context,
            "enhanced": True,
        }

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Result must be a dictionary")
    def inject_context(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Inject context information specific to analysis operations.

        Args:
            context: Basic context dictionary (can be None)

        Returns:
            Enhanced context with analysis-specific information

        Examples:
            >>> agent = AnalyzeAgent()
            >>> enhanced = agent.inject_context({"current_file": "src/main.py"})
            >>> isinstance(enhanced, dict)
            True
        """
        enhanced = super().inject_context(context)

        # Add workspace structure if workspace is available
        if enhanced.get("workspace"):
            workspace_path = Path(enhanced["workspace"])
            if workspace_path.exists() and workspace_path.is_dir():  # type: ignore[reportUnknownMemberType]
                # Add workspace structure information
                src_dirs = list(workspace_path.glob("src/**"))
                test_dirs = list(workspace_path.glob("tests/**"))
                enhanced["workspace_structure"] = {
                    "src_dirs": [str(d) for d in src_dirs[:10]],  # Limit to first 10
                    "test_dirs": [str(d) for d in test_dirs[:10]],
                }

        return enhanced

    @beartype
    @require(lambda repo_path: repo_path.exists() and repo_path.is_dir(), "Repo path must exist and be directory")  # type: ignore[reportUnknownMemberType]
    @ensure(lambda result: isinstance(result, dict), "Result must be a dictionary")
    def _load_codebase_context(self, repo_path: Path) -> dict[str, Any]:
        """
        Load codebase context for AI analysis.

        Args:
            repo_path: Path to repository root

        Returns:
            Dictionary with codebase context (structure, files, dependencies, summary)
        """
        context: dict[str, Any] = {
            "structure": [],
            "files": [],
            "dependencies": [],
            "summary": "",
        }

        # Load directory structure
        try:
            src_dirs = list(repo_path.glob("src/**")) if (repo_path / "src").exists() else []  # type: ignore[reportUnknownMemberType]
            test_dirs = list(repo_path.glob("tests/**")) if (repo_path / "tests").exists() else []  # type: ignore[reportUnknownMemberType]
            context["structure"] = {
                "src_dirs": [str(d.relative_to(repo_path)) for d in src_dirs[:20]],
                "test_dirs": [str(d.relative_to(repo_path)) for d in test_dirs[:20]],
            }
        except Exception:
            context["structure"] = {}

        # Load code files (all languages)
        code_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".ps1", ".psm1", ".go", ".rs", ".java", ".kt"}
        code_files: list[Path] = []
        for ext in code_extensions:
            code_files.extend(list(repo_path.rglob(f"*{ext}")))

        # Filter out common ignore patterns
        ignore_patterns = {
            "__pycache__",
            ".git",
            "venv",
            ".venv",
            "node_modules",
            ".pytest_cache",
            "dist",
            "build",
            ".eggs",
        }

        filtered_files = [
            f
            for f in code_files[:100]  # Limit to first 100 files
            if not any(pattern in str(f) for pattern in ignore_patterns)
        ]

        context["files"] = [str(f.relative_to(repo_path)) for f in filtered_files]

        # Load dependencies
        dependency_files = [
            repo_path / "requirements.txt",
            repo_path / "package.json",
            repo_path / "pom.xml",
            repo_path / "go.mod",
            repo_path / "Cargo.toml",
            repo_path / "pyproject.toml",
        ]

        dependencies: list[str] = []
        for dep_file in dependency_files:
            if dep_file.exists():  # type: ignore[reportUnknownMemberType]
                try:
                    content = dep_file.read_text(encoding="utf-8")[:500]  # First 500 chars
                    dependencies.append(f"{dep_file.name}: {content[:100]}...")
                except Exception:
                    pass

        context["dependencies"] = dependencies

        # Generate summary
        context["summary"] = f"""
Repository: {repo_path.name}
Total code files: {len(filtered_files)}
Languages detected: {", ".join({f.suffix for f in filtered_files[:20]})}
Dependencies: {len(dependencies)} dependency files found
"""

        return context

    @beartype
    @require(lambda repo_path: repo_path.exists() and repo_path.is_dir(), "Repo path must exist and be directory")  # type: ignore[reportUnknownMemberType]
    @require(lambda confidence: 0.0 <= confidence <= 1.0, "Confidence must be 0.0-1.0")
    @require(lambda plan_name: plan_name is None or isinstance(plan_name, str), "Plan name must be None or str")
    @ensure(lambda result: isinstance(result, PlanBundle), "Result must be PlanBundle")
    def analyze_codebase(self, repo_path: Path, confidence: float = 0.5, plan_name: str | None = None) -> PlanBundle:
        """
        Analyze codebase using AI-first approach with semantic understanding.

        **Pragmatic Approach**: This method is designed for AI IDE integration (Cursor, CoPilot, etc.).
        The AI IDE's native LLM will:
        1. Understand the codebase semantically (using the prompt from `generate_prompt()`)
        2. Call the SpecFact CLI (`specfact import from-code`) for structured analysis
        3. Enhance results with semantic understanding

        This avoids the need for:
        - Separate LLM API setup (langchain, OpenAI API keys, etc.)
        - Additional API costs
        - Complex integration code

        The CLI handles:
        - File I/O (reading code, writing YAML/Markdown)
        - Structured data generation (plan bundle format)
        - Validation (schema checking, error handling)
        - Mode detection (AI-first vs AST-based fallback)

        Args:
            repo_path: Path to repository root
            confidence: Minimum confidence score (0.0-1.0)
            plan_name: Custom plan name (will be used for idea.title, optional)

        Returns:
            PlanBundle with semantic understanding

        Note:
            In CoPilot mode, the AI IDE will execute the CLI and parse results.
            In CI/CD mode, the command falls back to AST-based CodeAnalyzer.
        """
        # Load codebase context for AI prompt generation
        _context = self._load_codebase_context(repo_path)

        # Generate AI analysis prompt (instructs AI IDE to use CLI)
        agent_context = {
            "workspace": str(repo_path),
            "current_file": None,
            "selection": None,
        }
        enhanced_context = self.inject_context(agent_context)
        _prompt = self.generate_prompt("import from-code", enhanced_context)

        # In AI IDE mode, the AI will:
        # 1. Use the prompt to understand the codebase semantically
        # 2. Call `specfact import from-code` with appropriate arguments
        # 3. Parse the CLI output and enhance with semantic understanding
        # 4. Present results to the user

        # For now, return a placeholder plan bundle
        # The actual analysis will be done by the AI IDE calling the CLI
        # Use plan name if provided, otherwise use repo name, otherwise fallback
        if plan_name:
            # Use the plan name (already sanitized, but humanize for title)
            title = plan_name.replace("_", " ").replace("-", " ").title()
        else:
            repo_name = repo_path.name or "Unknown Project"
            title = repo_name.replace("_", " ").replace("-", " ").title()

        idea = Idea(
            title=title,
            narrative=f"Auto-derived plan from brownfield analysis of {title}",
            metrics=None,
        )

        product = Product(
            themes=["Core"],
            releases=[],
        )

        return PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=[],
            metadata=Metadata(stage="draft", promoted_at=None, promoted_by=None),
            clarifications=None,
        )
