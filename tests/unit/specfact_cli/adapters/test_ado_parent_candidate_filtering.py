"""Regression tests for ADO parent-candidate filtering behavior."""

from __future__ import annotations

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.models.backlog_item import BacklogItem


def _item(item_id: str, iteration: str | None) -> BacklogItem:
    return BacklogItem(
        id=item_id,
        provider="ado",
        url=f"https://example.test/{item_id}",
        title=f"Item {item_id}",
        state="open",
        iteration=iteration,
    )


def test_resolve_sprint_filter_skips_implicit_current_iteration_when_disabled(monkeypatch) -> None:
    adapter = AdoAdapter(org="nold-ai", project="specfact-cli", api_token="token")

    monkeypatch.setattr(adapter, "_get_current_iteration", lambda: "Project\\Sprint 42")

    items = [_item("1", None), _item("2", "Project\\Sprint 41")]

    resolved, filtered = adapter._resolve_sprint_filter(None, items, apply_current_when_missing=False)

    assert resolved is None
    assert [item.id for item in filtered] == ["1", "2"]


def test_resolve_sprint_filter_uses_current_iteration_by_default(monkeypatch) -> None:
    adapter = AdoAdapter(org="nold-ai", project="specfact-cli", api_token="token")

    monkeypatch.setattr(adapter, "_get_current_iteration", lambda: "Project\\Sprint 42")

    items = [_item("1", None), _item("2", "Project\\Sprint 42"), _item("3", "Project\\Sprint 41")]

    resolved, filtered = adapter._resolve_sprint_filter(None, items, apply_current_when_missing=True)

    assert resolved == "Project\\Sprint 42"
    assert [item.id for item in filtered] == ["2"]


def test_fetch_backlog_items_wiql_omits_iteration_when_current_default_disabled(monkeypatch) -> None:
    import specfact_cli.adapters.ado as ado_module
    from specfact_cli.backlog.filters import BacklogFilters

    adapter = AdoAdapter(org="nold-ai", project="specfact-cli", api_token="token")

    captured_query: dict[str, str] = {}

    class _Resp:
        status_code = 200
        ok = True
        text = ""

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"workItems": []}

    def _fake_post(url: str, headers: dict, json: dict, timeout: int):
        _ = url, headers, timeout
        captured_query["query"] = json.get("query", "")
        return _Resp()

    monkeypatch.setattr(adapter, "_get_current_iteration", lambda: r"Project\Sprint 42")
    monkeypatch.setattr(ado_module.requests, "post", _fake_post)

    filters = BacklogFilters(use_current_iteration_default=False)
    _ = adapter.fetch_backlog_items(filters)

    assert "System.IterationPath" not in captured_query.get("query", "")
