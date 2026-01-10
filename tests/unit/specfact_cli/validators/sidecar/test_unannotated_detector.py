"""
Unit tests for unannotated code detector.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from specfact_cli.validators.sidecar.unannotated_detector import (
    detect_unannotated_functions,
    detect_unannotated_in_repo,
)


class TestDetectUnannotatedFunctions:
    """Test unannotated function detection."""

    def test_detect_function_with_beartype(self) -> None:
        """Test detection of function with beartype decorator."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(
                """
from beartype import beartype

@beartype
def annotated_function(x: int) -> int:
    return x * 2
"""
            )

            result = detect_unannotated_functions(test_file)

            assert len(result) == 0

    def test_detect_function_with_icontract(self) -> None:
        """Test detection of function with icontract decorator."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(
                """
from icontract import require, ensure

@require(lambda x: x > 0)
@ensure(lambda result: result > 0)
def annotated_function(x: int) -> int:
    return x * 2
"""
            )

            result = detect_unannotated_functions(test_file)

            assert len(result) == 0

    def test_detect_unannotated_function(self) -> None:
        """Test detection of unannotated function."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(
                """
def unannotated_function(x):
    return x * 2
"""
            )

            result = detect_unannotated_functions(test_file)

            assert len(result) == 1
            assert result[0]["name"] == "unannotated_function"
            assert result[0]["has_icontract"] is False
            assert result[0]["has_beartype"] is False

    def test_detect_mixed_functions(self) -> None:
        """Test detection with mix of annotated and unannotated functions."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(
                """
from beartype import beartype
from icontract import require

@beartype
def annotated1(x: int) -> int:
    return x * 2

def unannotated1(x):
    return x * 2

@require(lambda x: x > 0)
def annotated2(x: int) -> int:
    return x * 2

def unannotated2(y):
    return y + 1
"""
            )

            result = detect_unannotated_functions(test_file)

            assert len(result) == 2
            assert result[0]["name"] == "unannotated1"
            assert result[1]["name"] == "unannotated2"

    def test_detect_class_methods(self) -> None:
        """Test detection of unannotated class methods."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(
                """
class MyClass:
    def unannotated_method(self, x):
        return x * 2

    @beartype
    def annotated_method(self, x: int) -> int:
        return x * 2
"""
            )

            result = detect_unannotated_functions(test_file)

            # Should detect unannotated method
            assert len(result) >= 1
            assert any(f["name"] == "unannotated_method" for f in result)

    def test_skip_test_files(self) -> None:
        """Test that test files are skipped in repo detection."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_dir = repo_path / "src"
            src_dir.mkdir()
            test_dir = repo_path / "tests"
            test_dir.mkdir()

            # Create source file with unannotated function
            src_file = src_dir / "module.py"
            src_file.write_text("def unannotated(x): return x")

            # Create test file with unannotated function
            test_file = test_dir / "test_module.py"
            test_file.write_text("def test_function(x): return x")

            result = detect_unannotated_in_repo(repo_path)

            # Should only find source file function, not test file
            assert len(result) == 1
            assert result[0]["name"] == "unannotated"

    def test_detect_in_repo(self) -> None:
        """Test detection across repository."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_dir = repo_path / "src"
            src_dir.mkdir()

            # Create multiple files
            file1 = src_dir / "module1.py"
            file1.write_text("def func1(x): return x")

            file2 = src_dir / "module2.py"
            file2.write_text(
                """
from beartype import beartype

@beartype
def func2(x: int) -> int:
    return x

def func3(x):
    return x
"""
            )

            result = detect_unannotated_in_repo(repo_path)

            # Should find func1 and func3, but not func2
            assert len(result) == 2
            names = {f["name"] for f in result}
            assert "func1" in names
            assert "func3" in names
            assert "func2" not in names
