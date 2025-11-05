"""
Feature key normalization and conversion utilities.

Provides functions to normalize feature keys across different formats
to enable consistent comparison and merging of plans.
"""

import re
from typing import Any

from beartype import beartype


@beartype
def normalize_feature_key(key: str) -> str:
    """
    Normalize feature keys for comparison by removing prefixes and underscores.

    Converts various formats to a canonical form:
    - `000_CONTRACT_FIRST_TEST_MANAGER` -> `CONTRACTFIRSTTESTMANAGER`
    - `FEATURE-CONTRACTFIRSTTESTMANAGER` -> `CONTRACTFIRSTTESTMANAGER`
    - `FEATURE-001` -> `001`
    - `CONTRACT_FIRST_TEST_MANAGER` -> `CONTRACTFIRSTTESTMANAGER`

    Args:
        key: Feature key in any format

    Returns:
        Normalized key (uppercase, no prefixes, no underscores)

    Examples:
        >>> normalize_feature_key("000_CONTRACT_FIRST_TEST_MANAGER")
        'CONTRACTFIRSTTESTMANAGER'
        >>> normalize_feature_key("FEATURE-CONTRACTFIRSTTESTMANAGER")
        'CONTRACTFIRSTTESTMANAGER'
        >>> normalize_feature_key("FEATURE-001")
        '001'
    """
    # Remove common prefixes
    key = key.replace("FEATURE-", "").replace("000_", "").replace("001_", "")

    # Remove underscores and spaces, convert to uppercase
    return re.sub(r"[_\s-]", "", key).upper()


@beartype
def to_sequential_key(key: str, index: int) -> str:
    """
    Convert any feature key to sequential format (FEATURE-001, FEATURE-002, ...).

    Args:
        key: Original feature key
        index: Sequential index (1-based)

    Returns:
        Sequential feature key (e.g., FEATURE-001)

    Examples:
        >>> to_sequential_key("000_CONTRACT_FIRST_TEST_MANAGER", 1)
        'FEATURE-001'
        >>> to_sequential_key("FEATURE-CONTRACTFIRSTTESTMANAGER", 5)
        'FEATURE-005'
    """
    return f"FEATURE-{index:03d}"


@beartype
def to_classname_key(class_name: str) -> str:
    """
    Convert class name to feature key format (FEATURE-CLASSNAME).

    Args:
        class_name: Class name (e.g., ContractFirstTestManager)

    Returns:
        Feature key (e.g., FEATURE-CONTRACTFIRSTTESTMANAGER)

    Examples:
        >>> to_classname_key("ContractFirstTestManager")
        'FEATURE-CONTRACTFIRSTTESTMANAGER'
        >>> to_classname_key("CodeAnalyzer")
        'FEATURE-CODEANALYZER'
    """
    return f"FEATURE-{class_name.upper()}"


@beartype
def to_underscore_key(title: str, prefix: str = "000") -> str:
    """
    Convert feature title to underscore format (000_FEATURE_NAME).

    Args:
        title: Feature title (e.g., "Contract First Test Manager")
        prefix: Prefix to use (default: "000")

    Returns:
        Feature key (e.g., 000_CONTRACT_FIRST_TEST_MANAGER)

    Examples:
        >>> to_underscore_key("Contract First Test Manager")
        '000_CONTRACT_FIRST_TEST_MANAGER'
        >>> to_underscore_key("User Authentication", "001")
        '001_USER_AUTHENTICATION'
    """
    # Convert title to uppercase and replace spaces with underscores
    key = title.upper().replace(" ", "_")

    return f"{prefix}_{key}"


@beartype
def find_feature_by_normalized_key(features: list, target_key: str) -> dict | None:
    """
    Find a feature in a list by matching normalized keys.

    Useful for comparing features across plans with different key formats.

    Args:
        features: List of feature dictionaries with 'key' field
        target_key: Target key to find (will be normalized)

    Returns:
        Feature dictionary if found, None otherwise

    Examples:
        >>> features = [{"key": "000_CONTRACT_FIRST_TEST_MANAGER", "title": "..."}]
        >>> find_feature_by_normalized_key(features, "FEATURE-CONTRACTFIRSTTESTMANAGER")
        {'key': '000_CONTRACT_FIRST_TEST_MANAGER', 'title': '...'}
    """
    target_normalized = normalize_feature_key(target_key)

    for feature in features:
        if "key" not in feature:
            continue

        feature_normalized = normalize_feature_key(feature["key"])
        if feature_normalized == target_normalized:
            return feature

    return None


@beartype
def convert_feature_keys(features: list, target_format: str = "sequential", start_index: int = 1) -> list:
    """
    Convert feature keys to a consistent format.

    Args:
        features: List of feature dictionaries with 'key' field
        target_format: Target format ('sequential', 'classname', or 'underscore')
        start_index: Starting index for sequential format (default: 1)

    Returns:
        List of features with converted keys

    Examples:
        >>> features = [{"key": "000_CONTRACT_FIRST_TEST_MANAGER", "title": "Contract First Test Manager"}]
        >>> convert_feature_keys(features, "sequential")
        [{'key': 'FEATURE-001', 'title': 'Contract First Test Manager', ...}]
    """
    converted: list[dict[str, Any]] = []
    current_index = start_index

    for feature in features:
        if "key" not in feature:
            continue

        original_key = feature["key"]
        title = feature.get("title", "")

        if target_format == "sequential":
            new_key = to_sequential_key(original_key, current_index)
            current_index += 1
        elif target_format == "classname":
            # Extract class name from original key if possible
            class_name = _extract_class_name(original_key, title)
            new_key = to_classname_key(class_name)
        elif target_format == "underscore":
            prefix = str(current_index - 1).zfill(3)
            new_key = to_underscore_key(title, prefix)
            current_index += 1
        else:
            # Keep original key if format not recognized
            new_key = original_key

        new_feature = feature.copy()
        new_feature["key"] = new_key
        converted.append(new_feature)

    return converted


def _extract_class_name(key: str, title: str) -> str:
    """Extract class name from feature key or title."""
    # Try to extract from key first
    if "FEATURE-" in key:
        class_part = key.replace("FEATURE-", "")
        # Convert to PascalCase if needed
        if "_" in class_part or "-" in class_part:
            # Convert underscore/hyphen to PascalCase
            parts = re.split(r"[_-]", class_part.lower())
            return "".join(word.capitalize() for word in parts)
        # Already class-like (uppercase), convert to PascalCase
        return class_part.title()

    # Fall back to title
    if title:
        # Convert title to PascalCase class name
        parts = re.split(r"[_\s-]", title)
        return "".join(word.capitalize() for word in parts)

    return "UnknownClass"
