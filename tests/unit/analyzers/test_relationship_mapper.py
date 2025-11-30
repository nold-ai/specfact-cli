"""
Tests for relationship mapper.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype

from specfact_cli.analyzers.relationship_mapper import RelationshipMapper


class TestRelationshipMapper:
    """Tests for RelationshipMapper."""

    @beartype
    def test_extract_imports(self, tmp_path: Path) -> None:
        """Test import extraction."""
        test_file = tmp_path / "test_imports.py"
        test_file.write_text(
            """
import os
import sys
from pathlib import Path
from typing import List, Dict
"""
        )

        mapper = RelationshipMapper(tmp_path)
        result = mapper.analyze_file(test_file)

        assert "os" in result["imports"]
        assert "sys" in result["imports"]
        assert "pathlib" in result["imports"]
        assert "typing" in result["imports"]

    @beartype
    def test_extract_interfaces(self, tmp_path: Path) -> None:
        """Test interface extraction."""
        test_file = tmp_path / "test_interfaces.py"
        test_file.write_text(
            '''
from abc import ABC, abstractmethod

class UserInterface(ABC):
    """Interface for user operations."""

    @abstractmethod
    def get_user(self, user_id: int):
        pass

    @abstractmethod
    def create_user(self, user_data: dict):
        pass
'''
        )

        mapper = RelationshipMapper(tmp_path)
        result = mapper.analyze_file(test_file)

        assert len(result["interfaces"]) == 1
        interface = result["interfaces"][0]
        assert interface["name"] == "UserInterface"
        assert "get_user" in interface["methods"]
        assert "create_user" in interface["methods"]

    @beartype
    def test_extract_routes(self, tmp_path: Path) -> None:
        """Test route extraction."""
        test_file = tmp_path / "test_routes.py"
        test_file.write_text(
            """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users():
    pass

@app.post("/users")
def create_user():
    pass
"""
        )

        mapper = RelationshipMapper(tmp_path)
        result = mapper.analyze_file(test_file)

        assert len(result["routes"]) == 2
        route_methods = [r["method"] for r in result["routes"]]
        assert "GET" in route_methods
        assert "POST" in route_methods

    @beartype
    def test_analyze_multiple_files(self, tmp_path: Path) -> None:
        """Test analyzing multiple files."""
        file1 = tmp_path / "file1.py"
        file1.write_text("import os")
        file2 = tmp_path / "file2.py"
        file2.write_text("from file1 import something")

        mapper = RelationshipMapper(tmp_path)
        result = mapper.analyze_files([file1, file2])

        assert len(result["imports"]) == 2
        assert "file1.py" in result["imports"] or "file1" in str(result["imports"])

    @beartype
    def test_get_relationship_graph(self, tmp_path: Path) -> None:
        """Test relationship graph generation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import os")

        mapper = RelationshipMapper(tmp_path)
        mapper.analyze_file(test_file)
        graph = mapper.get_relationship_graph()

        assert "nodes" in graph
        assert "edges" in graph
        assert "interfaces" in graph
        assert "routes" in graph
