"""Typed predicates for icontract (basedpyright-friendly; avoids Unknown in lambdas)."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.backlog_item import BacklogItem


@require(lambda repo_path: isinstance(repo_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def repo_path_exists(repo_path: Path) -> bool:
    return repo_path.exists()


@require(lambda repo_path: isinstance(repo_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def repo_path_is_dir(repo_path: Path) -> bool:
    return repo_path.is_dir()


@require(lambda repo_path: repo_path is None or isinstance(repo_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def optional_repo_path_exists(repo_path: Path | None) -> bool:
    return repo_path is None or repo_path.exists()


@require(lambda path: isinstance(path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def path_exists(path: Path) -> bool:
    return path.exists()


@require(lambda bundle_dir: isinstance(bundle_dir, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def bundle_dir_exists(bundle_dir: Path) -> bool:
    return bundle_dir.exists()


@require(lambda file_path: isinstance(file_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def file_path_exists(file_path: Path) -> bool:
    return file_path.exists()


@require(lambda settings_relative: isinstance(settings_relative, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def settings_relative_nonblank(settings_relative: str) -> bool:
    stripped = settings_relative.strip()
    if stripped == "":
        return False
    path = Path(stripped)
    if path.is_absolute():
        return False
    return all(part != ".." for part in path.parts)


@require(lambda prompt_files: isinstance(prompt_files, list))
@ensure(lambda result: isinstance(result, bool))
@beartype
def prompt_files_all_strings(prompt_files: list[str]) -> bool:
    return all(isinstance(item, str) for item in prompt_files)


@require(lambda template_path: isinstance(template_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def template_path_exists(template_path: Path) -> bool:
    return template_path.exists()


@require(lambda template_path: isinstance(template_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def template_path_is_file(template_path: Path) -> bool:
    return template_path.is_file()


@require(lambda report_path: isinstance(report_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def report_path_is_parseable_repro(report_path: Path) -> bool:
    return report_path.exists() and report_path.suffix in (".yaml", ".yml", ".json") and report_path.is_file()


@require(lambda class_name: isinstance(class_name, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def class_name_nonblank(class_name: str) -> bool:
    return class_name.strip() != ""


@require(lambda title, prefix: isinstance(title, str) and isinstance(prefix, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def feature_title_nonblank(title: str, prefix: str = "000") -> bool:
    return title.strip() != ""


@require(lambda target_key: isinstance(target_key, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def target_key_nonblank(target_key: str) -> bool:
    return target_key.strip() != ""


@require(lambda maybe_path: maybe_path is None or isinstance(maybe_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def vscode_settings_result_ok(maybe_path: Path | None) -> bool:
    """Used by tests and as ``lambda result: vscode_settings_result_ok(result)`` on ``create_vscode_settings``."""
    return maybe_path is None or maybe_path.exists()


@require(lambda plan_path: isinstance(plan_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def plan_path_exists(plan_path: Path) -> bool:
    return plan_path.exists()


@require(lambda plan_path: isinstance(plan_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def plan_path_is_file(plan_path: Path) -> bool:
    return plan_path.is_file()


@require(lambda tasks_path: isinstance(tasks_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def tasks_path_exists(tasks_path: Path) -> bool:
    return tasks_path.exists()


@require(lambda tasks_path: isinstance(tasks_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def tasks_path_is_file(tasks_path: Path) -> bool:
    return tasks_path.is_file()


@require(lambda file_path: isinstance(file_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def file_path_is_file(file_path: Path) -> bool:
    return file_path.is_file()


@require(lambda spec_path: isinstance(spec_path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def spec_path_exists(spec_path: Path) -> bool:
    return spec_path.exists()


@require(lambda old_spec: isinstance(old_spec, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def old_spec_exists(old_spec: Path) -> bool:
    return old_spec.exists()


@require(lambda new_spec: isinstance(new_spec, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def new_spec_exists(new_spec: Path) -> bool:
    return new_spec.exists()


@require(lambda updated, original: isinstance(updated, BacklogItem) and isinstance(original, BacklogItem))
@ensure(lambda result: isinstance(result, bool))
@beartype
def backlog_update_preserves_identity(updated: BacklogItem, original: BacklogItem) -> bool:
    return updated.id == original.id and updated.provider == original.provider


@require(lambda comment: isinstance(comment, str))
@ensure(lambda result: isinstance(result, bool))
@beartype
def comment_nonblank(comment: str) -> bool:
    return comment.strip() != ""


@require(lambda path: isinstance(path, Path))
@ensure(lambda result: isinstance(result, bool))
@beartype
def path_exists_and_yaml_suffix(path: Path) -> bool:
    return path.exists() and path.suffix == ".yml"
