"""Unit tests for backlog adapter create_issue contract."""

from __future__ import annotations

import sys
from pathlib import Path


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.adapters.github import GitHubAdapter


class _DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.status_code = 201
        self.ok = True
        self.text = ""

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_github_create_issue_maps_payload_and_returns_shape(monkeypatch) -> None:
    """GitHub create_issue sends issue payload and normalizes response fields."""
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", api_token="token", use_gh_cli=False)

    captured: dict = {}

    def _fake_post(url: str, json: dict, headers: dict, timeout: int):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _DummyResponse({"id": 77, "number": 42, "html_url": "https://github.com/nold-ai/specfact-cli/issues/42"})

    import specfact_cli.adapters.github as github_module

    monkeypatch.setattr(github_module.requests, "post", _fake_post)

    retry_call: dict[str, object] = {}

    def _capture_retry(request_callable, **kwargs):
        retry_call.update(kwargs)
        return request_callable()

    monkeypatch.setattr(adapter, "_request_with_retry", _capture_retry)

    result = adapter.create_issue(
        "nold-ai/specfact-cli",
        {
            "type": "story",
            "title": "Implement X",
            "description": "Acceptance criteria: ...",
            "acceptance_criteria": "Given/When/Then",
            "priority": "high",
            "story_points": 5,
            "parent_id": "100",
        },
    )

    assert retry_call.get("retry_on_ambiguous_transport") is False
    assert captured["url"].endswith("/repos/nold-ai/specfact-cli/issues")
    assert captured["json"]["title"] == "Implement X"
    labels = [label.lower() for label in captured["json"]["labels"]]
    assert "story" in labels
    assert "priority:high" in labels
    assert "story-points:5" in labels
    assert "acceptance criteria" in captured["json"]["body"].lower()
    assert result == {"id": "42", "key": "42", "url": "https://github.com/nold-ai/specfact-cli/issues/42"}


def test_ado_create_issue_maps_payload_and_parent_relation(monkeypatch) -> None:
    """ADO create_issue sends JSON patch and includes parent relation when provided."""
    adapter = AdoAdapter(org="nold-ai", project="specfact-cli", api_token="token")

    captured: dict = {}

    def _fake_patch(url: str, json: list, headers: dict, timeout: int):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _DummyResponse(
            {
                "id": 901,
                "url": "https://dev.azure.com/nold-ai/specfact-cli/_apis/wit/workItems/901",
                "_links": {
                    "html": {"href": "https://dev.azure.com/nold-ai/specfact-cli/_workitems/edit/901"},
                },
            }
        )

    import specfact_cli.adapters.ado as ado_module

    monkeypatch.setattr(ado_module.requests, "patch", _fake_patch)

    retry_call: dict[str, object] = {}

    def _capture_retry(request_callable, **kwargs):
        retry_call.update(kwargs)
        return request_callable()

    monkeypatch.setattr(adapter, "_request_with_retry", _capture_retry)

    result = adapter.create_issue(
        "nold-ai/specfact-cli",
        {
            "type": "story",
            "title": "Implement X",
            "description": "Acceptance criteria: ...",
            "acceptance_criteria": "Given/When/Then",
            "priority": 1,
            "story_points": 8,
            "sprint": "Project\\Release 1\\Sprint 3",
            "parent_id": "123",
            "description_format": "classic",
        },
    )

    assert retry_call.get("retry_on_ambiguous_transport") is False
    assert "/_apis/wit/workitems/$" in captured["url"]
    assert any(op.get("path") == "/fields/System.Title" and op.get("value") == "Implement X" for op in captured["json"])
    assert any(op.get("path") == "/relations/-" for op in captured["json"])
    assert any(
        op.get("path") == "/multilineFieldsFormat/System.Description" and op.get("value") == "Html"
        for op in captured["json"]
    )
    assert any(op.get("path") == "/fields/Microsoft.VSTS.Common.AcceptanceCriteria" for op in captured["json"])
    assert any(
        op.get("path") == "/fields/Microsoft.VSTS.Common.Priority" and op.get("value") == 1 for op in captured["json"]
    )
    assert any(
        op.get("path") == "/fields/Microsoft.VSTS.Scheduling.StoryPoints" and op.get("value") == 8
        for op in captured["json"]
    )
    assert any(
        op.get("path") == "/fields/System.IterationPath" and op.get("value") == "Project\\Release 1\\Sprint 3"
        for op in captured["json"]
    )
    assert result == {
        "id": "901",
        "key": "901",
        "url": "https://dev.azure.com/nold-ai/specfact-cli/_workitems/edit/901",
    }


def test_github_create_issue_sets_projects_type_field_when_configured(monkeypatch) -> None:
    """GitHub create_issue can set ProjectV2 Type field when config is provided."""
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", api_token="token", use_gh_cli=False)

    calls: list[tuple[str, dict]] = []

    def _fake_post(url: str, json: dict, headers: dict, timeout: int):
        _ = headers, timeout
        calls.append((url, json))
        if url.endswith("/issues"):
            return _DummyResponse(
                {
                    "id": 88,
                    "number": 55,
                    "node_id": "ISSUE_NODE_55",
                    "html_url": "https://github.com/nold-ai/specfact-cli/issues/55",
                }
            )
        if url.endswith("/graphql"):
            query = str(json.get("query") or "")
            if "addProjectV2ItemById" in query:
                return _DummyResponse({"data": {"addProjectV2ItemById": {"item": {"id": "PVT_ITEM_1"}}}})
            if "updateProjectV2ItemFieldValue" in query:
                return _DummyResponse(
                    {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVT_ITEM_1"}}}}
                )
            return _DummyResponse({"data": {}})
        raise AssertionError(f"Unexpected URL: {url}")

    import specfact_cli.adapters.github as github_module

    monkeypatch.setattr(github_module.requests, "post", _fake_post)

    result = adapter.create_issue(
        "nold-ai/specfact-cli",
        {
            "type": "story",
            "title": "Implement projects type",
            "description": "Body",
            "provider_fields": {
                "github_project_v2": {
                    "project_id": "PVT_PROJECT_1",
                    "type_field_id": "PVT_FIELD_TYPE",
                    "type_option_ids": {
                        "story": "PVT_OPTION_STORY",
                    },
                }
            },
        },
    )

    graphql_calls = [entry for entry in calls if entry[0].endswith("/graphql")]
    assert len(graphql_calls) == 2

    add_variables = graphql_calls[0][1]["variables"]
    assert add_variables == {"projectId": "PVT_PROJECT_1", "contentId": "ISSUE_NODE_55"}

    set_variables = graphql_calls[1][1]["variables"]
    assert set_variables["projectId"] == "PVT_PROJECT_1"
    assert set_variables["itemId"] == "PVT_ITEM_1"
    assert set_variables["fieldId"] == "PVT_FIELD_TYPE"
    assert set_variables["optionId"] == "PVT_OPTION_STORY"

    assert result == {"id": "55", "key": "55", "url": "https://github.com/nold-ai/specfact-cli/issues/55"}


def test_github_create_issue_sets_repository_issue_type_when_configured(monkeypatch) -> None:
    """GitHub create_issue sets repository issue Type when mapping is configured."""
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", api_token="token", use_gh_cli=False)

    calls: list[tuple[str, dict]] = []

    def _fake_post(url: str, json: dict, headers: dict, timeout: int):
        _ = headers, timeout
        calls.append((url, json))
        if url.endswith("/issues"):
            return _DummyResponse(
                {
                    "id": 188,
                    "number": 77,
                    "node_id": "ISSUE_NODE_77",
                    "html_url": "https://github.com/nold-ai/specfact-cli/issues/77",
                }
            )
        if url.endswith("/graphql"):
            query = str(json.get("query") or "")
            if "updateIssue(input:" in query:
                return _DummyResponse({"data": {"updateIssue": {"issue": {"id": "ISSUE_NODE_77"}}}})
            return _DummyResponse({"data": {}})
        raise AssertionError(f"Unexpected URL: {url}")

    import specfact_cli.adapters.github as github_module

    monkeypatch.setattr(github_module.requests, "post", _fake_post)

    result = adapter.create_issue(
        "nold-ai/specfact-cli",
        {
            "type": "task",
            "title": "Apply issue type",
            "description": "Body",
            "provider_fields": {
                "github_issue_types": {
                    "type_ids": {
                        "task": "IT_kwDODWwjB84Brk47",
                    }
                }
            },
        },
    )

    graphql_calls = [entry for entry in calls if entry[0].endswith("/graphql")]
    assert len(graphql_calls) == 1
    variables = graphql_calls[0][1]["variables"]
    assert variables == {"issueId": "ISSUE_NODE_77", "issueTypeId": "IT_kwDODWwjB84Brk47"}
    assert result == {"id": "77", "key": "77", "url": "https://github.com/nold-ai/specfact-cli/issues/77"}


def test_github_create_issue_links_native_parent_subissue(monkeypatch) -> None:
    """GitHub create_issue links parent relationship via native sidebar sub-issue mutation."""
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", api_token="token", use_gh_cli=False)

    calls: list[tuple[str, dict]] = []

    def _fake_post(url: str, json: dict, headers: dict, timeout: int):
        _ = headers, timeout
        calls.append((url, json))
        if url.endswith("/issues"):
            return _DummyResponse(
                {
                    "id": 288,
                    "number": 99,
                    "node_id": "ISSUE_NODE_99",
                    "html_url": "https://github.com/nold-ai/specfact-cli/issues/99",
                }
            )
        if url.endswith("/graphql"):
            query = str(json.get("query") or "")
            if "repository(owner:$owner, name:$repo)" in query and "issue(number:$number)" in query:
                return _DummyResponse({"data": {"repository": {"issue": {"id": "ISSUE_NODE_PARENT_11"}}}})
            if "addSubIssue(input:" in query:
                return _DummyResponse(
                    {
                        "data": {
                            "addSubIssue": {
                                "issue": {"id": "ISSUE_NODE_PARENT_11"},
                                "subIssue": {"id": "ISSUE_NODE_99"},
                            }
                        }
                    }
                )
            return _DummyResponse({"data": {}})
        raise AssertionError(f"Unexpected URL: {url}")

    import specfact_cli.adapters.github as github_module

    monkeypatch.setattr(github_module.requests, "post", _fake_post)

    result = adapter.create_issue(
        "nold-ai/specfact-cli",
        {
            "type": "task",
            "title": "Link native parent",
            "description": "Body",
            "parent_id": "11",
        },
    )

    graphql_calls = [entry for entry in calls if entry[0].endswith("/graphql")]
    assert len(graphql_calls) == 2

    lookup_variables = graphql_calls[0][1]["variables"]
    assert lookup_variables == {"owner": "nold-ai", "repo": "specfact-cli", "number": 11}

    link_variables = graphql_calls[1][1]["variables"]
    assert link_variables == {"parentIssueId": "ISSUE_NODE_PARENT_11", "subIssueId": "ISSUE_NODE_99"}
    assert result == {"id": "99", "key": "99", "url": "https://github.com/nold-ai/specfact-cli/issues/99"}
