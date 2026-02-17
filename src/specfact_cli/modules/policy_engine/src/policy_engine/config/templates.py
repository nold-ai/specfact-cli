"""Policy template discovery and scaffolding."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require


TEMPLATE_NAMES: tuple[str, ...] = ("scrum", "kanban", "safe", "mixed")


@beartype
@ensure(lambda result: isinstance(result, list), "Must return list of template names")
def list_policy_templates() -> list[str]:
    """Return available built-in policy templates."""
    return list(TEMPLATE_NAMES)


@beartype
@ensure(lambda result: result is None or isinstance(result, Path), "Resolved template dir must be Path or None")
def resolve_policy_template_dir() -> Path | None:
    """Resolve the built-in templates folder in both source and installed contexts."""
    import specfact_cli

    pkg_root = Path(specfact_cli.__file__).resolve().parent
    packaged_dir = pkg_root / "resources" / "templates" / "policies"
    if packaged_dir.exists():
        return packaged_dir

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "resources" / "templates" / "policies"
        if candidate.exists():
            return candidate
    return None


@beartype
@require(lambda template_name: template_name.strip() != "", "Template name must not be empty")
@ensure(lambda result: isinstance(result, tuple), "Must return tuple")
def load_policy_template(template_name: str) -> tuple[str | None, str | None]:
    """Load template content by name."""
    normalized = template_name.strip().lower()
    if normalized not in TEMPLATE_NAMES:
        options = ", ".join(TEMPLATE_NAMES)
        return None, f"Unsupported policy template '{template_name}'. Available: {options}"

    template_dir = resolve_policy_template_dir()
    if template_dir is None:
        return None, "Built-in policy templates were not found under resources/templates/policies."

    template_path = template_dir / f"{normalized}.yaml"
    if not template_path.exists():
        return None, f"Policy template file not found: {template_path}"
    return template_path.read_text(encoding="utf-8"), None
