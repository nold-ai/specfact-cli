"""
Typed predicates for icontract @require / @ensure decorators.

icontract passes predicate parameters by name from the wrapped callable; lambdas
without annotations leave parameters as Unknown under strict basedpyright. These
helpers give Path/str/BacklogItem-typed parameters so member access is known.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.models.protocol import Protocol


@require(lambda repo_path: isinstance(repo_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_repo_path_exists(repo_path: Path) -> bool:
    return repo_path.exists()


@require(lambda repo_path: isinstance(repo_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_repo_path_is_dir(repo_path: Path) -> bool:
    return repo_path.is_dir()


@require(lambda bundle_dir: isinstance(bundle_dir, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_bundle_dir_exists(bundle_dir: Path) -> bool:
    return bundle_dir.exists()


@require(lambda plan_path: isinstance(plan_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_plan_path_exists(plan_path: Path) -> bool:
    return plan_path.exists()


@require(lambda plan_path: isinstance(plan_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_plan_path_is_file(plan_path: Path) -> bool:
    return plan_path.is_file()


@require(lambda tasks_path: isinstance(tasks_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_tasks_path_exists(tasks_path: Path) -> bool:
    return tasks_path.exists()


@require(lambda tasks_path: isinstance(tasks_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_tasks_path_is_file(tasks_path: Path) -> bool:
    return tasks_path.is_file()


@require(lambda file_path: isinstance(file_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_file_path_exists(file_path: Path) -> bool:
    return file_path.exists()


@require(lambda file_path: isinstance(file_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_file_path_is_file(file_path: Path) -> bool:
    return file_path.is_file()


@require(lambda spec_path: isinstance(spec_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_spec_path_exists(spec_path: Path) -> bool:
    return spec_path.exists()


@require(lambda old_spec: isinstance(old_spec, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_old_spec_exists(old_spec: Path) -> bool:
    return old_spec.exists()


@require(lambda new_spec: isinstance(new_spec, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_new_spec_exists(new_spec: Path) -> bool:
    return new_spec.exists()


@require(lambda updated, original: isinstance(updated, BacklogItem) and isinstance(original, BacklogItem))
@ensure(lambda result: isinstance(result, bool))
@beartype
def ensure_backlog_update_preserves_identity(updated: BacklogItem, original: BacklogItem) -> bool:
    return updated.id == original.id and updated.provider == original.provider


@require(lambda comment: isinstance(comment, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_comment_non_whitespace(comment: str) -> bool:
    return comment.strip() != ""


@require(lambda text: isinstance(text, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_stripped_nonempty(text: str) -> bool:
    return text.strip() != ""


@require(lambda namespace: isinstance(namespace, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_namespace_stripped_nonempty(namespace: str) -> bool:
    return namespace.strip() != ""


@require(lambda key: isinstance(key, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_extension_key_nonempty(key: str) -> bool:
    return key.strip() != ""


@require(lambda path: isinstance(path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_path_exists(path: Path) -> bool:
    return path.exists()


@require(lambda path: isinstance(path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_path_parent_exists(path: Path) -> bool:
    return path.parent.exists()


@require(lambda output_path: isinstance(output_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_output_path_exists(output_path: Path) -> bool:
    return output_path.exists()


@require(lambda contract_path: isinstance(contract_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_contract_path_exists(contract_path: Path) -> bool:
    return contract_path.exists()


@require(lambda constitution_path: isinstance(constitution_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_constitution_path_exists(constitution_path: Path) -> bool:
    return constitution_path.exists()


@require(lambda pyproject_path: isinstance(pyproject_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_pyproject_path_exists(pyproject_path: Path) -> bool:
    return pyproject_path.exists()


@require(lambda package_json_path: isinstance(package_json_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_package_json_path_exists(package_json_path: Path) -> bool:
    return package_json_path.exists()


@require(lambda readme_path: isinstance(readme_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_readme_path_exists(readme_path: Path) -> bool:
    return readme_path.exists()


@require(lambda rules_dir: isinstance(rules_dir, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_rules_dir_exists(rules_dir: Path) -> bool:
    return rules_dir.exists()


@require(lambda rules_dir: isinstance(rules_dir, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_rules_dir_is_dir(rules_dir: Path) -> bool:
    return rules_dir.is_dir()


@require(lambda python_version: isinstance(python_version, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_python_version_is_3_x(python_version: str) -> bool:
    return python_version.startswith("3.")


@require(lambda protocol: isinstance(protocol, Protocol))
@ensure(lambda result: isinstance(result, bool))
@beartype
def require_protocol_has_states(protocol: Protocol) -> bool:
    return len(protocol.states) > 0


@require(lambda path: isinstance(path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def ensure_path_exists_yaml_suffix(path: Path) -> bool:
    return path.exists() and path.suffix == ".yml"


@require(lambda output_path: isinstance(output_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def ensure_github_workflow_output_suffix(output_path: Path) -> bool:
    return output_path.suffix == ".yml"


@require(lambda output_path: isinstance(output_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def ensure_yaml_output_suffix(output_path: Path) -> bool:
    return output_path.suffix in (".yml", ".yaml")
