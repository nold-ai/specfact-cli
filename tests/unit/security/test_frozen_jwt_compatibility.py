"""Regression boundaries exercised by the focused frozen dependency repair."""

import jwt
import pytest
from jwt.types import Options


TEST_KEY = "local-regression-key-with-at-least-thirty-two-bytes"


def test_inspection_preserves_options_and_expiry_on_reuse() -> None:
    """Unverified inspection must not leak disabled claim checks into later reuse."""
    token = jwt.encode({"sub": "fixture", "exp": 1}, TEST_KEY, algorithm="HS256")
    options: Options = {"verify_signature": False}

    assert jwt.decode(token, options=options)["sub"] == "fixture"
    assert options == {"verify_signature": False}

    options["verify_signature"] = True
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, TEST_KEY, algorithms=["HS256"], options=options)


def test_signed_token_and_trailing_signature_padding_remain_supported() -> None:
    """Preserve normal signed-token decoding and supported signature padding."""
    token = jwt.encode({"sub": "fixture"}, TEST_KEY, algorithm="HS256")
    options: Options = {}

    assert jwt.decode(token, TEST_KEY, algorithms=["HS256"], options=options) == {"sub": "fixture"}
    padded_token = token + "=" * (-len(token.rsplit(".", 1)[1]) % 4)
    assert jwt.decode(padded_token, TEST_KEY, algorithms=["HS256"], options=options) == {"sub": "fixture"}
    assert options == {}
