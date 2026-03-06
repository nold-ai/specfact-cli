"""Backlog add command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import requests
import typer
import yaml
from beartype import beartype
from icontract import require

from backlog_core.adapters.backlog_protocol import require_backlog_graph_protocol
from backlog_core.graph.builder import BacklogGraphBuilder
from backlog_core.graph.config_schema import load_backlog_config_from_backlog_file, load_backlog_config_from_spec
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.dor_config import DefinitionOfReady
from specfact_cli.utils.prompts import print_error, print_info, print_success, print_warning, prompt_text


DEFAULT_CREATION_HIERARCHY: dict[str, list[str]] = {
    "epic": [],
    "feature": ["epic"],
    "story": ["feature", "epic"],
    "task": ["story", "feature"],
    "bug": ["story", "feature", "epic"],
    "spike": ["feature", "epic"],
    "custom": ["epic", "feature", "story"],
}

STORY_LIKE_TYPES: set[str] = {"story", "feature", "task", "bug"}

DEFAULT_CUSTOM_MAPPING_FILES: dict[str, Path] = {
    "ado": Path(".specfact/templates/backlog/field_mappings/ado_custom.yaml"),
    "github": Path(".specfact/templates/backlog/field_mappings/github_custom.yaml"),
}


@beartype
def _prompt_multiline_text(field_label: str, end_marker: str) -> str:
    """Read multiline text until a sentinel marker line is entered."""
    marker = end_marker.strip() or "::END::"
    print_info(f"{field_label} (multiline). End input with '{marker}' on a new line.")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == marker:
            break
        lines.append(line)
    return "\n".join(lines).strip()


@beartype
def _select_with_fallback(message: str, choices: list[str], default: str | None = None) -> str:
    """Use questionary select when available, otherwise plain text prompt."""
    normalized = [choice for choice in choices if choice]
    if not normalized:
        return (default or "").strip()

    try:
        import questionary  # type: ignore[reportMissingImports]

        selected = questionary.select(message, choices=normalized, default=default).ask()
        if isinstance(selected, str) and selected.strip():
            return selected.strip()
    except Exception:
        # If questionary is unavailable or fails, continue with plain-text prompt fallback.
        pass

    print_info(f"{message}: {', '.join(normalized)}")
    fallback_default = default if default in normalized else normalized[0]
    return prompt_text(message, default=fallback_default)


@beartype
def _interactive_sprint_selection(adapter_name: str, adapter_instance: Any, project_id: str) -> str | None:
    """Prompt for sprint/iteration selection (provider-aware)."""
    adapter_lower = adapter_name.strip().lower()

    if adapter_lower != "ado":
        raw = prompt_text("Sprint/iteration (optional)", default="", required=False).strip()
        return raw or None

    current_iteration: str | None = None
    list_iterations: list[str] = []

    restore_org = getattr(adapter_instance, "org", None)
    restore_project = getattr(adapter_instance, "project", None)
    resolver = getattr(adapter_instance, "_resolve_graph_project_context", None)
    if callable(resolver):
        try:
            resolved_org, resolved_project = resolver(project_id)
            if hasattr(adapter_instance, "org"):
                adapter_instance.org = resolved_org
            if hasattr(adapter_instance, "project"):
                adapter_instance.project = resolved_project
        except Exception:
            # Best-effort org/project resolution only; keep existing context on any failure.
            pass

    get_current = getattr(adapter_instance, "_get_current_iteration", None)
    if callable(get_current):
        try:
            resolved = get_current()
            if isinstance(resolved, str) and resolved.strip():
                current_iteration = resolved.strip()
        except Exception:
            current_iteration = None

    get_list = getattr(adapter_instance, "_list_available_iterations", None)
    if callable(get_list):
        try:
            candidates = get_list()
            if isinstance(candidates, list):
                list_iterations = [str(item).strip() for item in candidates if str(item).strip()]
        except Exception:
            list_iterations = []

    if hasattr(adapter_instance, "org"):
        adapter_instance.org = restore_org
    if hasattr(adapter_instance, "project"):
        adapter_instance.project = restore_project

    options = ["(skip sprint/iteration)"]
    if current_iteration:
        options.append(f"current: {current_iteration}")
    options.extend([iteration for iteration in list_iterations if iteration != current_iteration])
    options.append("manual entry")

    default = f"current: {current_iteration}" if current_iteration else "manual entry"
    selected = _select_with_fallback("Select sprint/iteration", options, default=default)

    if selected == "(skip sprint/iteration)":
        return None
    if selected.startswith("current: "):
        return selected.removeprefix("current: ").strip() or None
    if selected == "manual entry":
        manual = prompt_text("Enter sprint/iteration path", default="", required=False).strip()
        return manual or None
    return selected.strip() or None


@beartype
@require(lambda value: isinstance(value, str), "value must be a string")
def _normalize_type(value: str) -> str:
    return value.strip().lower().replace("_", " ").replace("-", " ")


@beartype
def _resolve_default_template(adapter_name: str, template: str | None) -> str:
    if template and template.strip():
        return template.strip()
    if adapter_name.strip().lower() == "ado":
        return "ado_scrum"
    return "github_projects"


@beartype
def _extract_item_type(item: Any) -> str:
    """Best-effort normalized item type from graph item and raw payload."""
    value = getattr(item, "type", None)
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str) and enum_value.strip():
        return _normalize_type(enum_value)
    if isinstance(value, str) and value.strip():
        normalized = _normalize_type(value)
        if normalized.startswith("itemtype."):
            normalized = normalized.split(".", 1)[1]
        if normalized:
            return normalized

    inferred = getattr(item, "inferred_type", None)
    inferred_value = getattr(inferred, "value", None)
    if isinstance(inferred_value, str) and inferred_value.strip():
        return _normalize_type(inferred_value)

    raw_data = getattr(item, "raw_data", {})
    if isinstance(raw_data, dict):
        fields = raw_data.get("fields") if isinstance(raw_data.get("fields"), dict) else {}
        candidates = [
            raw_data.get("type"),
            raw_data.get("work_item_type"),
            fields.get("System.WorkItemType") if isinstance(fields, dict) else None,
            raw_data.get("issue_type"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                normalized = _normalize_type(candidate)
                aliases = {
                    "user story": "story",
                    "product backlog item": "story",
                    "pb i": "story",
                }
                return aliases.get(normalized, normalized)

    return "custom"


@beartype
def _load_custom_config(custom_config: Path | None) -> dict[str, Any]:
    if custom_config is None:
        return {}
    if not custom_config.exists():
        raise ValueError(f"Custom config file not found: {custom_config}")
    loaded = yaml.safe_load(custom_config.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


@beartype
def _resolve_custom_config_path(adapter_name: str, custom_config: Path | None) -> Path | None:
    """Resolve custom mapping file path with adapter-specific default fallback."""
    if custom_config is not None:
        return custom_config
    candidate = DEFAULT_CUSTOM_MAPPING_FILES.get(adapter_name.strip().lower())
    if candidate is not None and candidate.exists():
        return candidate
    return None


@beartype
def _load_template_config(template: str) -> dict[str, Any]:
    module_root = Path(__file__).resolve().parents[1]
    template_file = module_root / "resources" / "backlog-templates" / f"{template}.yaml"
    shared_template_file = (
        Path(__file__).resolve().parents[5]
        / "src"
        / "specfact_cli"
        / "resources"
        / "backlog-templates"
        / f"{template}.yaml"
    )

    for candidate in (template_file, shared_template_file):
        if candidate.exists():
            loaded = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return loaded
    return {}


@beartype
def _load_provider_settings(repo_path: Path, adapter_name: str) -> dict[str, Any]:
    backlog_cfg = load_backlog_config_from_backlog_file(repo_path / ".specfact" / "backlog-config.yaml")
    spec_config = backlog_cfg or load_backlog_config_from_spec(repo_path / ".specfact" / "spec.yaml")
    if spec_config is None:
        return {}
    provider = spec_config.providers.get(adapter_name.strip().lower())
    if provider is None or not isinstance(provider.settings, dict):
        return {}
    return dict(provider.settings)


@beartype
def _load_field_mapping_payload(mapping_path: Path | None) -> dict[str, Any]:
    if mapping_path is None or not mapping_path.exists():
        return {}
    loaded = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


@beartype
def _resolve_saved_mapping_path(repo_path: Path, configured_path: str | None, adapter_name: str) -> Path | None:
    raw_path = (configured_path or "").strip()
    if raw_path:
        candidate = Path(raw_path)
        return candidate if candidate.is_absolute() else repo_path / candidate
    default_candidate = DEFAULT_CUSTOM_MAPPING_FILES.get(adapter_name.strip().lower())
    if default_candidate is None:
        return None
    return repo_path / default_candidate if not default_candidate.is_absolute() else default_candidate


@beartype
def _parse_custom_field_entries(entries: list[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_entry in entries or []:
        entry = raw_entry.strip()
        if not entry or "=" not in entry:
            raise ValueError("custom-field entries must use '<name>=<value>' format")
        raw_name, raw_value = entry.split("=", 1)
        name = raw_name.strip()
        value = raw_value.strip()
        if not name or not value:
            raise ValueError("custom-field entries must use '<name>=<value>' format")
        parsed[name] = value
    return parsed


@beartype
def _resolve_ado_custom_fields(
    repo_path: Path,
    issue_type: str,
    custom_fields: list[str] | None,
) -> dict[str, Any] | None:
    settings = _load_provider_settings(repo_path, "ado")
    if not settings and not custom_fields:
        return None

    mapping_path = _resolve_saved_mapping_path(
        repo_path,
        str(settings.get("field_mapping_file") or "").strip() or None,
        "ado",
    )
    mapping_payload = _load_field_mapping_payload(mapping_path)
    field_mappings = mapping_payload.get("field_mappings")
    provider_to_canonical = field_mappings if isinstance(field_mappings, dict) else {}

    selected_work_item_type = str(settings.get("selected_work_item_type") or "").strip()
    if not selected_work_item_type:
        selected_work_item_type = "User Story" if issue_type == "story" else issue_type.replace("_", " ").title()

    required_by_type = settings.get("required_fields_by_work_item_type")
    required_refs = []
    if isinstance(required_by_type, dict):
        selected_required = required_by_type.get(selected_work_item_type)
        if isinstance(selected_required, list):
            required_refs = [str(item).strip() for item in selected_required if str(item).strip()]

    allowed_by_type = settings.get("allowed_values_by_work_item_type")
    allowed_values: dict[str, list[str]] = {}
    if isinstance(allowed_by_type, dict):
        selected_allowed = allowed_by_type.get(selected_work_item_type)
        if isinstance(selected_allowed, dict):
            for field_name, raw_values in selected_allowed.items():
                if isinstance(raw_values, list):
                    allowed_values[str(field_name).strip()] = [
                        str(item).strip() for item in raw_values if str(item).strip()
                    ]

    alias_to_provider: dict[str, str] = {}
    for provider_field, canonical_name in provider_to_canonical.items():
        provider_key = str(provider_field).strip()
        canonical_key = str(canonical_name).strip()
        if provider_key:
            alias_to_provider[provider_key.lower()] = provider_key
        if canonical_key:
            alias_to_provider[canonical_key.lower()] = provider_key
    for provider_field in required_refs:
        alias_to_provider.setdefault(provider_field.lower(), provider_field)

    parsed_entries = _parse_custom_field_entries(custom_fields)
    resolved_fields: dict[str, Any] = {}
    for raw_name, value in parsed_entries.items():
        provider_key = alias_to_provider.get(raw_name.strip().lower())
        if provider_key is None:
            raise ValueError(f"unknown custom field '{raw_name}'")
        resolved_fields[provider_key] = value

    for required_ref in required_refs:
        if required_ref not in resolved_fields:
            canonical = str(provider_to_canonical.get(required_ref) or "").strip()
            label = canonical or required_ref
            raise ValueError(f"missing required custom field '{label}'")

    for provider_key, value in resolved_fields.items():
        allowed = allowed_values.get(provider_key) or []
        if allowed and value not in allowed:
            allowed_text = ", ".join(allowed)
            canonical = str(provider_to_canonical.get(provider_key) or "").strip()
            label = canonical or provider_key
            raise ValueError(f"invalid value for custom field '{label}'. Allowed values: {allowed_text}")

    return {"fields": resolved_fields} if resolved_fields else None


@beartype
def _derive_creation_hierarchy(template_payload: dict[str, Any], custom_config: dict[str, Any]) -> dict[str, list[str]]:
    custom_hierarchy = custom_config.get("creation_hierarchy")
    if isinstance(custom_hierarchy, dict):
        return {
            _normalize_type(str(child)): [_normalize_type(str(parent)) for parent in parents]
            for child, parents in custom_hierarchy.items()
            if isinstance(parents, list)
        }

    template_hierarchy = template_payload.get("creation_hierarchy")
    if isinstance(template_hierarchy, dict):
        return {
            _normalize_type(str(child)): [_normalize_type(str(parent)) for parent in parents]
            for child, parents in template_hierarchy.items()
            if isinstance(parents, list)
        }

    return DEFAULT_CREATION_HIERARCHY


@beartype
def _resolve_provider_fields_for_create(
    adapter_name: str,
    template_payload: dict[str, Any],
    custom_config: dict[str, Any],
    repo_path: Path,
) -> dict[str, Any] | None:
    """Resolve provider-specific create payload fields from template/custom config."""
    if adapter_name.strip().lower() != "github":
        return None

    def _extract_github_project_v2(source: dict[str, Any]) -> dict[str, Any]:
        provider_fields = source.get("provider_fields")
        if isinstance(provider_fields, dict):
            candidate = provider_fields.get("github_project_v2")
            if isinstance(candidate, dict):
                return dict(candidate)
        fallback = source.get("github_project_v2")
        if isinstance(fallback, dict):
            return dict(fallback)
        return {}

    def _extract_github_issue_types(source: dict[str, Any]) -> dict[str, Any]:
        def _has_type_id_mapping(candidate: dict[str, Any]) -> bool:
            raw_type_ids = candidate.get("type_ids")
            if not isinstance(raw_type_ids, dict):
                return False
            return any(str(value).strip() for value in raw_type_ids.values())

        provider_fields = source.get("provider_fields")
        if isinstance(provider_fields, dict):
            candidate = provider_fields.get("github_issue_types")
            if isinstance(candidate, dict) and _has_type_id_mapping(candidate):
                return dict(candidate)
        fallback = source.get("github_issue_types")
        if isinstance(fallback, dict) and _has_type_id_mapping(fallback):
            return dict(fallback)
        return {}

    spec_settings: dict[str, Any] = {}
    backlog_cfg = load_backlog_config_from_backlog_file(repo_path / ".specfact" / "backlog-config.yaml")
    spec_config = backlog_cfg or load_backlog_config_from_spec(repo_path / ".specfact" / "spec.yaml")
    if spec_config is not None:
        github_provider = spec_config.providers.get("github")
        if github_provider is not None and isinstance(github_provider.settings, dict):
            spec_settings = dict(github_provider.settings)

    template_cfg = _extract_github_project_v2(template_payload)
    spec_cfg = _extract_github_project_v2(spec_settings)
    custom_cfg = _extract_github_project_v2(custom_config)

    template_issue_types = _extract_github_issue_types(template_payload)
    spec_issue_types = _extract_github_issue_types(spec_settings)
    custom_issue_types = _extract_github_issue_types(custom_config)

    result: dict[str, Any] = {}

    if template_cfg or spec_cfg or custom_cfg:
        template_option_ids = template_cfg.get("type_option_ids")
        spec_option_ids = spec_cfg.get("type_option_ids")
        custom_option_ids = custom_cfg.get("type_option_ids")
        merged_option_ids: dict[str, Any] = {}
        if isinstance(template_option_ids, dict):
            merged_option_ids.update(template_option_ids)
        if isinstance(spec_option_ids, dict):
            merged_option_ids.update(spec_option_ids)
        if isinstance(custom_option_ids, dict):
            merged_option_ids.update(custom_option_ids)

        merged_cfg = {**template_cfg, **spec_cfg, **custom_cfg}
        if merged_option_ids:
            merged_cfg["type_option_ids"] = merged_option_ids
        if merged_cfg:
            result["github_project_v2"] = merged_cfg

    if template_issue_types or spec_issue_types or custom_issue_types:
        template_type_ids = template_issue_types.get("type_ids")
        spec_type_ids = spec_issue_types.get("type_ids")
        custom_type_ids = custom_issue_types.get("type_ids")
        merged_type_ids: dict[str, Any] = {}
        if isinstance(template_type_ids, dict):
            merged_type_ids.update(template_type_ids)
        if isinstance(spec_type_ids, dict):
            merged_type_ids.update(spec_type_ids)
        if isinstance(custom_type_ids, dict):
            merged_type_ids.update(custom_type_ids)

        issue_type_cfg = {**template_issue_types, **spec_issue_types, **custom_issue_types}
        if merged_type_ids:
            issue_type_cfg["type_ids"] = merged_type_ids
        if issue_type_cfg:
            result["github_issue_types"] = issue_type_cfg

    return result or None


@beartype
def _has_github_repo_issue_type_mapping(provider_fields: dict[str, Any] | None, issue_type: str) -> bool:
    """Return True when repository GitHub issue-type mapping metadata is available."""
    if not isinstance(provider_fields, dict):
        return False
    issue_cfg = provider_fields.get("github_issue_types")
    if not isinstance(issue_cfg, dict):
        return False
    type_ids = issue_cfg.get("type_ids")
    if not isinstance(type_ids, dict):
        return False
    normalized = issue_type.strip().lower()
    mapped = str(type_ids.get(issue_type) or type_ids.get(normalized) or "").strip()
    if mapped:
        return True
    if normalized == "story":
        fallback = str(type_ids.get("feature") or type_ids.get("Feature") or "").strip()
        return bool(fallback)
    return False


@beartype
def _resolve_parent_id(parent_ref: str, graph_items: dict[str, Any]) -> tuple[str | None, str | None]:
    normalized_ref = parent_ref.strip().lower()

    for item_id, item in graph_items.items():
        key = str(getattr(item, "key", "") or "").lower()
        title = str(getattr(item, "title", "") or "").lower()
        if normalized_ref in {item_id.lower(), key, title}:
            return item_id, _extract_item_type(item)

    return None, None


@beartype
def _validate_parent(child_type: str, parent_type: str, hierarchy: dict[str, list[str]]) -> bool:
    allowed = hierarchy.get(child_type, [])
    if not allowed:
        return True
    return parent_type in allowed


@beartype
def _choose_parent_interactively(
    issue_type: str,
    graph_items: dict[str, Any],
    hierarchy: dict[str, list[str]],
) -> str | None:
    """Interactively choose parent from existing hierarchy-compatible items."""
    add_parent_choice = _select_with_fallback("Add parent issue?", ["yes", "no"], default="yes")
    if add_parent_choice.strip().lower() != "yes":
        return None

    allowed = set(hierarchy.get(issue_type, []))
    all_candidates: list[tuple[str, str]] = []
    candidates: list[tuple[str, str]] = []
    for item_id, item in graph_items.items():
        parent_type = _extract_item_type(item)
        key = str(getattr(item, "key", item_id) or item_id)
        title = str(getattr(item, "title", "") or "")
        label = f"{key} | {title} | type={parent_type}" if title else f"{key} | type={parent_type}"
        all_candidates.append((label, item_id))
        if allowed and parent_type not in allowed:
            continue
        candidates.append((label, item_id))

    if not candidates:
        if all_candidates:
            print_warning(
                "No hierarchy-compatible parent candidates found from inferred types. "
                "Showing all issues so you can choose a parent manually."
            )
            candidates = all_candidates
        else:
            print_warning("No hierarchy-compatible parent candidates found. Continuing without parent.")
            return None

    options = ["(no parent)"] + [label for label, _ in candidates]
    default_option = options[1] if len(options) > 1 else options[0]
    selected = _select_with_fallback("Select parent issue", options, default=default_option)
    if selected == "(no parent)":
        return None

    mapping = dict(candidates)
    return mapping.get(selected)


@beartype
def _parse_story_points(raw_value: str | None) -> int | float | None:
    if raw_value is None:
        return None
    stripped = raw_value.strip()
    if not stripped:
        return None
    try:
        if "." in stripped:
            return float(stripped)
        return int(stripped)
    except ValueError:
        print_warning(f"Invalid story points '{raw_value}', keeping as text")
        return None


@beartype
def add(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    template: Annotated[str | None, typer.Option("--template", help="Template name for mapping")] = None,
    issue_type: Annotated[str | None, typer.Option("--type", help="Issue type (story/task/feature/...)")] = None,
    parent: Annotated[str | None, typer.Option("--parent", help="Parent issue id/key/title")] = None,
    title: Annotated[str | None, typer.Option("--title", help="Issue title")] = None,
    body: Annotated[str | None, typer.Option("--body", help="Issue body/description")] = None,
    acceptance_criteria: Annotated[
        str | None,
        typer.Option("--acceptance-criteria", help="Acceptance criteria text (recommended for story-like items)"),
    ] = None,
    priority: Annotated[str | None, typer.Option("--priority", help="Priority value (for example 1, high, P1)")] = None,
    story_points: Annotated[
        str | None, typer.Option("--story-points", help="Story points value (integer/float)")
    ] = None,
    sprint: Annotated[str | None, typer.Option("--sprint", help="Sprint/iteration assignment")] = None,
    body_end_marker: Annotated[
        str,
        typer.Option("--body-end-marker", help="End marker for interactive multiline input"),
    ] = "::END::",
    description_format: Annotated[
        str,
        typer.Option("--description-format", help="Description format: markdown or classic"),
    ] = "markdown",
    non_interactive: Annotated[bool, typer.Option("--non-interactive", help="Disable prompts")] = False,
    check_dor: Annotated[
        bool, typer.Option("--check-dor", help="Validate Definition of Ready before creation")
    ] = False,
    repo_path: Annotated[Path, typer.Option("--repo-path", help="Repository path for DoR config")] = Path("."),
    custom_config: Annotated[
        Path | None, typer.Option("--custom-config", help="Path to custom hierarchy/config YAML")
    ] = None,
    custom_field: Annotated[
        list[str] | None,
        typer.Option(
            "--custom-field", help="Custom field entry '<canonical-or-provider-key>=<value>'", metavar="KEY=VALUE"
        ),
    ] = None,
) -> None:
    """Create a backlog item with optional parent hierarchy validation and DoR checks."""
    adapter_instance = AdapterRegistry.get_adapter(adapter)
    interactive_mode = not non_interactive

    if non_interactive:
        missing = [
            name for name, value in {"type": issue_type, "title": title}.items() if not (value and value.strip())
        ]
        if missing:
            print_error(f"{', '.join(missing)} required in --non-interactive mode")
            raise typer.Exit(code=1)
    else:
        issue_type_choices = sorted(set(DEFAULT_CREATION_HIERARCHY.keys()))
        if not issue_type:
            issue_type = _select_with_fallback("Select issue type", issue_type_choices, default="story")
        if not title:
            title = prompt_text("Issue title")
        if body is None:
            body = _prompt_multiline_text("Issue body", body_end_marker)
        if sprint is None:
            sprint = _interactive_sprint_selection(adapter, adapter_instance, project_id)
        description_format = _select_with_fallback(
            "Select description format",
            ["markdown", "classic"],
            default=description_format or "markdown",
        ).lower()

        normalized_issue_type = _normalize_type(issue_type or "")
        if normalized_issue_type in STORY_LIKE_TYPES and acceptance_criteria is None:
            capture_ac = _select_with_fallback("Add acceptance criteria?", ["yes", "no"], default="yes")
            if capture_ac.strip().lower() == "yes":
                acceptance_criteria = _prompt_multiline_text("Acceptance criteria", body_end_marker)

        if priority is None:
            priority_raw = prompt_text("Priority (optional)", default="", required=False).strip()
            priority = priority_raw or None

        if story_points is None and normalized_issue_type in STORY_LIKE_TYPES:
            story_points = prompt_text("Story points (optional)", default="", required=False).strip() or None

    assert issue_type is not None
    assert title is not None
    issue_type = _normalize_type(issue_type)
    title = title.strip()
    body = (body or "").strip()
    acceptance_criteria = (acceptance_criteria or "").strip() or None
    priority = (priority or "").strip() or None

    description_format = (description_format or "markdown").strip().lower()
    if description_format not in {"markdown", "classic"}:
        print_error("description-format must be one of: markdown, classic")
        raise typer.Exit(code=1)

    parsed_story_points = _parse_story_points(story_points)

    graph_adapter = require_backlog_graph_protocol(adapter_instance)

    template = _resolve_default_template(adapter, template)
    print_info("Input captured. Preparing backlog context and validations before create...")

    resolved_custom_config = _resolve_custom_config_path(adapter, custom_config)
    custom = _load_custom_config(resolved_custom_config)
    template_payload = _load_template_config(template)

    fetch_filters = dict(custom.get("filters") or {})
    if adapter.strip().lower() == "ado":
        fetch_filters.setdefault("use_current_iteration_default", False)
    items = graph_adapter.fetch_all_issues(project_id, filters=fetch_filters)
    relationships = graph_adapter.fetch_relationships(project_id)

    graph = (
        BacklogGraphBuilder(
            provider=adapter,
            template_name=template,
            custom_config={**custom, "project_key": project_id},
        )
        .add_items(items)
        .add_dependencies(relationships)
        .build()
    )

    hierarchy = _derive_creation_hierarchy(template_payload, custom)

    parent_id: str | None = None
    if parent:
        parent_id, parent_type = _resolve_parent_id(parent, graph.items)
        if not parent_id or not parent_type:
            print_error(f"Parent '{parent}' not found")
            raise typer.Exit(code=1)
        if not _validate_parent(issue_type, parent_type, hierarchy):
            allowed = hierarchy.get(issue_type, [])
            print_error(
                f"Type '{issue_type}' is not allowed under parent type '{parent_type}'. "
                f"Allowed parent types: {', '.join(allowed) if allowed else '(any)'}"
            )
            raise typer.Exit(code=1)
    elif interactive_mode:
        parent_id = _choose_parent_interactively(issue_type, graph.items, hierarchy)

    payload: dict[str, Any] = {
        "type": issue_type,
        "title": title,
        "description": body,
        "description_format": description_format,
    }
    if acceptance_criteria:
        payload["acceptance_criteria"] = acceptance_criteria
    if priority:
        payload["priority"] = priority
    if parsed_story_points is not None:
        payload["story_points"] = parsed_story_points
    if parent_id:
        payload["parent_id"] = parent_id
    if sprint:
        payload["sprint"] = sprint

    provider_fields = _resolve_provider_fields_for_create(adapter, template_payload, custom, repo_path)
    if adapter.strip().lower() == "ado":
        try:
            ado_provider_fields = _resolve_ado_custom_fields(repo_path, issue_type, custom_field)
        except ValueError as error:
            print_error(str(error))
            raise typer.Exit(code=1) from error
        if ado_provider_fields:
            provider_fields = dict(provider_fields or {})
            provider_fields.update(ado_provider_fields)
    if provider_fields:
        payload["provider_fields"] = provider_fields

    if adapter.strip().lower() == "github" and not _has_github_repo_issue_type_mapping(provider_fields, issue_type):
        print_warning(
            "GitHub repository issue-type mapping is not configured for this issue type; "
            "issue type may fall back to labels/body only. Configure "
            "backlog_config.providers.github.settings.github_issue_types.type_ids "
            "(ProjectV2 mapping is optional) to enable automatic issue Type updates."
        )

    if check_dor:
        dor_config = DefinitionOfReady.load_from_repo(repo_path)
        if dor_config:
            draft = {
                "id": "DRAFT",
                "title": title,
                "body_markdown": body,
                "description": body,
                "type": issue_type,
                "provider_fields": {
                    "acceptance_criteria": acceptance_criteria,
                    "priority": priority,
                    "story_points": parsed_story_points,
                },
            }
            dor_errors = dor_config.validate_item(draft)
            if dor_errors:
                print_warning("Definition of Ready (DoR) issues detected:")
                for err in dor_errors:
                    print_warning(err)
                raise typer.Exit(code=1)
            print_info("Definition of Ready (DoR) satisfied")

    create_context = f"adapter={adapter}, format={description_format}"
    if sprint:
        create_context += f", sprint={sprint}"
    if parent_id:
        create_context += ", parent=selected"
    print_info(f"Creating backlog item now ({create_context})...")

    try:
        created = graph_adapter.create_issue(project_id, payload)
    except (requests.Timeout, requests.ConnectionError) as error:
        print_warning("Create request failed after send; item may already exist remotely.")
        print_warning("Verify backlog for the title/key before retrying to avoid duplicates.")
        raise typer.Exit(code=1) from error
    print_success("Issue created successfully")
    print_info(f"id: {created.get('id', '')}")
    print_info(f"key: {created.get('key', '')}")
    print_info(f"url: {created.get('url', '')}")
