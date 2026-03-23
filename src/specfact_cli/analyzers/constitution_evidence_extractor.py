"""Constitution evidence extractor for extracting evidence-based constitution checklist from code patterns.

Extracts evidence from code patterns to determine PASS/FAIL status for Articles VII, VIII, and IX
of the Spec-Kit constitution, generating rationale based on concrete evidence from the codebase.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


def _framework_match_for_token(
    token: str,
    framework_imports: dict[str, list[str]],
    rel_path: str,
) -> tuple[set[str], list[str]]:
    found: set[str] = set()
    evidence: list[str] = []
    for framework, patterns in framework_imports.items():
        if not any(pattern.startswith(token) for pattern in patterns):
            continue
        found.add(framework)
        evidence.append(f"Framework '{framework}' detected in {rel_path}")
    return found, evidence


def _viii_class_abstraction_layers(class_node: ast.ClassDef, rel_path: str) -> tuple[int, list[str]]:
    layers = 0
    evidence: list[str] = []
    for base in class_node.bases:
        if isinstance(base, ast.Name) and ("Model" in base.id or "Base" in base.id):
            layers += 1
            evidence.append(f"ORM pattern detected in {rel_path}: {base.id}")
    return layers, evidence


def _ix_decorator_hits(decorator: ast.expr, lineno: int, rel_path: str) -> tuple[int, list[str]]:
    if isinstance(decorator, ast.Name):
        name = decorator.id
        if name in ("require", "ensure", "invariant", "beartype"):
            return 1, [f"Contract decorator '@{name}' found in {rel_path}:{lineno}"]
        return 0, []
    if (
        isinstance(decorator, ast.Attribute)
        and isinstance(decorator.value, ast.Name)
        and decorator.value.id == "icontract"
    ):
        return 1, [
            f"Contract decorator '@icontract.{decorator.attr}' found in {rel_path}:{lineno}",
        ]
    return 0, []


def _ix_function_metrics(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    rel_path: str,
) -> tuple[int, int, int, list[str]]:
    contract_decorators = 0
    type_hinted = 1 if node.returns is not None else 0
    evidence: list[str] = []
    for decorator in node.decorator_list:
        c, ev = _ix_decorator_hits(decorator, node.lineno, rel_path)
        contract_decorators += c
        evidence.extend(ev)
    return contract_decorators, type_hinted, 1, evidence


def _ix_pydantic_metrics(class_node: ast.ClassDef, rel_path: str) -> tuple[int, list[str]]:
    pydantic_models = 0
    evidence: list[str] = []
    for base in class_node.bases:
        if (isinstance(base, ast.Name) and ("BaseModel" in base.id or "Pydantic" in base.id)) or (
            isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) and base.value.id == "pydantic"
        ):
            pydantic_models += 1
            evidence.append(f"Pydantic model detected in {rel_path}: {class_node.name}")
    return pydantic_models, evidence


class ConstitutionEvidenceExtractor:
    """
    Extracts evidence-based constitution checklist from code patterns.

    Analyzes code patterns to determine PASS/FAIL status for:
    - Article VII (Simplicity): Project structure, directory depth, file organization
    - Article VIII (Anti-Abstraction): Framework usage, abstraction layers
    - Article IX (Integration-First): Contract patterns, API definitions, type hints

    Generates evidence-based status (PASS/FAIL) with rationale, avoiding PENDING status.
    """

    # Framework detection patterns
    FRAMEWORK_IMPORTS = {
        "django": ["django", "django.db", "django.contrib"],
        "flask": ["flask", "flask_sqlalchemy", "flask_restful"],
        "fastapi": ["fastapi", "fastapi.routing", "fastapi.middleware"],
        "sqlalchemy": ["sqlalchemy", "sqlalchemy.orm", "sqlalchemy.ext"],
        "pydantic": ["pydantic", "pydantic.v1", "pydantic.v2"],
        "tortoise": ["tortoise", "tortoise.models", "tortoise.fields"],
        "peewee": ["peewee"],
        "sqlmodel": ["sqlmodel"],
    }

    # Contract decorator patterns
    CONTRACT_DECORATORS = ["@icontract", "@require", "@ensure", "@invariant", "@beartype"]

    # Thresholds for Article VII (Simplicity)
    MAX_DIRECTORY_DEPTH = 4  # PASS if depth <= 4, FAIL if depth > 4
    MAX_FILES_PER_DIRECTORY = 20  # PASS if files <= 20, FAIL if files > 20

    # Thresholds for Article VIII (Anti-Abstraction)
    MAX_ABSTRACTION_LAYERS = 2  # PASS if layers <= 2, FAIL if layers > 2

    # Thresholds for Article IX (Integration-First)
    MIN_CONTRACT_COVERAGE = 0.1  # PASS if >= 10% of functions have contracts, FAIL if < 10%

    @beartype
    def __init__(self, repo_path: Path) -> None:
        """
        Initialize constitution evidence extractor.

        Args:
            repo_path: Path to repository root for analysis
        """
        self.repo_path = Path(repo_path)

    def _scan_viii_python_file(self, repo_path: Path, py_file: Path) -> tuple[set[str], int, int, list[str]] | None:
        if py_file.name.startswith(".") or "__pycache__" in str(py_file):
            return None
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            return None

        frameworks_local: set[str] = set()
        abstraction_layers = 0
        total_imports = 0
        evidence_local: list[str] = []
        rel = str(py_file.relative_to(repo_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    total_imports += 1
                    fw, ev = _framework_match_for_token(
                        alias.name.split(".")[0],
                        self.FRAMEWORK_IMPORTS,
                        rel,
                    )
                    frameworks_local.update(fw)
                    evidence_local.extend(ev)
            elif isinstance(node, ast.ImportFrom) and node.module:
                total_imports += 1
                fw, ev = _framework_match_for_token(
                    node.module.split(".")[0],
                    self.FRAMEWORK_IMPORTS,
                    rel,
                )
                frameworks_local.update(fw)
                evidence_local.extend(ev)
            elif isinstance(node, ast.ClassDef):
                layers, ev = _viii_class_abstraction_layers(node, rel)
                abstraction_layers += layers
                evidence_local.extend(ev)

        return frameworks_local, abstraction_layers, total_imports, evidence_local

    def _scan_ix_python_file(self, repo_path: Path, py_file: Path) -> tuple[int, int, int, int, list[str]] | None:
        if py_file.name.startswith(".") or "__pycache__" in str(py_file):
            return None
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            return None

        contract_decorators_found = 0
        functions_with_type_hints = 0
        total_functions = 0
        pydantic_models = 0
        evidence_local: list[str] = []
        rel = str(py_file.relative_to(repo_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                c_dec, fn_hints, fn_total, ev = _ix_function_metrics(node, rel)
                contract_decorators_found += c_dec
                functions_with_type_hints += fn_hints
                total_functions += fn_total
                evidence_local.extend(ev)
            elif isinstance(node, ast.ClassDef):
                p_cnt, ev = _ix_pydantic_metrics(node, rel)
                pydantic_models += p_cnt
                evidence_local.extend(ev)

        return (
            contract_decorators_found,
            functions_with_type_hints,
            total_functions,
            pydantic_models,
            evidence_local,
        )

    @beartype
    @require(
        lambda repo_path: repo_path is None or (isinstance(repo_path, Path) and repo_path.exists()),
        "Repository path must exist if provided",
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_article_vii_evidence(self, repo_path: Path | None = None) -> dict[str, Any]:
        """
        Extract Article VII (Simplicity) evidence from project structure.

        Analyzes:
        - Directory depth (shallow = PASS, deep = FAIL)
        - Files per directory (few = PASS, many = FAIL)
        - File naming patterns (consistent = PASS, inconsistent = FAIL)

        Args:
            repo_path: Path to repository (default: self.repo_path)

        Returns:
            Dictionary with status, rationale, and evidence
        """
        if repo_path is None:
            repo_path = self.repo_path

        repo_path = Path(repo_path)
        if not repo_path.exists():
            return {
                "status": "FAIL",
                "rationale": "Repository path does not exist",
                "evidence": [],
            }

        # Analyze directory structure
        max_depth = 0
        max_files_per_dir = 0
        total_dirs = 0
        total_files = 0
        evidence: list[str] = []

        def analyze_directory(path: Path, depth: int = 0) -> None:
            """Recursively analyze directory structure."""
            nonlocal max_depth, max_files_per_dir, total_dirs, total_files

            if depth > max_depth:
                max_depth = depth

            # Count files in this directory (excluding hidden and common ignore patterns)
            files = [
                f
                for f in path.iterdir()
                if f.is_file()
                and not f.name.startswith(".")
                and f.suffix in (".py", ".md", ".yaml", ".yml", ".toml", ".json")
            ]
            file_count = len(files)

            if file_count > max_files_per_dir:
                max_files_per_dir = file_count
                evidence.append(f"Directory {path.relative_to(repo_path)} has {file_count} files")

            total_dirs += 1
            total_files += file_count

            # Recurse into subdirectories (limit depth to avoid infinite recursion)
            if depth < 10:  # Safety limit
                for subdir in path.iterdir():
                    if (
                        subdir.is_dir()
                        and not subdir.name.startswith(".")
                        and subdir.name not in ("__pycache__", "node_modules", ".git")
                    ):
                        analyze_directory(subdir, depth + 1)

        # Start analysis from repo root
        analyze_directory(repo_path, 0)

        # Determine status based on thresholds
        depth_pass = max_depth <= self.MAX_DIRECTORY_DEPTH
        files_pass = max_files_per_dir <= self.MAX_FILES_PER_DIRECTORY

        if depth_pass and files_pass:
            status = "PASS"
            rationale = (
                f"Project has simple structure (max depth: {max_depth}, max files per directory: {max_files_per_dir})"
            )
        else:
            status = "FAIL"
            issues: list[str] = []
            if not depth_pass:
                issues.append(
                    f"deep directory structure (max depth: {max_depth}, threshold: {self.MAX_DIRECTORY_DEPTH})"
                )
            if not files_pass:
                issues.append(
                    f"many files per directory (max: {max_files_per_dir}, threshold: {self.MAX_FILES_PER_DIRECTORY})"
                )
            rationale = f"Project violates simplicity: {', '.join(issues)}"

        return {
            "status": status,
            "rationale": rationale,
            "evidence": evidence[:5],  # Limit to top 5 evidence items
            "max_depth": max_depth,
            "max_files_per_dir": max_files_per_dir,
            "total_dirs": total_dirs,
            "total_files": total_files,
        }

    @beartype
    @require(
        lambda repo_path: repo_path is None or (isinstance(repo_path, Path) and repo_path.exists()),
        "Repository path must exist if provided",
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_article_viii_evidence(self, repo_path: Path | None = None) -> dict[str, Any]:
        """
        Extract Article VIII (Anti-Abstraction) evidence from framework usage.

        Analyzes:
        - Framework imports (Django, Flask, FastAPI, etc.)
        - Abstraction layers (ORM, middleware, wrappers)
        - Framework-specific patterns

        Args:
            repo_path: Path to repository (default: self.repo_path)

        Returns:
            Dictionary with status, rationale, and evidence
        """
        if repo_path is None:
            repo_path = self.repo_path

        repo_path = Path(repo_path)
        if not repo_path.exists():
            return {
                "status": "FAIL",
                "rationale": "Repository path does not exist",
                "evidence": [],
            }

        frameworks_detected: set[str] = set()
        abstraction_layers = 0
        evidence: list[str] = []
        total_imports = 0

        for py_file in repo_path.rglob("*.py"):
            scan = self._scan_viii_python_file(repo_path, py_file)
            if scan is None:
                continue
            fw, layers, imports, ev = scan
            frameworks_detected.update(fw)
            abstraction_layers += layers
            total_imports += imports
            evidence.extend(ev)

        # Determine status
        # PASS if no frameworks or minimal abstraction, FAIL if heavy framework usage
        if not frameworks_detected and abstraction_layers <= self.MAX_ABSTRACTION_LAYERS:
            status = "PASS"
            rationale = "No framework abstractions detected (direct library usage)"
        else:
            status = "FAIL"
            issues: list[str] = []
            if frameworks_detected:
                issues.append(f"framework abstractions detected ({', '.join(frameworks_detected)})")
            if abstraction_layers > self.MAX_ABSTRACTION_LAYERS:
                issues.append(
                    f"too many abstraction layers ({abstraction_layers}, threshold: {self.MAX_ABSTRACTION_LAYERS})"
                )
            rationale = f"Project violates anti-abstraction: {', '.join(issues)}"

        return {
            "status": status,
            "rationale": rationale,
            "evidence": evidence[:5],  # Limit to top 5 evidence items
            "frameworks_detected": list(frameworks_detected),
            "abstraction_layers": abstraction_layers,
            "total_imports": total_imports,
        }

    @beartype
    @require(
        lambda repo_path: repo_path is None or (isinstance(repo_path, Path) and repo_path.exists()),
        "Repository path must exist if provided",
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_article_ix_evidence(self, repo_path: Path | None = None) -> dict[str, Any]:
        """
        Extract Article IX (Integration-First) evidence from contract patterns.

        Analyzes:
        - Contract decorators (@icontract, @require, @ensure)
        - API definitions (OpenAPI, JSON Schema, Pydantic models)
        - Type hints (comprehensive = PASS, minimal = FAIL)

        Args:
            repo_path: Path to repository (default: self.repo_path)

        Returns:
            Dictionary with status, rationale, and evidence
        """
        if repo_path is None:
            repo_path = self.repo_path

        repo_path = Path(repo_path)
        if not repo_path.exists():
            return {
                "status": "FAIL",
                "rationale": "Repository path does not exist",
                "evidence": [],
            }

        contract_decorators_found = 0
        functions_with_type_hints = 0
        total_functions = 0
        pydantic_models = 0
        evidence: list[str] = []

        for py_file in repo_path.rglob("*.py"):
            scan = self._scan_ix_python_file(repo_path, py_file)
            if scan is None:
                continue
            c_dec, fn_hints, fn_total, pyd_cnt, ev = scan
            contract_decorators_found += c_dec
            functions_with_type_hints += fn_hints
            total_functions += fn_total
            pydantic_models += pyd_cnt
            evidence.extend(ev)

        # Calculate contract coverage
        contract_coverage = contract_decorators_found / total_functions if total_functions > 0 else 0.0
        type_hint_coverage = functions_with_type_hints / total_functions if total_functions > 0 else 0.0

        # Determine status
        # PASS if contracts defined or good type hint coverage, FAIL if minimal contracts
        if (
            contract_decorators_found > 0
            or contract_coverage >= self.MIN_CONTRACT_COVERAGE
            or type_hint_coverage >= 0.5
        ):
            status = "PASS"
            if contract_decorators_found > 0:
                rationale = f"Contracts defined using decorators ({contract_decorators_found} functions with contracts)"
            elif type_hint_coverage >= 0.5:
                rationale = f"Good type hint coverage ({type_hint_coverage:.1%} of functions have type hints)"
            else:
                rationale = f"Contract coverage meets threshold ({contract_coverage:.1%})"
        else:
            status = "FAIL"
            rationale = (
                f"No contract definitions detected (0 contracts, {total_functions} functions, "
                f"threshold: {self.MIN_CONTRACT_COVERAGE:.0%} coverage)"
            )

        return {
            "status": status,
            "rationale": rationale,
            "evidence": evidence[:5],  # Limit to top 5 evidence items
            "contract_decorators": contract_decorators_found,
            "functions_with_type_hints": functions_with_type_hints,
            "total_functions": total_functions,
            "pydantic_models": pydantic_models,
            "contract_coverage": contract_coverage,
            "type_hint_coverage": type_hint_coverage,
        }

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_all_evidence(self, repo_path: Path | None = None) -> dict[str, Any]:
        """
        Extract evidence for all constitution articles.

        Args:
            repo_path: Path to repository (default: self.repo_path)

        Returns:
            Dictionary with evidence for all articles
        """
        if repo_path is None:
            repo_path = self.repo_path

        return {
            "article_vii": self.extract_article_vii_evidence(repo_path),
            "article_viii": self.extract_article_viii_evidence(repo_path),
            "article_ix": self.extract_article_ix_evidence(repo_path),
        }

    @beartype
    @require(lambda evidence: isinstance(evidence, dict), "Evidence must be dict")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def generate_constitution_check_section(self, evidence: dict[str, Any]) -> str:
        """
        Generate constitution check section markdown from evidence.

        Args:
            evidence: Dictionary with evidence for all articles (from extract_all_evidence)

        Returns:
            Markdown string for constitution check section
        """
        lines = ["## Constitution Check", ""]

        # Article VII: Simplicity
        article_vii = evidence.get("article_vii", {})
        status_vii = article_vii.get("status", "FAIL")
        rationale_vii = article_vii.get("rationale", "Evidence extraction failed")
        evidence_vii = article_vii.get("evidence", [])

        lines.append("**Article VII (Simplicity)**:")
        if status_vii == "PASS":
            lines.append(f"- [x] {rationale_vii}")
        else:
            lines.append(f"- [ ] {rationale_vii}")
        if evidence_vii:
            lines.append("")
            lines.append("  **Evidence:**")
            for ev in evidence_vii:
                lines.append(f"  - {ev}")
        lines.append("")

        # Article VIII: Anti-Abstraction
        article_viii = evidence.get("article_viii", {})
        status_viii = article_viii.get("status", "FAIL")
        rationale_viii = article_viii.get("rationale", "Evidence extraction failed")
        evidence_viii = article_viii.get("evidence", [])

        lines.append("**Article VIII (Anti-Abstraction)**:")
        if status_viii == "PASS":
            lines.append(f"- [x] {rationale_viii}")
        else:
            lines.append(f"- [ ] {rationale_viii}")
        if evidence_viii:
            lines.append("")
            lines.append("  **Evidence:**")
            for ev in evidence_viii:
                lines.append(f"  - {ev}")
        lines.append("")

        # Article IX: Integration-First
        article_ix = evidence.get("article_ix", {})
        status_ix = article_ix.get("status", "FAIL")
        rationale_ix = article_ix.get("rationale", "Evidence extraction failed")
        evidence_ix = article_ix.get("evidence", [])

        lines.append("**Article IX (Integration-First)**:")
        if status_ix == "PASS":
            lines.append(f"- [x] {rationale_ix}")
        else:
            lines.append(f"- [ ] {rationale_ix}")
        if evidence_ix:
            lines.append("")
            lines.append("  **Evidence:**")
            for ev in evidence_ix:
                lines.append(f"  - {ev}")
        lines.append("")

        # Overall status (PASS if all articles PASS, otherwise FAIL)
        all_pass = all(evidence.get(f"article_{roman}", {}).get("status") == "PASS" for roman in ["vii", "viii", "ix"])
        overall_status = "PASS" if all_pass else "FAIL"
        lines.append(f"**Status**: {overall_status}")
        lines.append("")

        return "\n".join(lines)
