#!/usr/bin/env python3
"""HTTP-check ``https://modules.specfact.io/...`` URLs found in docs Markdown."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from beartype import beartype


_REPO_ROOT = Path(__file__).resolve().parents[1]

_PREFIX = "https://modules.specfact.io"


@beartype
def _urls_from_line(line: str) -> list[str]:
    """Extract modules URLs; stop before Markdown ``)``, whitespace, ``]``, or ``**`` (bold)."""
    out: list[str] = []
    start = 0
    while True:
        idx = line.find(_PREFIX, start)
        if idx == -1:
            break
        end = idx + len(_PREFIX)
        while end < len(line):
            ch = line[end]
            if ch in ")|`\"'<>|]" or ch.isspace():
                break
            if line[end : end + 2] == "**":
                break
            end += 1
        raw = line[idx:end]
        if raw and raw[-1] in {")", "*"}:
            raw = raw[:-1]
        if raw and raw not in out:
            out.append(raw)
        start = end
    return out


@beartype
def _collect_urls_from_markdown(text: str) -> list[str]:
    cleaned: list[str] = []
    for line in text.splitlines():
        if _PREFIX not in line:
            continue
        for u in _urls_from_line(line):
            if u not in cleaned:
                cleaned.append(u)
    return cleaned


@beartype
def _check_url(url: str, timeout_s: float) -> tuple[bool, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "modules.specfact.io":
        return True, "skipped non-modules URL"
    req = Request(url, method="HEAD", headers={"User-Agent": "specfact-docs-link-check/1.0"})
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            if code is not None and 200 <= int(code) < 400:
                return True, str(code)
    except HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            return True, str(exc.code)
        if exc.code != 405:
            return False, f"HTTP {exc.code}"
    except (URLError, OSError) as exc:
        return False, str(exc)

    get_req = Request(url, headers={"User-Agent": "specfact-docs-link-check/1.0"})
    try:
        with urlopen(get_req, timeout=timeout_s) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            if code is not None and 200 <= int(code) < 400:
                return True, str(code)
            return False, f"GET {code}"
    except HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            return True, str(exc.code)
        return False, f"HTTP {exc.code}"
    except (URLError, OSError) as exc:
        return False, str(exc)


@beartype
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print failures but exit 0 (for optional CI steps).",
    )
    parser.add_argument("--timeout", type=float, default=25.0, help="HTTP timeout in seconds.")
    args = parser.parse_args()

    docs_root = _REPO_ROOT / "docs"
    if not docs_root.is_dir():
        print("check-cross-site-links: no docs/ directory", file=sys.stderr)
        return 1

    seen: set[str] = set()
    failures: list[str] = []

    for md_path in sorted(docs_root.rglob("*.md")):
        if "_site" in md_path.parts or "vendor" in md_path.parts:
            continue
        rel = md_path.relative_to(_REPO_ROOT)
        try:
            text = md_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{rel}: cannot decode file as UTF-8 ({exc})")
            continue
        for url in _collect_urls_from_markdown(text):
            if url in seen:
                continue
            seen.add(url)
            ok, detail = _check_url(url, args.timeout)
            if not ok:
                failures.append(f"{rel}: {url} — {detail}")

    if failures:
        print("Cross-site link validation failed:", file=sys.stderr)
        for line in failures:
            print(line, file=sys.stderr)
        return 0 if args.warn_only else 1
    print(f"check-cross-site-links: OK ({len(seen)} unique modules.specfact.io URL(s) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
