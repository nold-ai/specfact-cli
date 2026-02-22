"""Unit tests for centralized backlog adapter retry behavior."""

from __future__ import annotations

import requests

from specfact_cli.adapters.backlog_base import BacklogAdapterMixin


class _DummyRetryAdapter(BacklogAdapterMixin):
    def map_backlog_status_to_openspec(self, status: str) -> str:
        return status

    def map_openspec_status_to_backlog(self, status: str) -> str | list[str]:
        return status

    def create_issue(self, project_id: str, payload: dict[str, object]) -> dict[str, object]:
        _ = project_id, payload
        return {}

    def extract_change_proposal_data(self, item_data: dict[str, object]) -> dict[str, object]:
        _ = item_data
        return {}


class _Response:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error

    def json(self) -> dict:
        return self._payload


def test_request_with_retry_retries_transient_status_then_succeeds(monkeypatch) -> None:
    adapter = _DummyRetryAdapter()
    monkeypatch.setattr("specfact_cli.adapters.backlog_base.time.sleep", lambda _seconds: None)

    calls = {"count": 0}

    def _request() -> _Response:
        calls["count"] += 1
        if calls["count"] < 3:
            return _Response(503)
        return _Response(200, {"ok": True})

    response = adapter._request_with_retry(_request)

    assert response.status_code == 200
    assert calls["count"] == 3


def test_request_with_retry_does_not_retry_non_transient_http_error(monkeypatch) -> None:
    adapter = _DummyRetryAdapter()
    monkeypatch.setattr("specfact_cli.adapters.backlog_base.time.sleep", lambda _seconds: None)

    calls = {"count": 0}

    def _request() -> _Response:
        calls["count"] += 1
        return _Response(400)

    try:
        adapter._request_with_retry(_request)
    except requests.HTTPError as error:
        assert error.response is not None
        assert error.response.status_code == 400
    else:
        raise AssertionError("Expected HTTPError")

    assert calls["count"] == 1


def test_request_with_retry_retries_connection_error_then_succeeds(monkeypatch) -> None:
    adapter = _DummyRetryAdapter()
    monkeypatch.setattr("specfact_cli.adapters.backlog_base.time.sleep", lambda _seconds: None)

    calls = {"count": 0}

    def _request() -> _Response:
        calls["count"] += 1
        if calls["count"] < 2:
            raise requests.ConnectionError("network")
        return _Response(200)

    response = adapter._request_with_retry(_request)

    assert response.status_code == 200
    assert calls["count"] == 2


def test_request_with_retry_does_not_retry_transport_when_ambiguous_disabled(monkeypatch) -> None:
    adapter = _DummyRetryAdapter()
    monkeypatch.setattr("specfact_cli.adapters.backlog_base.time.sleep", lambda _seconds: None)

    calls = {"count": 0}

    def _request() -> _Response:
        calls["count"] += 1
        raise requests.Timeout("timeout")

    try:
        adapter._request_with_retry(_request, retry_on_ambiguous_transport=False)
    except requests.Timeout:
        pass
    else:
        raise AssertionError("Expected Timeout")

    assert calls["count"] == 1
