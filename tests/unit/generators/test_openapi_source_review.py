"""Regressions for source-only HTTP example extraction."""

from pathlib import Path
from textwrap import dedent

import pytest

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


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "def test_first(client):\n"
            "    response = client.post('/items', json={'x': 1})\n"
            "    assert response.json() == {'error': True}\n"
            "def test_second(client):\n"
            "    response = client.post('/items', json={'x': 2})\n"
            "    assert response.status_code == 201\n",
            [("/items", {"x": 2}, 201, None)],
        ),
        (
            "def test_import():\n    remote = None\n    import requests as remote\n    remote.get('/healthy')\n",
            [("/healthy", {}, None, None)],
        ),
        (
            "def test_import(client):\n"
            "    requests = client.get('/first')\n"
            "    assert requests.status_code == 200\n"
            "    import requests\n"
            "    assert requests.status_code == 404\n"
            "    requests.get('/healthy')\n",
            [("/first", {}, 200, None), ("/healthy", {}, None, None)],
        ),
        (
            "from contextlib import nullcontext\n"
            "def test_context(client, other):\n"
            "    response = client.get('/health')\n"
            "    assert response.status_code == 200\n"
            "    with nullcontext(other) as response:\n"
            "        assert response.status_code == 404\n",
            [("/health", {}, 200, None)],
        ),
        (
            "import requests\ndef test_url():\n    requests.get(url='/health')\n",
            [("/health", {}, None, None)],
        ),
        (
            "def test_collision(client):\n    client.get('/a-b')\n    client.get('/a/b')\n    client.get('/a-b/2')\n",
            [("/a-b", {}, None, None), ("/a-b/2", {}, None, None), ("/a/b", {}, None, None)],
        ),
        (
            "def test_data(client):\n"
            "    client.post('/array', json=[{'name': 'Jo'}])\n"
            "    client.post('/empty', json=[], data={'ignore': True})\n",
            [("/array", [{"name": "Jo"}], None, None), ("/empty", [], None, None)],
        ),
        (
            "def test_scores(client):\n"
            "    client.post('/array', json=[-1, -2.5, +3])\n"
            "    client.post('/scalar', json=-1)\n",
            [("/array", [-1, -2.5, 3], None, None), ("/scalar", -1, None, None)],
        ),
    ],
)
def test_literal_openapi_examples_preserve_request_and_response_identity(
    tmp_path: Path, source: str, expected: list[tuple[str, object, int | None, object]]
) -> None:
    test_path = tmp_path / "test_example.py"
    test_path.write_text(source, encoding="utf-8")
    examples = OpenAPITestConverter(tmp_path).extract_examples_from_tests([test_path.name])

    assert (
        sorted(
            (item["request"]["path"], item["request"]["body"], item.get("status_code"), item.get("response"))
            for item in examples.values()
        )
        == expected
    )
