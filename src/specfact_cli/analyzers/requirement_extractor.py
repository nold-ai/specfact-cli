"""Requirement extractor for generating complete requirements from code semantics."""

from __future__ import annotations

import ast
import re

from beartype import beartype
from icontract import ensure, require


class RequirementExtractor:
    """
    Extracts complete requirements from code semantics.

    Generates requirement statements in the format:
    Subject + Modal verb + Action verb + Object + Outcome

    Also extracts Non-Functional Requirements (NFRs) from code patterns.
    """

    # Modal verbs for requirement statements
    MODAL_VERBS = ["must", "shall", "should", "will", "can", "may"]

    # Action verbs commonly used in requirements
    ACTION_VERBS = [
        "provide",
        "support",
        "enable",
        "allow",
        "ensure",
        "validate",
        "handle",
        "process",
        "generate",
        "extract",
        "analyze",
        "transform",
        "store",
        "retrieve",
        "display",
        "execute",
        "implement",
        "perform",
    ]

    # NFR patterns
    PERFORMANCE_PATTERNS = [
        "async",
        "await",
        "cache",
        "parallel",
        "concurrent",
        "thread",
        "pool",
        "queue",
        "batch",
        "optimize",
        "lazy",
        "defer",
    ]

    SECURITY_PATTERNS = [
        "auth",
        "authenticate",
        "authorize",
        "encrypt",
        "decrypt",
        "hash",
        "token",
        "secret",
        "password",
        "credential",
        "permission",
        "role",
        "access",
        "secure",
    ]

    RELIABILITY_PATTERNS = [
        "retry",
        "retries",
        "timeout",
        "fallback",
        "circuit",
        "breaker",
        "resilient",
        "recover",
        "error",
        "exception",
        "handle",
        "validate",
        "verify",
    ]

    MAINTAINABILITY_PATTERNS = [
        "docstring",
        "documentation",
        "comment",
        "type",
        "hint",
        "annotation",
        "interface",
        "abstract",
        "protocol",
        "test",
        "mock",
        "fixture",
    ]

    @beartype
    def __init__(self) -> None:
        """Initialize requirement extractor."""

    @beartype
    @require(lambda class_node: isinstance(class_node, ast.ClassDef), "Class must be ClassDef node")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def extract_complete_requirement(self, class_node: ast.ClassDef) -> str:
        """
        Extract complete requirement statement from class.

        Format: Subject + Modal + Action + Object + Outcome

        Args:
            class_node: AST node for the class

        Returns:
            Complete requirement statement
        """
        # Extract subject (class name)
        subject = self._humanize_name(class_node.name)

        # Extract from docstring
        docstring = ast.get_docstring(class_node)
        if docstring:
            requirement = self._parse_docstring_to_requirement(docstring, subject)
            if requirement:
                return requirement

        # Extract from class name patterns
        requirement = self._infer_requirement_from_name(class_node.name, subject)
        if requirement:
            return requirement

        # Default requirement
        return f"The system {subject.lower()} must provide {subject.lower()} functionality"

    @beartype
    @require(lambda method_node: isinstance(method_node, ast.FunctionDef), "Method must be FunctionDef node")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def extract_method_requirement(self, method_node: ast.FunctionDef, class_name: str) -> str:
        """
        Extract complete requirement statement from method.

        Args:
            method_node: AST node for the method
            class_name: Name of the class containing the method

        Returns:
            Complete requirement statement
        """
        method_name = method_node.name
        subject = class_name

        # Extract from docstring
        docstring = ast.get_docstring(method_node)
        if docstring:
            requirement = self._parse_docstring_to_requirement(docstring, subject, method_name)
            if requirement:
                return requirement

        # Extract from method name patterns
        requirement = self._infer_requirement_from_name(method_name, subject, method_name)
        if requirement:
            return requirement

        # Default requirement
        action = self._extract_action_from_method_name(method_name)
        return f"The system {subject.lower()} must {action} {method_name.replace('_', ' ')}"

    @beartype
    @require(lambda class_node: isinstance(class_node, ast.ClassDef), "Class must be ClassDef node")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def extract_nfrs(self, class_node: ast.ClassDef) -> list[str]:
        """
        Extract Non-Functional Requirements from code patterns.

        Args:
            class_node: AST node for the class

        Returns:
            List of NFR statements
        """
        nfrs: list[str] = []

        # Analyze class body for NFR patterns
        class_code = ast.unparse(class_node) if hasattr(ast, "unparse") else str(class_node)
        class_code_lower = class_code.lower()

        # Performance NFRs
        if any(pattern in class_code_lower for pattern in self.PERFORMANCE_PATTERNS):
            nfrs.append("The system must meet performance requirements (async operations, caching, optimization)")

        # Security NFRs
        if any(pattern in class_code_lower for pattern in self.SECURITY_PATTERNS):
            nfrs.append("The system must meet security requirements (authentication, authorization, encryption)")

        # Reliability NFRs
        if any(pattern in class_code_lower for pattern in self.RELIABILITY_PATTERNS):
            nfrs.append("The system must meet reliability requirements (error handling, retry logic, resilience)")

        # Maintainability NFRs
        if any(pattern in class_code_lower for pattern in self.MAINTAINABILITY_PATTERNS):
            nfrs.append("The system must meet maintainability requirements (documentation, type hints, testing)")

        # Check for async methods
        async_methods = [item for item in class_node.body if isinstance(item, ast.AsyncFunctionDef)]
        if async_methods:
            nfrs.append("The system must support asynchronous operations for improved performance")

        # Check for type hints
        has_type_hints = False
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and (item.returns or any(arg.annotation for arg in item.args.args)):
                has_type_hints = True
                break
        if has_type_hints:
            nfrs.append("The system must use type hints for improved code maintainability and IDE support")

        return nfrs

    @beartype
    def _parse_docstring_to_requirement(
        self, docstring: str, subject: str, method_name: str | None = None
    ) -> str | None:
        """
        Parse docstring to extract complete requirement statement.

        Args:
            docstring: Class or method docstring
            subject: Subject of the requirement (class name)
            method_name: Optional method name

        Returns:
            Complete requirement statement or None
        """
        # Clean docstring
        docstring = docstring.strip()
        first_sentence = docstring.split(".")[0].strip()

        # Check if already in requirement format
        if any(modal in first_sentence.lower() for modal in self.MODAL_VERBS):
            # Already has modal verb, return as-is
            return first_sentence

        # Try to extract action and object
        action_match = re.search(
            r"(?:provides?|supports?|enables?|allows?|ensures?|validates?|handles?|processes?|generates?|extracts?|analyzes?|transforms?|stores?|retrieves?|displays?|executes?|implements?|performs?)\s+(.+?)(?:\.|$)",
            first_sentence.lower(),
        )
        if action_match:
            action = action_match.group(0).split()[0]  # Get the action verb
            object_part = action_match.group(1).strip()
            return f"The system {subject.lower()} must {action} {object_part}"

        # Try to extract from "This class/method..." pattern
        this_match = re.search(
            r"(?:this|the)\s+(?:class|method|function)\s+(?:provides?|supports?|enables?|allows?|ensures?)\s+(.+?)(?:\.|$)",
            first_sentence.lower(),
        )
        if this_match:
            object_part = this_match.group(1).strip()
            action = "provide"
            return f"The system {subject.lower()} must {action} {object_part}"

        return None

    @beartype
    def _infer_requirement_from_name(self, name: str, subject: str, method_name: str | None = None) -> str | None:
        """
        Infer requirement from class or method name patterns.

        Args:
            name: Class or method name
            subject: Subject of the requirement
            method_name: Optional method name (for method requirements)

        Returns:
            Complete requirement statement or None
        """
        name_lower = name.lower()

        # Validation patterns
        if any(keyword in name_lower for keyword in ["validate", "check", "verify"]):
            target = name.replace("validate", "").replace("check", "").replace("verify", "").strip()
            return f"The system {subject.lower()} must validate {target.replace('_', ' ')}"

        # Processing patterns
        if any(keyword in name_lower for keyword in ["process", "handle", "manage"]):
            target = name.replace("process", "").replace("handle", "").replace("manage", "").strip()
            return f"The system {subject.lower()} must {name_lower.split('_')[0]} {target.replace('_', ' ')}"

        # Get/Set patterns
        if name_lower.startswith("get_"):
            target = name.replace("get_", "").replace("_", " ")
            return f"The system {subject.lower()} must retrieve {target}"

        if name_lower.startswith(("set_", "update_")):
            target = name.replace("set_", "").replace("update_", "").replace("_", " ")
            return f"The system {subject.lower()} must update {target}"

        return None

    @beartype
    def _extract_action_from_method_name(self, method_name: str) -> str:
        """Extract action verb from method name."""
        method_lower = method_name.lower()

        for action in self.ACTION_VERBS:
            if method_lower.startswith(action) or action in method_lower:
                return action

        # Default action
        return "execute"

    @beartype
    def _humanize_name(self, name: str) -> str:
        """Convert camelCase or snake_case to human-readable name."""
        # Handle camelCase
        if re.search(r"[a-z][A-Z]", name):
            name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

        # Handle snake_case
        name = name.replace("_", " ")

        # Capitalize words
        return " ".join(word.capitalize() for word in name.split())
