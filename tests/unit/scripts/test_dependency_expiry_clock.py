"""Default policy clocks must enforce the Berlin calendar without shell TZ."""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, date, datetime, timedelta, tzinfo
from pathlib import Path
from types import ModuleType
from typing import Self
from zoneinfo import ZoneInfo

import pytest


ROOT = Path(__file__).resolve().parents[3]


def _load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("after_cutoff", [False, True], ids=["before-midnight", "at-midnight"])
@pytest.mark.parametrize("owner", ["security_audit_gate", "check_dependency_trust_exceptions"])
def test_default_expiry_uses_berlin_midnight(
    owner: str, after_cutoff: bool, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_script(owner)
    expiry = date.today()
    midnight = datetime.combine(expiry + timedelta(days=1), datetime.min.time(), ZoneInfo("Europe/Berlin"))
    instant = midnight.astimezone(UTC) - timedelta(seconds=not after_cutoff)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> Self:
            assert isinstance(tz, ZoneInfo) and tz.key == "Europe/Berlin"
            return cls.fromtimestamp(instant.timestamp(), tz)

    monkeypatch.setattr(module, "datetime", FixedDatetime, raising=False)
    if owner == "security_audit_gate":
        approved, error = module._approved_exception_ids(
            {
                "package": "clock-fixture",
                "version": "1.0",
                "vulnerability_ids": ["TEST-CLOCK"],
                "reviewed_on": expiry.isoformat(),
                "expires_on": expiry.isoformat(),
                "rationale": "Synthetic clock boundary",
                "mitigation": "Test fixture only",
            },
            0,
        )
        assert bool(error) is after_cutoff
        assert bool(approved) is not after_cutoff
    else:
        register = tmp_path / "exceptions.json"
        register.write_text(
            json.dumps(
                {
                    "exceptions": [
                        {
                            "package": "clock-fixture",
                            "version": "1.0",
                            "source_url": "https://files.pythonhosted.org/clock-fixture.whl",
                            "artifact_sha256": "a" * 64,
                            "classification": "source-provenance-reviewed",
                            "reviewed_on": expiry.isoformat(),
                            "expires_on": expiry.isoformat(),
                            "transitive_path": "test fixture",
                            "rationale": "Synthetic clock boundary",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        errors = module.validate_exception_register(register)
        assert bool(errors) is after_cutoff, errors
        assert module.validate_exception_register(register, today=expiry) == []
