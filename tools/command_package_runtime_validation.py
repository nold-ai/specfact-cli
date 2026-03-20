from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from icontract import ensure, require


logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for candidate in (str(SRC_ROOT), str(REPO_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


DEFAULT_MODULES_REPO = REPO_ROOT.parent / "specfact-cli-modules"
DEFAULT_REGISTRY_INDEX = DEFAULT_MODULES_REPO / "registry" / "index.json"
FORBIDDEN_OUTPUT = (
    "Module compatibility check:",
    "Partially compliant modules:",
    "Legacy modules:",
    "takes precedence over user-scoped module",
)


def _subprocess_env(home_dir: Path, registry_index: Path) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_parts = [str(SRC_ROOT), str(REPO_ROOT)]
    existing = env.get("PYTHONPATH", "")
    if existing:
        pythonpath_parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    env["HOME"] = str(home_dir)
    env["SPECFACT_REPO_ROOT"] = str(REPO_ROOT)
    env["SPECFACT_MODULES_REPO"] = str(registry_index.parents[1])
    env["SPECFACT_REGISTRY_INDEX_URL"] = str(registry_index)
    env["SPECFACT_ALLOW_UNSIGNED"] = "1"
    env["SPECFACT_REGISTRY_DIR"] = str(home_dir / ".specfact-test-registry")
    return env


def _run_cli(env: dict[str, str], *argv: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "specfact_cli", *argv],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@require(lambda: DEFAULT_REGISTRY_INDEX.is_absolute(), "Default registry index must resolve to an absolute path")
@ensure(lambda result: isinstance(result, int), "main must return an int exit code")
def main() -> int:
    from specfact_cli.validation.command_audit import build_command_audit_cases, official_marketplace_module_ids

    configured_registry_index = os.environ.get("SPECFACT_REGISTRY_INDEX_URL", "").strip()
    registry_index = (
        Path(configured_registry_index).expanduser() if configured_registry_index else DEFAULT_REGISTRY_INDEX
    )
    registry_index = registry_index.resolve()
    if not registry_index.exists():
        logger.error("Registry index not found: %s", registry_index)
        return 2

    with tempfile.TemporaryDirectory(prefix="specfact-command-audit-") as tmp_dir:
        home_dir = Path(tmp_dir) / "home"
        home_dir.mkdir(parents=True, exist_ok=True)
        env = _subprocess_env(home_dir, registry_index)

        install_failures: list[dict[str, object]] = []
        for module_id in official_marketplace_module_ids():
            logger.info("[install] %s", module_id)
            result = _run_cli(env, "module", "install", module_id, "--source", "marketplace", cwd=REPO_ROOT)
            if result.returncode != 0:
                install_failures.append(
                    {
                        "module_id": module_id,
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
                )
        if install_failures:
            sys.stdout.write(json.dumps({"status": "install_failed", "failures": install_failures}, indent=2) + "\n")
            sys.stdout.flush()
            return 1

        failures: list[dict[str, object]] = []
        for case in build_command_audit_cases():
            logger.info("[audit] %s", case.command_path)
            result = _run_cli(env, *case.argv, cwd=home_dir)
            merged_output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
            if result.returncode != 0:
                failures.append(
                    {
                        "command_path": case.command_path,
                        "phase": case.phase,
                        "mode": case.mode,
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
                )
                continue
            leaked = [marker for marker in FORBIDDEN_OUTPUT if marker in merged_output]
            if leaked:
                failures.append(
                    {
                        "command_path": case.command_path,
                        "phase": case.phase,
                        "mode": case.mode,
                        "leaked_markers": leaked,
                        "output": merged_output,
                    }
                )

        status = "passed" if not failures else "failed"
        sys.stdout.write(
            json.dumps(
                {"status": status, "case_count": len(build_command_audit_cases()), "failures": failures}, indent=2
            )
            + "\n"
        )
        sys.stdout.flush()
        return 0 if not failures else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())
