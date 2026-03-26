"""Redirect / reachability coverage for modules URLs listed in the handoff map."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
MAP_PATH = REPO_ROOT / "docs" / "reference" / "core-to-modules-handoff-urls.md"

_MODULES_URL_RE = re.compile(r"https://modules\.specfact\.io[^\s|`]+")


def _urls_from_map(content: str) -> list[str]:
    urls: list[str] = []
    for line in content.splitlines():
        if "modules.specfact.io" not in line:
            continue
        for m in _MODULES_URL_RE.finditer(line):
            u = m.group(0).rstrip("`")
            if u not in urls:
                urls.append(u)
    return urls


def _url_ok(url: str, timeout: float = 25.0) -> bool:
    req = Request(url, method="HEAD", headers={"User-Agent": "specfact-handoff-url-test/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            return code is not None and 200 <= int(code) < 400
    except HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            return True
        if exc.code != 405:
            return False
    except (URLError, OSError):
        pass

    get_req = Request(url, headers={"User-Agent": "specfact-handoff-url-test/1.0"})
    try:
        with urlopen(get_req, timeout=timeout) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            return code is not None and 200 <= int(code) < 400
    except HTTPError as exc:
        return 200 <= exc.code < 400 or exc.code in {301, 302, 303, 307, 308}
    except (URLError, OSError):
        return False


@pytest.mark.skipif(
    os.environ.get("SPECFACT_RUN_HANDOFF_URL_CHECK") != "1",
    reason="set SPECFACT_RUN_HANDOFF_URL_CHECK=1 to run live HTTP checks against modules.specfact.io",
)
def test_handoff_map_modules_urls_http_reachable() -> None:
    assert MAP_PATH.is_file(), f"missing {MAP_PATH}"
    content = MAP_PATH.read_text(encoding="utf-8")
    urls = _urls_from_map(content)
    assert len(urls) >= 10, "expected migration map to list modules URLs"

    bad = [u for u in urls if not _url_ok(u)]
    assert not bad, "unreachable handoff map URL(s):\n" + "\n".join(bad)
