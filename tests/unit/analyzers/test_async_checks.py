"""Contract fixtures for the built-in async analysis."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest


def test_builtin_async_rules() -> None:
    """Run every fixture under the one Requirements proof selector."""
    cases = [
        ("asyncio.create_task(worker())", "asyncio-create-task-not-awaited"),
        ("time.sleep(1)", "blocking-sleep-in-async"),
        ("worker()", "missing-await-on-coroutine"),
        ("try:\n    await worker()\nexcept:\n    pass", "bare-except-in-async"),
        ("await asyncio.wait_for(worker(), None)", "missing-timeout-on-wait"),
        ("open(filename)", "blocking-file-io-in-async"),
        ("await asyncio.gather(worker(), worker())", "asyncio-gather-without-error-handling"),
        ("asyncio.run(worker())", "event-loop-in-async-context"),
        ("async with queue:\n    pass", "missing-async-context-manager"),
        ("threading.Lock()", "sync-lock-in-async"),
        ("await first()\nawait second()", "sequential-await-could-be-parallel"),
        ("await worker()", "missing-cancellation-handling"),
        ("task = asyncio.create_task(worker())", "task-result-not-checked"),
    ]
    for body, rule in cases:
        _check_builtin_async_rules(body, rule)


def _check_builtin_async_rules(body: str, rule: str) -> None:
    from specfact_cli.analyzers.async_checks import async_findings

    source = "async def worker():\n    pass\n\nasync def run():\n"
    source += "".join(f"    {line}\n" for line in body.splitlines())
    findings = async_findings(ast.parse(source), "example.py")
    assert any(item.rule_id == rule and item.file == "example.py" and item.line >= 4 for item in findings)


def test_async_controls_do_not_report_blocking_or_task_lifetime_errors() -> None:
    from specfact_cli.analyzers.async_checks import async_findings

    source = dedent("""
        import asyncio as aio
        import time

        async def run():
            try:
                task = aio.create_task(worker())
                await aio.wait_for(task, 1)
                following = worker()
                await aio.gather(following, return_exceptions=True)
            except aio.CancelledError:
                raise

            def synchronous_helper():
                time.sleep(1)
    """)
    assert async_findings(ast.parse(source), "example.py") == []


def test_async_cli_records_unavailable_source_and_leaves_requested_fix_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text("async def run():\n    time.sleep(1)\n", encoding="utf-8")
    source_root = Path(__file__).resolve().parents[3] / "src"
    command = [sys.executable, "-m", "specfact_cli.analyzers.async_checks", "--root", str(tmp_path)]
    incomplete = subprocess.run(
        [*command, "example.py", "missing.py"], cwd=source_root, capture_output=True, text=True, check=False, timeout=10
    )
    assert incomplete.returncode == 2
    assert json.loads(incomplete.stdout)["diagnostics"][0]["file"] == "missing.py"

    fix = subprocess.run(
        [*command, "--fix", "example.py"], cwd=source_root, capture_output=True, text=True, check=False, timeout=10
    )
    assert fix.returncode == 2
    assert "manual fixes" in json.loads(fix.stdout)["diagnostics"][0]["message"]
    assert source.read_text(encoding="utf-8") == "async def run():\n    time.sleep(1)\n"


def test_local_assignment_shadows_an_outer_coroutine() -> None:
    from specfact_cli.analyzers.async_checks import async_findings

    source = dedent("""
        async def worker():
            pass

        async def run():
            worker = lambda: None
            worker()
    """)

    assert not any(item.rule_id == "missing-await-on-coroutine" for item in async_findings(ast.parse(source), "app.py"))


def test_async_definition_replaces_an_earlier_assignment() -> None:
    from specfact_cli.analyzers.async_checks import async_findings

    source = dedent("""\
        worker = None

        async def worker():
            pass

        async def run():
            worker()
    """)

    assert any(item.rule_id == "missing-await-on-coroutine" for item in async_findings(ast.parse(source), "app.py"))


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("worker()\n    worker = lambda: None\n    worker()", [4]),
        ("if enabled:\n        worker = lambda: None\n    worker()", [6]),
        ("worker: object\n    worker()", [5]),
        (
            "if enabled:\n        for worker in [lambda: None]:\n            worker()\n    worker()",
            [7],
        ),
        (
            "replacement = worker\n    for worker in (lambda: None,):\n        worker()\n"
            "        worker = replacement\n        worker()\n        worker = lambda: None\n        worker()",
            [8],
        ),
        (
            "for worker in [lambda: None]:\n        worker = worker\n        worker()\n"
            "        async def worker():\n            pass\n        worker()",
            [9],
        ),
        (
            "for worker in [lambda: None]:\n        for turn in (1, 2):\n            worker()\n"
            "            async def worker():\n                pass",
            [6],
        ),
        (
            "for worker in [lambda: None]:\n        for turn in (1, 2):\n            alias = worker\n"
            "            alias()\n            async def worker():\n                pass",
            [7],
        ),
        (
            "for worker in [lambda: None]:\n        for worker in (lambda: None,):\n            worker()\n"
            "            async def worker():\n                pass",
            [],
        ),
        ("worker, ignored = worker, None\n    worker()", [5]),
        ("left, [worker] = None, [worker]\n    worker()", [5]),
        (
            "replacement = lambda: None\n    worker, replacement = replacement, worker\n"
            "    worker()\n    replacement()",
            [7],
        ),
        (
            "replacement = worker\n    worker = lambda: None\n"
            "    for turn in (1, 2):\n        worker()\n        worker = replacement",
            [7],
        ),
        (
            "replacement = worker\n    replacement = lambda: None\n    worker = lambda: None\n"
            "    for turn in (1, 2):\n        worker()\n        worker = replacement",
            [],
        ),
        (
            "replacement = worker\n    worker = lambda: None\n"
            "    for turn in (1, 2):\n        worker()\n        worker = replacement\n"
            "        worker = lambda: None",
            [],
        ),
        (
            "replacement = worker\n    worker = lambda: None\n"
            "    for turn in (1, 2):\n        worker()\n        worker = replacement\n"
            "        if enabled:\n            continue\n        worker = lambda: None",
            [7],
        ),
        (
            "callback = lambda: None\n    for turn in (1, 2):\n"
            "        callback()\n        callback = worker\n        break",
            [],
        ),
        (
            "callback = lambda: None\n    for turn in (1, 2):\n"
            "        callback()\n        callback = worker\n        if enabled:\n            break",
            [6],
        ),
        (
            "callback = lambda: None\n    for turn in (1, 2):\n"
            "        callback()\n        callback = worker\n        if enabled:\n            continue\n"
            "        break",
            [6],
        ),
        ("callback = lambda: None\n    for turn in (1,):\n        callback()\n        callback = worker", []),
        (
            "callback = lambda: None\n    for turn in (1, 2):\n"
            "        callback()\n        callback = worker\n        if enabled:\n            break\n"
            "        else:\n            return",
            [],
        ),
        ("for worker in (worker,):\n        worker()", [5]),
        (
            "replacement = worker\n    worker = replacement if enabled else worker\n    worker()",
            [6],
        ),
        ("worker = worker if enabled else (lambda: None)\n    worker()", [5]),
        ("worker = worker if False else (lambda: None)\n    worker()", []),
        ("worker = worker\n    worker()", [5]),
        ("other = worker\n    other()\n    other = lambda: None\n    other()", [5]),
    ],
    ids=[
        "later-assignment",
        "conditional-assignment",
        "local-annotation",
        "synchronous-loop-target",
        "loop-target-reassigned",
        "loop-target-resets-each-iteration",
        "nested-loop-carry",
        "nested-loop-carry-alias",
        "nested-loop-target-reset",
        "unpacking-alias",
        "nested-unpacking-alias",
        "unpacking-swap",
        "loop-carried-async-assignment",
        "loop-carried-sync-assignment",
        "loop-rebinding-cleared-before-backedge",
        "loop-rebinding-can-reach-continue",
        "unconditional-loop-break",
        "conditional-loop-break",
        "continue-before-loop-break",
        "single-iteration-loop",
        "loop-exits-in-either-branch",
        "coroutine-iterable",
        "conditional-async-values",
        "conditional-possible-async-value",
        "conditional-unreachable-async-value",
        "self-alias",
        "async-alias",
    ],
)
def test_local_coroutine_calls_respect_runtime_bindings(code: str, expected: list[int]) -> None:
    source = f"async def run(enabled=False):\n    async def worker():\n        pass\n    {code}\n"

    assert _missing_await_lines(source) == expected


def test_module_annotation_does_not_rebind_a_coroutine() -> None:
    from specfact_cli.analyzers.async_checks import async_findings

    source = "async def worker():\n    pass\nworker: object\nasync def run():\n    worker()\n"

    assert any(item.rule_id == "missing-await-on-coroutine" for item in async_findings(ast.parse(source), "app.py"))


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "import asyncio\n"
            "async def worker():\n    pass\n"
            "async def run():\n    worker()\n"
            "asyncio.run(run())\nworker = lambda: None\n",
            [5],
        ),
        (
            "async def run():\n"
            "    worker = lambda: None\n"
            "    for value in (1, 2):\n"
            "        worker()\n"
            "        async def worker():\n"
            "            pass\n",
            [4],
        ),
        (
            "async def worker():\n    pass\n"
            "def enclosing():\n    worker = lambda: None\n"
            "    async def run():\n        global worker\n"
            "        worker()\n        worker = lambda: None\n        worker()\n",
            [7],
        ),
        (
            "def enclosing():\n    async def worker():\n        pass\n"
            "    async def run():\n        nonlocal worker\n"
            "        worker()\n        worker = lambda: None\n        worker()\n",
            [6],
        ),
        (
            "import asyncio\nasync def worker():\n    pass\n"
            "def enclosing():\n    global worker\n    async def run():\n        worker()\n"
            "    asyncio.run(run())\n    worker = lambda: None\n",
            [7],
        ),
        (
            "async def worker():\n    pass\n"
            "def outer():\n    worker = lambda: None\n    def middle():\n        global worker\n"
            "        async def run():\n            worker()\n",
            [8],
        ),
        (
            "async def worker():\n    pass\n"
            "def enclosing():\n    global worker\n    worker = lambda: None\n"
            "    async def run():\n        worker()\n",
            [],
        ),
        (
            "def outer():\n    async def worker():\n        pass\n"
            "    def middle():\n        nonlocal worker\n        async def run():\n            worker()\n"
            "        worker = lambda: None\n",
            [7],
        ),
    ],
    ids=[
        "enclosing-binding",
        "previous-loop-iteration",
        "global",
        "nonlocal",
        "enclosing-global-later-write",
        "enclosing-global-skips-local",
        "enclosing-global-earlier-write",
        "enclosing-nonlocal-later-write",
    ],
)
def test_coroutine_calls_can_use_enclosing_or_later_bindings(source: str, expected: list[int]) -> None:
    assert _missing_await_lines(source) == expected


def _missing_await_lines(source: str) -> list[int]:
    from specfact_cli.analyzers.async_checks import async_findings

    findings = async_findings(ast.parse(source), "app.py")
    return [finding.line for finding in findings if finding.rule_id == "missing-await-on-coroutine"]
