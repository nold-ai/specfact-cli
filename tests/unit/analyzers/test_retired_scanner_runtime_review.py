"""Regression cases for source-only Python feature and async analysis."""

from __future__ import annotations

import ast
from pathlib import Path
from textwrap import dedent

import pytest

from specfact_cli.analyzers.async_checks import async_findings
from specfact_cli.analyzers.python_patterns import feature_patterns


def _lines_for(source: str, rule: str) -> list[int]:
    return [
        finding.line
        for finding in async_findings(ast.parse(dedent(source).strip()), "example.py")
        if finding.rule_id == rule
    ]


@pytest.mark.parametrize(
    ("source", "rule", "lines"),
    [
        pytest.param(
            """
            async def run():
                task = asyncio.create_task(worker())
                await task
                task = asyncio.create_task(worker())
                task = None
                other = asyncio.create_task(worker())
                await other
            """,
            "task-result-not-checked",
            [4],
            id="task-observation-stops-at-reassignment",
        ),
        pytest.param(
            """
            async def run(lock=threading.Lock()):
                return threading.Lock()
            """,
            "sync-lock-in-async",
            [2],
            id="body-excludes-definition-time-expressions",
        ),
        pytest.param(
            """
            async def save():
                pass

            class AsyncStore:
                async def save(self):
                    pass

                async def run(self):
                    self.save()

            class SyncStore:
                def save(self):
                    pass

                async def run(self):
                    self.save()

            async def wrapper():
                async def local():
                    pass

                local()

                def save():
                    pass

                save()
            """,
            "missing-await-on-coroutine",
            [9, 22],
            id="missing-await-resolves-nested-coroutines-and-current-class",
        ),
    ],
)
def test_async_analysis_respects_scope(source: str, rule: str, lines: list[int]) -> None:
    assert _lines_for(source, rule) == lines


def test_only_authentication_dependencies_add_auth_evidence(tmp_path: Path) -> None:
    source = """
        from fastapi import Depends, Security

        @app.get("/health", dependencies=[Depends(record_metrics)])
        def health():
            pass

        @app.get("/protected", dependencies=[Depends(require_auth)])
        def protected():
            pass

        @app.get("/scoped", dependencies=[Security(check_scopes)])
        def scoped():
            pass
    """
    findings = feature_patterns(ast.parse(dedent(source).strip()), tmp_path / "example.py")
    auth = [item["start"]["line"] for item in findings if item["check_id"] == "fastapi-dependency-auth-detection"]
    assert auth == [7, 11]
