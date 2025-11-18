"""
Constitution enricher for automatic bootstrap and enrichment of project constitutions.

This module provides automatic constitution generation and enrichment capabilities
that analyze repository context to create bootstrap templates for review and adjustment.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


class ConstitutionEnricher:
    """
    Enricher for automatically generating and enriching project constitutions.

    Analyzes repository context (README, pyproject.toml, .cursor/rules/, docs/rules/)
    to extract project metadata, development principles, and quality standards,
    then generates a bootstrap constitution template ready for review and adjustment.
    """

    @beartype
    @require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @ensure(lambda result: isinstance(result, dict), "Must return dict with analysis results")
    def analyze_repository(self, repo_path: Path) -> dict[str, Any]:
        """
        Analyze repository and extract constitution metadata.

        Args:
            repo_path: Path to repository root

        Returns:
            Dictionary with analysis results (project_name, description, principles, etc.)
        """
        analysis: dict[str, Any] = {
            "project_name": "",
            "description": "",
            "target_users": [],
            "technology_stack": [],
            "principles": [],
            "quality_standards": [],
            "development_workflow": [],
            "project_type": "auto-detect",
        }

        # Analyze pyproject.toml or package.json
        pyproject_path = repo_path / "pyproject.toml"
        package_json_path = repo_path / "package.json"

        if pyproject_path.exists():
            analysis.update(self._analyze_pyproject(pyproject_path))
        elif package_json_path.exists():
            analysis.update(self._analyze_package_json(package_json_path))

        # Analyze README.md
        readme_path = repo_path / "README.md"
        if readme_path.exists():
            analysis.update(self._analyze_readme(readme_path))

        # Analyze .cursor/rules/ for development principles
        cursor_rules_dir = repo_path / ".cursor" / "rules"
        if cursor_rules_dir.exists():
            analysis["principles"].extend(self._analyze_cursor_rules(cursor_rules_dir))

        # Analyze docs/rules/ for quality gates and standards
        docs_rules_dir = repo_path / "docs" / "rules"
        if docs_rules_dir.exists():
            analysis["quality_standards"].extend(self._analyze_docs_rules(docs_rules_dir))

        # Detect project type
        analysis["project_type"] = self._detect_project_type(repo_path, analysis)

        return analysis

    @beartype
    @require(lambda pyproject_path: isinstance(pyproject_path, Path), "Path must be Path")
    @require(lambda pyproject_path: pyproject_path.exists(), "Path must exist")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _analyze_pyproject(self, pyproject_path: Path) -> dict[str, Any]:
        """Analyze pyproject.toml for project metadata."""
        result: dict[str, Any] = {
            "project_name": "",
            "description": "",
            "technology_stack": [],
            "python_version": "",
        }

        try:
            content = pyproject_path.read_text(encoding="utf-8")

            # Extract project name
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                result["project_name"] = name_match.group(1)

            # Extract description
            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if desc_match:
                result["description"] = desc_match.group(1)

            # Extract Python version requirement
            python_match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', content)
            if python_match:
                result["python_version"] = python_match.group(1)
                result["technology_stack"].append(f"Python {python_match.group(1)}")

            # Extract key dependencies (top 5)
            deps_match = re.search(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if deps_match:
                deps_content = deps_match.group(1)
                # Extract dependency names
                dep_matches = re.findall(r'["\']([^"\']+)["\']', deps_content)
                # Map common dependencies to technology stack
                tech_mapping = {
                    "typer": "Typer (CLI framework)",
                    "fastapi": "FastAPI (Web framework)",
                    "django": "Django (Web framework)",
                    "flask": "Flask (Web framework)",
                    "pydantic": "Pydantic (Data validation)",
                    "sqlalchemy": "SQLAlchemy (ORM)",
                    "icontract": "icontract (Runtime contracts)",
                    "beartype": "beartype (Type checking)",
                    "crosshair": "CrossHair (Symbolic execution)",
                }
                for dep in dep_matches[:5]:
                    if dep in tech_mapping:
                        result["technology_stack"].append(tech_mapping[dep])
                    elif not any(char in dep for char in [">", "<", "=", "~"]):
                        # Simple dependency name without version constraints
                        result["technology_stack"].append(dep)

        except Exception:
            pass  # If parsing fails, return empty result

        return result

    @beartype
    @require(lambda package_json_path: isinstance(package_json_path, Path), "Path must be Path")
    @require(lambda package_json_path: package_json_path.exists(), "Path must exist")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _analyze_package_json(self, package_json_path: Path) -> dict[str, Any]:
        """Analyze package.json for project metadata."""
        result: dict[str, Any] = {
            "project_name": "",
            "description": "",
            "technology_stack": [],
        }

        try:
            import json

            content = json.loads(package_json_path.read_text(encoding="utf-8"))

            result["project_name"] = content.get("name", "")
            result["description"] = content.get("description", "")

            # Extract dependencies
            deps = content.get("dependencies", {})
            dev_deps = content.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}

            # Map common dependencies
            tech_mapping = {
                "react": "React",
                "vue": "Vue.js",
                "typescript": "TypeScript",
                "vite": "Vite",
                "next": "Next.js",
            }

            for dep in list(all_deps.keys())[:5]:
                if dep in tech_mapping:
                    result["technology_stack"].append(tech_mapping[dep])
                else:
                    result["technology_stack"].append(dep)

        except Exception:
            pass

        return result

    @beartype
    @require(lambda readme_path: isinstance(readme_path, Path), "Path must be Path")
    @require(lambda readme_path: readme_path.exists(), "Path must exist")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _analyze_readme(self, readme_path: Path) -> dict[str, Any]:
        """Analyze README.md for project description and target users."""
        result: dict[str, Any] = {
            "description": "",
            "target_users": [],
        }

        try:
            content = readme_path.read_text(encoding="utf-8")

            # Extract first paragraph after title as description
            lines = content.split("\n")
            description_lines = []
            in_description = False

            for line in lines:
                # Skip title and empty lines
                if line.startswith("# "):
                    in_description = True
                    continue
                if in_description and line.strip() and not line.startswith("#"):
                    description_lines.append(line.strip())
                    if len(description_lines) >= 3:  # Get first 3 lines
                        break
                elif line.startswith("#") and description_lines:
                    break

            if description_lines:
                result["description"] = " ".join(description_lines)

            # Extract target users from "Perfect for:" or similar patterns
            perfect_for_match = re.search(r"(?:Perfect for|Target users?|For):\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            if perfect_for_match:
                users_text = perfect_for_match.group(1)
                # Split by commas or semicolons
                users = [u.strip() for u in re.split(r"[,;]", users_text)]
                result["target_users"] = users[:5]  # Limit to 5

        except Exception:
            pass

        return result

    @beartype
    @require(lambda rules_dir: isinstance(rules_dir, Path), "Rules directory must be Path")
    @require(lambda rules_dir: rules_dir.exists(), "Rules directory must exist")
    @require(lambda rules_dir: rules_dir.is_dir(), "Rules directory must be directory")
    @ensure(lambda result: isinstance(result, list), "Must return list of principles")
    def _analyze_cursor_rules(self, rules_dir: Path) -> list[dict[str, str]]:
        """Analyze .cursor/rules/ for development principles."""
        principles: list[dict[str, str]] = []

        # Common rule files that contain principles
        rule_files = [
            "python-github-rules.md",
            "coding-factory-rules.md",
            "spec-fact-cli-rules.md",
            "modern-javascript-typescript-guidelines.md",
        ]

        for rule_file in rule_files:
            rule_path = rules_dir / rule_file
            if rule_path.exists():
                try:
                    content = rule_path.read_text(encoding="utf-8")
                    # Extract principles from headings and key sections
                    extracted = self._extract_principles_from_markdown(content, rule_file)
                    principles.extend(extracted)
                except Exception:
                    pass

        return principles

    @beartype
    @require(lambda rules_dir: isinstance(rules_dir, Path), "Rules directory must be Path")
    @require(lambda rules_dir: rules_dir.exists(), "Rules directory must exist")
    @require(lambda rules_dir: rules_dir.is_dir(), "Rules directory must be directory")
    @ensure(lambda result: isinstance(result, list), "Must return list of standards")
    def _analyze_docs_rules(self, rules_dir: Path) -> list[str]:
        """Analyze docs/rules/ for quality standards and testing requirements."""
        standards: list[str] = []

        # Look for testing and quality gate files
        test_files = [
            "testing-and-build-guide.md",
            "python-github-rules.md",
        ]

        for test_file in test_files:
            test_path = rules_dir / test_file
            if test_path.exists():
                try:
                    content = test_path.read_text(encoding="utf-8")
                    # Extract quality standards
                    extracted = self._extract_quality_standards(content)
                    standards.extend(extracted)
                except Exception:
                    pass

        return standards

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be string")
    @require(lambda source: isinstance(source, str), "Source must be string")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_principles_from_markdown(self, content: str, source: str) -> list[dict[str, str]]:
        """Extract principles from markdown content."""
        principles: list[dict[str, str]] = []

        # Look for headings that indicate principles
        principle_patterns = [
            (r"##\s+(?:Core\s+)?Principles?", r"###\s+(.+?)\n(.*?)(?=###|\n##|\Z)", re.DOTALL),
            (r"###\s+(?:I\.|1\.|Principle\s+\d+)\s+(.+?)\n(.*?)(?=###|\n##|\Z)", re.DOTALL),
        ]

        for pattern, extract_pattern, flags in principle_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Extract principle sections
                matches = re.finditer(extract_pattern, content, flags)
                for match in matches:
                    if len(match.groups()) >= 2:
                        name = match.group(1).strip()
                        description = match.group(2).strip()
                        # Clean up description (remove markdown formatting, limit length)
                        description = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", description)  # Remove links
                        description = re.sub(r"\*\*([^\*]+)\*\*", r"\1", description)  # Remove bold
                        description = description[:200]  # Limit length
                        # Take first sentence or first 150 chars
                        if len(description) > 150:
                            description = description[:150].rsplit(".", 1)[0] + "."

                        principles.append({"name": name, "description": description, "source": source})

        # If no structured principles found, look for key phrases
        if not principles:
            key_phrases = [
                ("CLI-First", "All functionality exposed via CLI; CLI is the primary interface"),
                ("Contract-Driven", "Runtime contracts mandatory; Contract exploration with CrossHair"),
                ("Test-First", "TDD mandatory; Tests written before implementation"),
                ("Quality Gates", "All code changes must pass linting, formatting, type checking, test coverage"),
            ]

            for phrase, default_desc in key_phrases:
                if phrase.lower() in content.lower():
                    principles.append({"name": phrase, "description": default_desc, "source": source})

        return principles[:5]  # Limit to 5 principles

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be string")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_quality_standards(self, content: str) -> list[str]:
        """Extract quality standards from markdown content."""
        standards: list[str] = []

        # Look for testing requirements
        if re.search(r"test.*coverage|coverage.*requirement", content, re.IGNORECASE):
            coverage_match = re.search(r"(\d+)%", content)
            if coverage_match:
                standards.append(f"Test coverage: ≥{coverage_match.group(1)}% required")

        # Look for linting requirements
        if re.search(r"lint|linting", content, re.IGNORECASE):
            standards.append("Linting: black, isort, mypy, pylint required")

        # Look for formatting requirements
        if re.search(r"format|formatting", content, re.IGNORECASE):
            standards.append("Formatting: black, isort required")

        # Look for type checking
        if re.search(r"type.*check|mypy|basedpyright", content, re.IGNORECASE):
            standards.append("Type checking: mypy or basedpyright required")

        return standards

    @beartype
    @require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
    @require(lambda analysis: isinstance(analysis, dict), "Analysis must be dict")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _detect_project_type(self, repo_path: Path, analysis: dict[str, Any]) -> str:
        """Detect project type from repository structure."""
        # Check for CLI indicators
        if (repo_path / "src" / "specfact_cli" / "cli.py").exists() or (repo_path / "cli.py").exists():
            return "cli"
        if (repo_path / "setup.py").exists() and "cli" in analysis.get("description", "").lower():
            return "cli"

        # Check for library indicators
        if (repo_path / "src").exists() and not (repo_path / "src" / "app").exists():
            return "library"

        # Check for API indicators
        if (repo_path / "app").exists() or (repo_path / "api").exists():
            return "api"
        if "fastapi" in str(analysis.get("technology_stack", [])).lower():
            return "api"

        # Check for frontend indicators
        if (repo_path / "package.json").exists() and (
            "react" in str(analysis.get("technology_stack", [])).lower() or (repo_path / "src" / "components").exists()
        ):
            return "frontend"

        return "auto-detect"

    @beartype
    @require(lambda analysis: isinstance(analysis, dict), "Analysis must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list of principles")
    def suggest_principles(self, analysis: dict[str, Any]) -> list[dict[str, str]]:
        """
        Suggest principles based on repository analysis.

        Args:
            analysis: Repository analysis results

        Returns:
            List of principle dictionaries with name and description
        """
        principles: list[dict[str, str]] = []

        # Use extracted principles from analysis
        extracted_principles = analysis.get("principles", [])
        if extracted_principles:
            # Map to numbered principles
            for i, principle in enumerate(extracted_principles[:5], 1):
                principles.append(
                    {
                        "name": f"{self._number_to_roman(i)}. {principle.get('name', 'Principle')}",
                        "description": principle.get("description", ""),
                    }
                )

        # Add project-type-specific principles if not enough extracted
        project_type = analysis.get("project_type", "auto-detect")
        if len(principles) < 3:
            type_specific = self._get_project_type_principles(project_type, analysis)
            # Add only if not already present
            existing_names = {p["name"].lower() for p in principles}
            for principle in type_specific:
                if principle["name"].lower() not in existing_names:
                    principles.append(principle)
                    if len(principles) >= 5:
                        break

        # Ensure at least 3 principles
        if len(principles) < 3:
            # Add generic principles
            generic_principles = [
                {
                    "name": "I. Code Quality",
                    "description": "All code must pass linting, formatting, and type checking before commit",
                },
                {
                    "name": "II. Testing",
                    "description": "Tests required for all new features; Maintain test coverage standards",
                },
                {
                    "name": "III. Documentation",
                    "description": "Documentation must be updated for all public API changes",
                },
            ]
            for generic in generic_principles[: 3 - len(principles)]:
                principles.append(generic)

        return principles[:5]  # Limit to 5 principles

    @beartype
    @require(lambda num: isinstance(num, int), "Number must be int")
    @require(lambda num: 1 <= num <= 10, "Number must be 1-10")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _number_to_roman(self, num: int) -> str:
        """Convert number to Roman numeral."""
        roman_map = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
        return roman_map.get(num, str(num))

    @beartype
    @require(lambda project_type: isinstance(project_type, str), "Project type must be string")
    @require(lambda analysis: isinstance(analysis, dict), "Analysis must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _get_project_type_principles(self, project_type: str, analysis: dict[str, Any]) -> list[dict[str, str]]:
        """Get project-type-specific principles."""
        principles_map = {
            "cli": [
                {
                    "name": "I. CLI-First Architecture",
                    "description": "All functionality exposed via CLI; CLI is the primary interface; No direct code manipulation bypassing CLI validation",
                },
                {
                    "name": "II. Command Structure",
                    "description": "Commands follow consistent structure; Help text is comprehensive; Output formats are standardized",
                },
            ],
            "library": [
                {
                    "name": "I. API Design",
                    "description": "Public APIs must be well-documented; Backward compatibility maintained; Versioning follows semantic versioning",
                },
                {
                    "name": "II. Modularity",
                    "description": "Modules are self-contained; Dependencies are minimal; Clear separation of concerns",
                },
            ],
            "api": [
                {
                    "name": "I. REST/GraphQL Conventions",
                    "description": "API endpoints follow RESTful or GraphQL conventions; Status codes are used correctly; Error responses are standardized",
                },
                {
                    "name": "II. Authentication & Authorization",
                    "description": "All endpoints require authentication; Authorization is enforced; Security best practices followed",
                },
            ],
            "frontend": [
                {
                    "name": "I. Component Architecture",
                    "description": "Components are reusable and composable; Props are typed; State management is centralized",
                },
                {
                    "name": "II. Accessibility",
                    "description": "WCAG 2.1 AA compliance required; Keyboard navigation supported; Screen reader compatible",
                },
            ],
        }

        return principles_map.get(project_type, [])

    @beartype
    @require(lambda template_path: isinstance(template_path, Path), "Template path must be Path")
    @require(lambda suggestions: isinstance(suggestions, dict), "Suggestions must be dict")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def enrich_template(self, template_path: Path, suggestions: dict[str, Any]) -> str:
        """
        Fill constitution template with suggestions.

        Args:
            template_path: Path to constitution template
            suggestions: Dictionary with placeholder values

        Returns:
            Enriched constitution markdown
        """
        if not template_path.exists() or str(template_path) == "/dev/null":
            # Create default template
            template_content = self._get_default_template()
        else:
            template_content = template_path.read_text(encoding="utf-8")

        # Replace placeholders
        enriched = template_content

        # Replace [PROJECT_NAME]
        project_name = suggestions.get("project_name", "Project")
        enriched = re.sub(r"\[PROJECT_NAME\]", project_name, enriched)

        # Replace principles (up to 5)
        principles = suggestions.get("principles", [])
        for i, principle in enumerate(principles, 1):
            enriched = re.sub(
                rf"\[PRINCIPLE_{i}_NAME\]",
                principle.get("name", f"Principle {i}"),
                enriched,
            )
            enriched = re.sub(
                rf"\[PRINCIPLE_{i}_DESCRIPTION\]",
                principle.get("description", ""),
                enriched,
            )

        # Remove unused principle placeholders
        for i in range(len(principles) + 1, 6):
            # Remove principle section if placeholder remains
            pattern = rf"### \[PRINCIPLE_{i}_NAME\].*?\[PRINCIPLE_{i}_DESCRIPTION\]"
            enriched = re.sub(pattern, "", enriched, flags=re.DOTALL)

        # Replace [SECTION_2_NAME] and [SECTION_2_CONTENT]
        section2_name = suggestions.get("section2_name", "Development Workflow")
        section2_content = suggestions.get("section2_content", self._generate_workflow_section(suggestions))
        enriched = re.sub(r"\[SECTION_2_NAME\]", section2_name, enriched)
        enriched = re.sub(r"\[SECTION_2_CONTENT\]", section2_content, enriched)

        # Replace [SECTION_3_NAME] and [SECTION_3_CONTENT] (optional)
        section3_name = suggestions.get("section3_name", "Quality Standards")
        section3_content = suggestions.get("section3_content", self._generate_quality_standards_section(suggestions))
        enriched = re.sub(r"\[SECTION_3_NAME\]", section3_name, enriched)
        enriched = re.sub(r"\[SECTION_3_CONTENT\]", section3_content, enriched)

        # Replace [GOVERNANCE_RULES]
        governance_rules = suggestions.get(
            "governance_rules",
            "Constitution supersedes all other practices. Amendments require documentation, team approval, and migration plan for breaking changes.",
        )
        enriched = re.sub(r"\[GOVERNANCE_RULES\]", governance_rules, enriched)

        # Replace version and dates
        today = date.today().isoformat()
        enriched = re.sub(r"\[CONSTITUTION_VERSION\]", "1.0.0", enriched)
        enriched = re.sub(r"\[RATIFICATION_DATE\]", today, enriched)
        enriched = re.sub(r"\[LAST_AMENDED_DATE\]", today, enriched)

        # Remove HTML comments (examples)
        enriched = re.sub(r"<!--.*?-->", "", enriched, flags=re.DOTALL)

        # Clean up multiple blank lines
        enriched = re.sub(r"\n{3,}", "\n\n", enriched)

        return enriched.strip() + "\n"

    @beartype
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _get_default_template(self) -> str:
        """Get default constitution template."""
        return """# [PROJECT_NAME] Constitution

## Core Principles

### [PRINCIPLE_1_NAME]
[PRINCIPLE_1_DESCRIPTION]

### [PRINCIPLE_2_NAME]
[PRINCIPLE_2_DESCRIPTION]

### [PRINCIPLE_3_NAME]
[PRINCIPLE_3_DESCRIPTION]

## [SECTION_2_NAME]

[SECTION_2_CONTENT]

## [SECTION_3_NAME]

[SECTION_3_CONTENT]

## Governance

[GOVERNANCE_RULES]

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
"""

    @beartype
    @require(lambda suggestions: isinstance(suggestions, dict), "Suggestions must be dict")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _generate_workflow_section(self, suggestions: dict[str, Any]) -> str:
        """Generate development workflow section."""
        workflow_items = suggestions.get("development_workflow", [])

        if not workflow_items:
            # Generate from analysis
            workflow_items = [
                "Testing: Run test suite before committing",
                "Formatting: Apply code formatter before committing",
                "Linting: Fix linting errors before committing",
                "Type Checking: Ensure type checking passes",
            ]

        lines = []
        for item in workflow_items:
            lines.append(f"- {item}")

        return "\n".join(lines) if lines else "Standard development workflow applies."

    @beartype
    @require(lambda suggestions: isinstance(suggestions, dict), "Suggestions must be dict")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _generate_quality_standards_section(self, suggestions: dict[str, Any]) -> str:
        """Generate quality standards section."""
        standards = suggestions.get("quality_standards", [])

        if not standards:
            standards = [
                "Code quality: Linting and formatting required",
                "Testing: Test coverage standards must be met",
                "Documentation: Public APIs must be documented",
            ]

        lines = []
        for standard in standards:
            lines.append(f"- {standard}")

        return "\n".join(lines) if lines else "Standard quality gates apply."

    @beartype
    @require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
    @require(lambda constitution_path: isinstance(constitution_path, Path), "Constitution path must be Path")
    @ensure(lambda result: isinstance(result, str), "Must return enriched constitution")
    def bootstrap(self, repo_path: Path, constitution_path: Path) -> str:
        """
        Generate bootstrap constitution from repository analysis.

        Args:
            repo_path: Path to repository root
            constitution_path: Path where constitution should be written

        Returns:
            Enriched constitution markdown
        """
        # Analyze repository
        analysis = self.analyze_repository(repo_path)

        # Suggest principles
        principles = self.suggest_principles(analysis)

        # Prepare suggestions
        suggestions: dict[str, Any] = {
            "project_name": analysis.get("project_name", "Project"),
            "principles": principles,
            "section2_name": "Development Workflow",
            "section2_content": self._generate_workflow_section(analysis),
            "section3_name": "Quality Standards",
            "section3_content": self._generate_quality_standards_section(analysis),
            "governance_rules": "Constitution supersedes all other practices. Amendments require documentation, team approval, and migration plan for breaking changes.",
            "development_workflow": analysis.get("development_workflow", []),
            "quality_standards": analysis.get("quality_standards", []),
        }

        # Enrich template (always use default template for bootstrap, not existing constitution)
        # Bootstrap should generate fresh constitution, not enrich existing one
        template_path = Path("/dev/null")  # Will trigger default template in enrich_template
        return self.enrich_template(template_path, suggestions)

    @beartype
    @require(lambda constitution_path: isinstance(constitution_path, Path), "Constitution path must be Path")
    @ensure(lambda result: isinstance(result, tuple), "Must return (is_valid, issues) tuple")
    def validate(self, constitution_path: Path) -> tuple[bool, list[str]]:
        """
        Validate constitution completeness.

        Args:
            constitution_path: Path to constitution file

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues: list[str] = []

        if not constitution_path.exists():
            return (False, ["Constitution file does not exist"])

        try:
            content = constitution_path.read_text(encoding="utf-8").strip()

            if not content or content == "# Constitution":
                issues.append("Constitution is empty or minimal (only contains header)")

            # Check for remaining placeholders
            placeholder_pattern = r"\[[A-Z_0-9]+\]"
            placeholders = re.findall(placeholder_pattern, content)
            if placeholders:
                issues.append(
                    f"Constitution contains {len(placeholders)} unresolved placeholders: {', '.join(placeholders[:5])}"
                )

            # Check for principles
            if not re.search(r"##\s+Core\s+Principles", content, re.IGNORECASE):
                issues.append("Constitution missing 'Core Principles' section")

            # Check for at least one principle
            principle_count = len(re.findall(r"###\s+(?:I\.|II\.|III\.|IV\.|V\.|1\.|2\.|3\.|4\.|5\.)", content))
            if principle_count == 0:
                issues.append("Constitution has no numbered principles")

            # Check for governance section
            if not re.search(r"##\s+Governance", content, re.IGNORECASE):
                issues.append("Constitution missing 'Governance' section")

            # Check for version line
            if not re.search(r"\*\*Version\*\*.*\*\*Ratified\*\*", content):
                issues.append("Constitution missing version and ratification date")

        except Exception as e:
            return (False, [f"Error reading constitution: {e!s}"])

        return (len(issues) == 0, issues)
