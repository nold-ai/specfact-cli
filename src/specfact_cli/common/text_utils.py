"""
Text utility functions for SpecFact CLI modules
"""

import re
import textwrap

from beartype import beartype
from icontract import ensure, require


class TextUtils:
    """A utility class for text manipulation."""

    @staticmethod
    @beartype
    @require(lambda max_length: max_length > 0, "Max length must be positive")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return None or string")
    def shorten_text(text: str | None, max_length: int = 50) -> str | None:
        """Shorten text to a maximum length, appending '...' if truncated."""
        if text is None:
            return None
        return text if len(text) <= max_length else text[:max_length] + "..."

    @staticmethod
    @beartype
    @require(lambda code: isinstance(code, str), "Code must be string")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def clean_code(code: str) -> str:
        """
        Extract code from markdown triple-backtick fences. If multiple fenced
        blocks are present, only the first block is returned. Language hints
        (e.g. ```python) are stripped. Leading indentation inside the block is
        removed via ``textwrap.dedent`` to make assertions deterministic.
        """
        # Use regex that handles both real newline and literal \n inside the string.
        pattern = r"```(?:[a-zA-Z0-9_-]+)?(?:\\n|\n)([\s\S]*?)```"
        match = re.search(pattern, code)

        if not match:
            return code.strip()

        content = match.group(1)

        # Dedent and strip
        content = textwrap.dedent(content).strip()
        # If the cleaned content ends with a *literal* "\\n" sequence (common when the
        # source string itself contains escaped new-line characters), remove it so that
        # callers do not have to account for this artefact in expectations.
        if content.endswith("\\n"):
            content = content[:-2]
        return content
