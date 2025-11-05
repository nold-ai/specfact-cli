"""
SpecFact CLI utilities.

This package contains utility functions for git operations,
YAML processing, console output, and interactive prompts.
"""

from specfact_cli.utils.console import console, print_validation_report
from specfact_cli.utils.feature_keys import (
    convert_feature_keys,
    find_feature_by_normalized_key,
    normalize_feature_key,
    to_classname_key,
    to_sequential_key,
    to_underscore_key,
)
from specfact_cli.utils.git import GitOperations
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
from specfact_cli.utils.yaml_utils import YAMLUtils, dump_yaml, load_yaml, string_to_yaml, yaml_to_string


__all__ = [
    "GitOperations",
    "YAMLUtils",
    "console",
    "convert_feature_keys",
    "display_summary",
    "dump_yaml",
    "find_feature_by_normalized_key",
    "load_yaml",
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
    "string_to_yaml",
    "to_classname_key",
    "to_sequential_key",
    "to_underscore_key",
    "yaml_to_string",
]
