"""Tests for shared retry policy usage across adapter write operations."""

from __future__ import annotations

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.adapters.github import GitHubAdapter


class _Resp:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_github_add_issue_comment_uses_duplicate_safe_retry(monkeypatch) -> None:
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", api_token="token", use_gh_cli=False)

    captured: dict[str, object] = {}

    def _capture_retry(_request_callable, **kwargs):
        captured.update(kwargs)
        return _Resp({})

    monkeypatch.setattr(adapter, "_request_with_retry", _capture_retry)

    adapter._add_issue_comment("nold-ai", "specfact-cli", 42, "hello")

    assert captured.get("retry_on_ambiguous_transport") is False


def test_github_update_issue_status_uses_default_retry_mode(monkeypatch) -> None:
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", api_token="token", use_gh_cli=False)

    captured: dict[str, object] = {}

    def _capture_retry(_request_callable, **kwargs):
        captured.update(kwargs)
        return _Resp({"number": 42, "html_url": "https://example.test/42", "state": "open"})

    monkeypatch.setattr(adapter, "_request_with_retry", _capture_retry)
    monkeypatch.setattr(adapter, "_get_status_comment", lambda *_args, **_kwargs: "")

    proposal_data = {
        "status": "in-progress",
        "title": "Change title",
        "source_tracking": {"source_id": 42},
    }

    result = adapter._update_issue_status(proposal_data, "nold-ai", "specfact-cli")

    assert result["issue_number"] == 42
    assert "retry_on_ambiguous_transport" not in captured


def test_ado_add_work_item_comment_uses_duplicate_safe_retry(monkeypatch) -> None:
    adapter = AdoAdapter(org="nold-ai", project="specfact-cli", api_token="token")

    captured: dict[str, object] = {}

    def _capture_retry(_request_callable, **kwargs):
        captured.update(kwargs)
        return _Resp({"id": 7})

    monkeypatch.setattr(adapter, "_request_with_retry", _capture_retry)

    result = adapter._add_work_item_comment("nold-ai", "specfact-cli", 101, "comment")

    assert result["comment_id"] == 7
    assert captured.get("retry_on_ambiguous_transport") is False


def test_ado_update_work_item_status_uses_default_retry_mode(monkeypatch) -> None:
    adapter = AdoAdapter(org="nold-ai", project="specfact-cli", api_token="token")

    captured: dict[str, object] = {}

    def _capture_retry(_request_callable, **kwargs):
        captured.update(kwargs)
        return _Resp({"_links": {"html": {"href": "https://example.test/workitem/101"}}})

    monkeypatch.setattr(adapter, "_request_with_retry", _capture_retry)

    proposal_data = {
        "status": "in-progress",
        "source_tracking": {"source_id": 101},
    }

    result = adapter._update_work_item_status(proposal_data, "nold-ai", "specfact-cli")

    assert result["work_item_id"] == 101
    assert "retry_on_ambiguous_transport" not in captured
