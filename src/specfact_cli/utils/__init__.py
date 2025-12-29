"""
SpecFact CLI utilities.

This package contains utility functions for git operations,
YAML processing, console output, and interactive prompts.
"""

from specfact_cli.utils.console import console, print_validation_report
from specfact_cli.utils.content_sanitizer import ContentSanitizer
from specfact_cli.utils.feature_keys import (
    convert_feature_keys,
    find_feature_by_normalized_key,
    normalize_feature_key,
    to_classname_key,
    to_sequential_key,
    to_underscore_key,
)
from specfact_cli.utils.git import GitOperations
from specfact_cli.utils.progress import (
    create_progress_callback,
    load_bundle_with_progress,
    save_bundle_with_progress,
)
from specfact_cli.utils.prompts import (
    display_summary,
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
    prompt_confirm,
    prompt_dict,
    prompt_list,
    prompt_text,
)
from specfact_cli.utils.structured_io import (
    StructuredFormat,
    dump_structured_file,
    dumps_structured_data,
    load_structured_file,
    loads_structured_data,
    structured_extension,
)
from specfact_cli.utils.yaml_utils import YAMLUtils, dump_yaml, load_yaml, string_to_yaml, yaml_to_string


__all__ = [
    "ContentSanitizer",
    "GitOperations",
    "StructuredFormat",
    "YAMLUtils",
    "console",
    "convert_feature_keys",
    "create_progress_callback",
    "display_summary",
    "dump_structured_file",
    "dump_yaml",
    "dumps_structured_data",
    "find_feature_by_normalized_key",
    "load_bundle_with_progress",
    "load_structured_file",
    "load_yaml",
    "loads_structured_data",
    "normalize_feature_key",
    "print_error",
    "print_info",
    "print_section",
    "print_success",
    "print_validation_report",
    "print_warning",
    "prompt_confirm",
    "prompt_dict",
    "prompt_list",
    "prompt_text",
    "save_bundle_with_progress",
    "string_to_yaml",
    "structured_extension",
    "to_classname_key",
    "to_sequential_key",
    "to_underscore_key",
    "yaml_to_string",
]
