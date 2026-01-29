"""
Unit tests for ADO PATCH failure debug logging and user-facing error messages.

Spec: openspec/changes/improve-ado-backlog-refine-error-logging/specs/api-error-diagnostics/spec.md
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from specfact_cli.adapters.ado import AdoAdapter


def _make_response(
    status_code: int = 400,
    body_json: dict | None = None,
    body_text: str | None = None,
) -> requests.Response:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    if body_json is not None:
        resp.text = json.dumps(body_json)
        resp.json.return_value = body_json
    elif body_text is not None:
        resp.text = body_text
        resp.json.side_effect = ValueError("not JSON")
    else:
        resp.text = ""
        resp.json.side_effect = ValueError("not JSON")
    return resp


def _make_http_error(response: requests.Response) -> requests.HTTPError:
    err = requests.HTTPError()
    err.response = response
    return err


class TestAdoPatchFailureDebugLogging:
    """Debug log contains response and patch paths on PATCH failure (spec scenario)."""

    @pytest.fixture
    def adapter(self) -> AdoAdapter:
        return AdoAdapter(org="myorg", project="myproj", api_token="dummy")

    def test_debug_log_operation_called_with_extra_when_debug_on(self, adapter: AdoAdapter) -> None:
        """When debug on and PATCH fails, debug_log_operation is called with response_body and patch_paths."""
        response = _make_response(
            400,
            body_json={"message": "TF51535: Cannot find field System.AcceptanceCriteria."},
        )
        with (
            patch("specfact_cli.adapters.ado.requests.patch") as mock_patch,
            patch("specfact_cli.adapters.ado.is_debug_mode", return_value=True),
            patch("specfact_cli.adapters.ado.debug_log_operation") as mock_debug_log,
            patch("specfact_cli.adapters.ado.console.print"),
        ):
            mock_patch.return_value = response
            response.raise_for_status = lambda: (_ for _ in ()).throw(_make_http_error(response))
            with pytest.raises(requests.RequestException):
                adapter.sync_status_to_ado(
                    {"status": "in_progress", "source_tracking": {"source_id": 123}},
                    "myorg",
                    "myproj",
                )
            mock_debug_log.assert_called()
            call_args = mock_debug_log.call_args
            assert call_args[0][0] == "ado_patch"
            assert call_args[0][2] == "failed"
            call_kw = call_args[1] or {}
            extra = call_kw.get("extra") or {}
            assert "response_body" in extra
            assert "patch_paths" in extra
            assert extra["patch_paths"] == ["/fields/System.State"]
            assert "Cannot find field" in str(extra["response_body"])

    def test_debug_log_operation_not_called_when_debug_off(self, adapter: AdoAdapter) -> None:
        """When debug off and PATCH fails, debug_log_operation is not called."""
        response = _make_response(400, body_json={"message": "Bad request"})
        with (
            patch("specfact_cli.adapters.ado.requests.patch") as mock_patch,
            patch("specfact_cli.adapters.ado.is_debug_mode", return_value=False),
            patch("specfact_cli.adapters.ado.debug_log_operation") as mock_debug_log,
            patch("specfact_cli.adapters.ado.console.print"),
        ):
            mock_patch.return_value = response
            response.raise_for_status = lambda: (_ for _ in ()).throw(_make_http_error(response))
            with pytest.raises(requests.RequestException):
                adapter.sync_status_to_ado(
                    {"status": "in_progress", "source_tracking": {"source_id": 123}},
                    "myorg",
                    "myproj",
                )
            mock_debug_log.assert_not_called()


class TestAdoPatchUserMessage:
    """Console shows ADO message and mapping hint on 400 (spec scenario)."""

    @pytest.fixture
    def adapter(self) -> AdoAdapter:
        return AdoAdapter(org="myorg", project="myproj", api_token="dummy")

    def test_console_print_contains_ado_message_and_hint(self, adapter: AdoAdapter) -> None:
        """User-facing message includes ADO error text and custom field mapping hint."""
        response = _make_response(
            400,
            body_json={"message": "TF51535: Cannot find field System.AcceptanceCriteria."},
        )
        with (
            patch("specfact_cli.adapters.ado.requests.patch") as mock_patch,
            patch("specfact_cli.adapters.ado.is_debug_mode", return_value=False),
            patch("specfact_cli.adapters.ado.debug_log_operation"),
            patch("specfact_cli.adapters.ado.console.print") as mock_console_print,
        ):
            mock_patch.return_value = response
            response.raise_for_status = lambda: (_ for _ in ()).throw(_make_http_error(response))
            with pytest.raises(requests.RequestException):
                adapter.sync_status_to_ado(
                    {"status": "in_progress", "source_tracking": {"source_id": 123}},
                    "myorg",
                    "myproj",
                )
            mock_console_print.assert_called()
            printed = " ".join(str(c) for c in mock_console_print.call_args[0])
            assert "Field '" in printed and "System.AcceptanceCriteria" in printed
            assert "custom field mapping" in printed or "ado_custom" in printed.lower()

    def test_reraised_exception_carries_ado_context(self, adapter: AdoAdapter) -> None:
        """Re-raised exception has ado_user_message with ADO error and mapping hint (spec)."""
        response = _make_response(
            400,
            body_json={"message": "TF51535: Cannot find field System.AcceptanceCriteria."},
        )
        with (
            patch("specfact_cli.adapters.ado.requests.patch") as mock_patch,
            patch("specfact_cli.adapters.ado.is_debug_mode", return_value=False),
            patch("specfact_cli.adapters.ado.debug_log_operation"),
            patch("specfact_cli.adapters.ado.console.print"),
        ):
            mock_patch.return_value = response
            response.raise_for_status = lambda: (_ for _ in ()).throw(_make_http_error(response))
            with pytest.raises(requests.RequestException) as exc_info:
                adapter.sync_status_to_ado(
                    {"status": "in_progress", "source_tracking": {"source_id": 123}},
                    "myorg",
                    "myproj",
                )
            exc = exc_info.value
            ado_msg = getattr(exc, "ado_user_message", "")
            assert "System.AcceptanceCriteria" in ado_msg or "Cannot find field" in ado_msg
            assert "custom field mapping" in ado_msg or "ado_custom" in ado_msg.lower()


class TestAdoPatchSensitiveDataRedaction:
    """No sensitive data in debug log (spec scenario)."""

    @pytest.fixture
    def adapter(self) -> AdoAdapter:
        return AdoAdapter(org="myorg", project="myproj", api_token="dummy")

    def test_debug_log_redacts_api_key_in_response_body(self, adapter: AdoAdapter) -> None:
        """Response body containing sk-... pattern is redacted in debug log."""
        secret = "sk-" + "x" * 24
        response = _make_response(
            400,
            body_json={"message": f"Invalid token: {secret}"},
        )
        with (
            patch("specfact_cli.adapters.ado.requests.patch") as mock_patch,
            patch("specfact_cli.adapters.ado.is_debug_mode", return_value=True),
            patch("specfact_cli.adapters.ado.debug_log_operation") as mock_debug_log,
            patch("specfact_cli.adapters.ado.console.print"),
        ):
            mock_patch.return_value = response
            response.raise_for_status = lambda: (_ for _ in ()).throw(_make_http_error(response))
            with pytest.raises(requests.RequestException):
                adapter.sync_status_to_ado(
                    {"status": "in_progress", "source_tracking": {"source_id": 123}},
                    "myorg",
                    "myproj",
                )
            mock_debug_log.assert_called()
            call_kw = mock_debug_log.call_args[1] or {}
            extra = call_kw.get("extra") or {}
            logged = str(extra.get("response_body", ""))
            assert "*** MASKED" in logged
            assert secret not in logged


class TestAdoPatchNonJsonBody:
    """Non-JSON or oversized response body (spec scenario)."""

    @pytest.fixture
    def adapter(self) -> AdoAdapter:
        return AdoAdapter(org="myorg", project="myproj", api_token="dummy")

    def test_non_json_response_no_crash(self, adapter: AdoAdapter) -> None:
        """Non-JSON response body does not crash; safe string used."""
        response = _make_response(body_text="<html>Error 400</html>")
        response.status_code = 400
        with (
            patch("specfact_cli.adapters.ado.requests.patch") as mock_patch,
            patch("specfact_cli.adapters.ado.is_debug_mode", return_value=True),
            patch("specfact_cli.adapters.ado.debug_log_operation") as mock_debug_log,
            patch("specfact_cli.adapters.ado.console.print"),
        ):
            mock_patch.return_value = response
            response.raise_for_status = lambda: (_ for _ in ()).throw(_make_http_error(response))
            with pytest.raises(requests.RequestException):
                adapter.sync_status_to_ado(
                    {"status": "in_progress", "source_tracking": {"source_id": 123}},
                    "myorg",
                    "myproj",
                )
            mock_debug_log.assert_called()
            call_kw = mock_debug_log.call_args[1]
            extra = call_kw.get("extra") or {}
            assert "response_body" in extra
            assert "Error 400" in str(extra["response_body"]) or "html" in str(extra["response_body"]).lower()
