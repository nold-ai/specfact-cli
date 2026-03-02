"""Tests for official-tier module validation."""

from __future__ import annotations

import inspect

import pytest

from specfact_cli.registry import crypto_validator


def _manifest(*, tier: str, publisher: str, signature: str = "sig") -> dict[str, object]:
    return {
        "name": "specfact-example",
        "tier": tier,
        "publisher": {"name": publisher},
        "integrity": {"signature": signature},
    }


def test_official_tier_with_trusted_publisher_and_valid_signature_returns_official_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(crypto_validator, "verify_signature", lambda *_args, **_kwargs: True)
    result = crypto_validator.validate_module(_manifest(tier="official", publisher="nold-ai"), b"artifact", "pub-key")
    assert result.tier == "official"
    assert result.signature_valid is True


def test_official_tier_with_untrusted_publisher_raises_security_error() -> None:
    with pytest.raises(crypto_validator.SecurityError, match="publisher"):
        crypto_validator.validate_module(_manifest(tier="official", publisher="unknown-org"), b"artifact", "pub-key")


def test_official_tier_with_invalid_signature_raises_signature_verification_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_signature_error(*_args, **_kwargs) -> bool:
        raise ValueError("Signature verification failed")

    monkeypatch.setattr(crypto_validator, "verify_signature", _raise_signature_error)
    with pytest.raises(crypto_validator.SignatureVerificationError):
        crypto_validator.validate_module(_manifest(tier="official", publisher="nold-ai"), b"artifact", "pub-key")


def test_community_tier_not_promoted_to_official(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(crypto_validator, "verify_signature", lambda *_args, **_kwargs: True)
    result = crypto_validator.validate_module(_manifest(tier="community", publisher="nold-ai"), b"artifact", "pub-key")
    assert result.tier == "community"
    assert result.signature_valid is False


def test_official_publishers_constant_is_frozenset_with_nold_ai() -> None:
    assert isinstance(crypto_validator.OFFICIAL_PUBLISHERS, frozenset)
    assert "nold-ai" in crypto_validator.OFFICIAL_PUBLISHERS


def test_validate_module_is_guarded_by_contract_and_type_decorators() -> None:
    source = inspect.getsource(crypto_validator.validate_module)
    assert "@require" in source
    assert "@beartype" in source
