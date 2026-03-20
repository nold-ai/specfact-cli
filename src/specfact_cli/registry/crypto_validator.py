"""
Checksum and optional signature verification for module artifacts (arch-06).
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


_ArtifactInput = bytes | Path
OFFICIAL_PUBLISHERS: frozenset[str] = frozenset({"nold-ai"})


class SecurityError(RuntimeError):
    """Raised when manifest provenance violates security policy."""


class SignatureVerificationError(SecurityError):
    """Raised when signature validation fails for trusted tiers."""


@dataclass(frozen=True)
class ValidationResult:
    """Result of manifest-level tier validation."""

    tier: str
    signature_valid: bool


def _algo_and_hex(expected_checksum: str) -> tuple[str, str]:
    """Parse 'algo:hex' format. Raises ValueError if invalid."""
    if ":" not in expected_checksum or not expected_checksum.strip():
        raise ValueError("Expected checksum must be in algo:hex format (e.g. sha256:<64 hex chars>)")
    algo, hex_part = expected_checksum.strip().split(":", 1)
    algo = algo.lower()
    if algo not in ("sha256", "sha384", "sha512"):
        raise ValueError("Supported checksum algorithms: sha256, sha384, sha512")
    if not hex_part or not all(c in "0123456789abcdefABCDEF" for c in hex_part):
        raise ValueError("Checksum hex part must contain only hex digits")
    expected_len = {"sha256": 64, "sha384": 96, "sha512": 128}
    if len(hex_part) != expected_len[algo]:
        raise ValueError(f"Checksum hex length for {algo} must be {expected_len[algo]}, got {len(hex_part)}")
    return algo, hex_part


@beartype
@require(lambda expected_checksum: expected_checksum.strip() != "", "Expected checksum must not be empty")
def verify_checksum(artifact: _ArtifactInput, expected_checksum: str) -> bool:
    """
    Verify artifact checksum against expected algo:hex value.

    Args:
        artifact: Raw bytes or path to file.
        expected_checksum: Expected value in format sha256:<64 hex>, sha384:<96>, or sha512:<128>.

    Returns:
        True if the artifact's checksum matches.

    Raises:
        ValueError: If format is invalid or checksum does not match.
    """
    algo, expected_hex = _algo_and_hex(expected_checksum)
    data = artifact.read_bytes() if isinstance(artifact, Path) else artifact
    hasher = hashlib.new(algo)
    hasher.update(data)
    actual_hex = hasher.hexdigest()
    if actual_hex.lower() != expected_hex.lower():
        raise ValueError(f"Checksum mismatch: computed {algo}:{actual_hex[:16]}... does not match expected")
    return True


def _verify_signature_impl(artifact: bytes, signature_b64: str, public_key_pem: str) -> bool:
    """
    Verify detached signature over artifact using public key.
    Uses cryptography if available; otherwise raises.
    """
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
    except ImportError as e:
        raise ValueError(
            "Signature verification requires the 'cryptography' package. Install with: pip install cryptography"
        ) from e
    if not public_key_pem or not public_key_pem.strip():
        raise ValueError("Public key PEM must not be empty")
    try:
        key = serialization.load_pem_public_key(public_key_pem.encode())
    except Exception as e:
        raise ValueError(f"Invalid public key PEM: {e}") from e
    try:
        sig_bytes = base64.b64decode(signature_b64, validate=True)
    except Exception as e:
        raise ValueError(f"Invalid base64 signature: {e}") from e
    if isinstance(key, rsa.RSAPublicKey):
        try:
            key.verify(sig_bytes, artifact, padding.PKCS1v15(), hashes.SHA256())
            return True
        except InvalidSignature:
            return False
    if isinstance(key, ed25519.Ed25519PublicKey):
        try:
            key.verify(sig_bytes, artifact)
            return True
        except InvalidSignature:
            return False
    raise ValueError("Unsupported key type for signature verification (RSA or Ed25519 only)")


@beartype
@require(lambda signature_b64: isinstance(signature_b64, str), "signature_b64 must be a string")
@require(lambda public_key_pem: isinstance(public_key_pem, str), "public_key_pem must be a string")
@ensure(lambda result: isinstance(result, bool), "Must return a bool")
def verify_signature(
    artifact: _ArtifactInput,
    signature_b64: str,
    public_key_pem: str,
) -> bool:
    """
    Verify detached signature over artifact.

    Args:
        artifact: Raw bytes or path to file.
        signature_b64: Base64-encoded signature.
        public_key_pem: PEM-encoded public key.

    Returns:
        True if signature is valid. False if no signature to verify (empty).
        Raises ValueError on missing key, invalid format, or verification failure.
    """
    if not signature_b64 or not signature_b64.strip():
        return False
    artifact_bytes = artifact.read_bytes() if isinstance(artifact, Path) else artifact
    if not public_key_pem or not public_key_pem.strip():
        raise ValueError("Public key PEM is required for signature verification")
    ok = _verify_signature_impl(artifact_bytes, signature_b64.strip(), public_key_pem.strip())
    if not ok:
        raise ValueError("Signature verification failed: signature does not match artifact or key")
    return True


@beartype
def _extract_publisher_name(manifest: dict[str, Any]) -> str:
    """Normalize publisher name from manifest payload."""
    publisher_raw = manifest.get("publisher")
    if isinstance(publisher_raw, dict):
        return str(publisher_raw.get("name", "")).strip().lower()
    return str(publisher_raw or "").strip().lower()


@beartype
@require(
    lambda manifest: str(manifest.get("tier", "unsigned")).strip().lower() in {"official", "community", "unsigned"},
    "tier must be one of: official, community, unsigned",
)
def validate_module(
    manifest: dict[str, Any], artifact: _ArtifactInput, public_key_pem: str | None = None
) -> ValidationResult:
    """Validate manifest trust tier and signature policy."""
    tier = str(manifest.get("tier", "unsigned")).strip().lower()
    publisher_name = _extract_publisher_name(manifest)

    if tier == "official":
        if publisher_name not in OFFICIAL_PUBLISHERS:
            raise SecurityError(f"Official-tier publisher is not allowlisted: {publisher_name or '<missing>'}")
        integrity = manifest.get("integrity")
        signature = str(integrity.get("signature", "")).strip() if isinstance(integrity, dict) else ""
        if not signature:
            raise SignatureVerificationError("Official-tier manifest requires integrity.signature")
        key_material = (public_key_pem or "").strip()
        if not key_material:
            raise SignatureVerificationError("Official-tier signature verification requires public key material")
        try:
            verify_signature(artifact, signature, key_material)
        except ValueError as exc:
            raise SignatureVerificationError(str(exc)) from exc
        return ValidationResult(tier="official", signature_valid=True)

    if tier == "community":
        return ValidationResult(tier="community", signature_valid=False)

    return ValidationResult(tier="unsigned", signature_valid=False)
