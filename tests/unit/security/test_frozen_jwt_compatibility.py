"""Regression boundaries exercised by the focused frozen dependency repair."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import jwt
from jwt.types import Options


TEST_KEY = "local-regression-key-with-at-least-thirty-two-bytes"


REPO_ROOT = Path(__file__).resolve().parents[3]
JWT_PROBE = """
import json, sys
sys.path.insert(0, sys.argv[1])
import jwt
key = "local-regression-key-with-at-least-thirty-two-bytes"
token = jwt.encode({"sub": "fixture", "exp": 1}, key, algorithm="HS256")
options = {"verify_signature": False}
subject = jwt.decode(token, options=options)["sub"]
after_inspection = dict(options)
options["verify_signature"] = True
expired = False
try:
    jwt.decode(token, key, algorithms=["HS256"], options=options)
except jwt.ExpiredSignatureError:
    expired = True
print(json.dumps({"version": jwt.__version__, "subject": subject,
                  "after_inspection": after_inspection, "expired": expired}))
"""


def test_inspection_preserves_options_and_expiry_on_reuse(tmp_path: Path) -> None:
    """Exercise the hash-pinned delivery package independently of verifier dependencies."""
    locked = (REPO_ROOT / "requirements/ci/locked.txt").read_text(encoding="utf-8")
    entries = re.findall(r"(?m)^pyjwt==([^\s]+) \\\n((?:[ \t]+--hash=sha256:[0-9a-f]{64}(?: \\)?\n)+)", locked)
    assert len(entries) == 1, "Expected one hash-pinned PyJWT delivery requirement"
    version, hashes = entries[0]
    requirement = tmp_path / "pyjwt.txt"
    requirement.write_text(f"pyjwt=={version} \\\n{hashes}", encoding="utf-8")
    uv = shutil.which("uv")
    assert uv is not None, "The frozen delivery probe requires uv"
    target = tmp_path / "delivery-package"
    subprocess.run(
        [
            uv,
            "--no-config",
            "pip",
            "install",
            "--target",
            str(target),
            "--only-binary=:all:",
            "--no-deps",
            "--require-hashes",
            "--index-url",
            "https://pypi.org/simple",
            "-r",
            str(requirement),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    observed = subprocess.run(
        [sys.executable, "-I", "-S", "-c", JWT_PROBE, str(target)],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    result = json.loads(observed.stdout)
    assert result["version"] == version
    assert result["subject"] == "fixture"
    assert result["after_inspection"] == {"verify_signature": False}
    assert result["expired"] is True


def test_signed_token_and_trailing_signature_padding_remain_supported() -> None:
    """Preserve normal signed-token decoding and supported signature padding."""
    token = jwt.encode({"sub": "fixture"}, TEST_KEY, algorithm="HS256")
    options: Options = {}

    assert jwt.decode(token, TEST_KEY, algorithms=["HS256"], options=options) == {"sub": "fixture"}
    padded_token = token + "=" * (-len(token.rsplit(".", 1)[1]) % 4)
    assert jwt.decode(padded_token, TEST_KEY, algorithms=["HS256"], options=options) == {"sub": "fixture"}
    assert options == {}
