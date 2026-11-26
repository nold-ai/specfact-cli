"""Regressions for source-only HTTP example extraction."""

from pathlib import Path
from textwrap import dedent

from specfact_cli.generators.test_to_openapi import OpenAPITestConverter


def test_selected_test_keeps_its_own_request_and_response(tmp_path: Path) -> None:
    (tmp_path / "test_api.py").write_text(
        dedent("""
            def test_create():
                response = client.post("/users")
                def helper():
                    response = client.get("/health")
                assert response.status_code == 201
        """),
        encoding="utf-8",
    )
    result = OpenAPITestConverter(tmp_path).extract_examples_from_tests(["test_api.py::test_create"])
    assert set(result) == {"post_users"}
    assert result["post_users"]["status_code"] == 201


def test_only_http_receivers_and_literal_paths_create_operations(tmp_path: Path) -> None:
    (tmp_path / "test_api.py").write_text(
        dedent("""
            import requests as http

            def test_list():
                client.get(url)
                client.get(f"/users/{user_id}")
                payload.get("id")
                client.get("/users")
                http.get("/health")
                client = {"name": "value"}
                client.get("name")
        """),
        encoding="utf-8",
    )
    result = OpenAPITestConverter(tmp_path).extract_examples_from_tests(["test_api.py::test_list"])
    assert set(result) == {"get_users", "get_health"}
