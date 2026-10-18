from __future__ import annotations

from typing import cast

import pytest

from tests.unit.scripts import test_downstream_semgrep as contract


wheel_recipe = contract.wheel_recipe


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("runtime",), None),
        (("runtime", "python_executable_sha256"), None),
        (("runtime", "system"), "Windows"),
        (("runtime", "machine"), "arm64"),
        (("runtime", "python_version"), "3.8.9"),
        (("runtime", "python_executable"), ""),
        (("runtime", "sysconfig_platform"), "win-amd64"),
        (("runtime", "python_executable_sha256"), "not-a-digest"),
        (("runtime", "libc"), ["glibc", "2.39"]),
        (("runtime", "libc"), [""]),
        (("commands",), None),
        (("commands",), []),
    ],
    ids=[
        "missing-runtime",
        "missing-interpreter-digest",
        "wrong-os",
        "wrong-arch",
        "wrong-python",
        "empty-interpreter",
        "wrong-sysconfig",
        "invalid-interpreter-digest",
        "wrong-libc",
        "malformed-libc",
        "missing-commands",
        "empty-commands",
    ],
)
def test_native_report_rejects_missing_or_contradictory_identity(
    wheel_recipe: contract.WheelRecipe, path: tuple[str, ...], value: object
) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    target = cast(dict[str, object], reports[0])
    for key in path[:-1]:
        target = cast(dict[str, object], target[key])
    if value is None:
        target.pop(path[-1])
    else:
        target[path[-1]] = value
    with pytest.raises(ValueError):
        module.aggregate_candidate_reports(recipe_path, reports)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("returncode", True),
        ("returncode", "0"),
        ("argv", []),
        ("argv", "python"),
        ("argv", [""]),
        ("argv", ["python", 1]),
        ("stdout_sha256", "invalid"),
        ("stderr_sha256", "g" * 64),
    ],
    ids=[
        "bool-code",
        "string-code",
        "empty-argv",
        "scalar-argv",
        "empty-executable",
        "nonstring-arg",
        "invalid-stdout-hash",
        "nonhex-stderr-hash",
    ],
)
def test_native_report_rejects_malformed_command_evidence(
    wheel_recipe: contract.WheelRecipe, field: str, value: object
) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    cast(dict[str, object], reports[0]["commands"][0])[field] = value
    with pytest.raises(ValueError):
        module.aggregate_candidate_reports(recipe_path, reports)


@pytest.mark.parametrize(
    ("platform", "libc"),
    [
        ("manylinux_2_34_x86_64", ["glibc", "2.33"]),
        ("manylinux_2_34_x86_64", ["musl", "Version 1.2"]),
        ("musllinux_1_2_x86_64", ["musl", "Version 1.1"]),
    ],
    ids=["old-glibc", "wrong-libc-family", "old-musl"],
)
def test_native_report_rejects_incompatible_linux_libc(
    wheel_recipe: contract.WheelRecipe, platform: str, libc: list[str]
) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    next(report for report in reports if report["platform"] == platform)["runtime"]["libc"] = libc
    with pytest.raises(ValueError):
        module.aggregate_candidate_reports(recipe_path, reports)


@pytest.mark.parametrize("control", ["faithful", "aliases", "universal2", "nonzero-control", "empty-argument"])
def test_native_report_accepts_supported_runtime_and_command_shapes(
    wheel_recipe: contract.WheelRecipe, control: str
) -> None:
    module = contract._module()
    recipe_path, recipe, _upstream = wheel_recipe
    reports = contract._reports(recipe_path, recipe)
    if control == "aliases":
        for report in reports:
            runtime = report["runtime"]
            runtime["machine"] = {"x86_64": "AMD64", "AMD64": "x86_64", "aarch64": "arm64", "arm64": "aarch64"}[
                runtime["machine"]
            ]
    if control == "universal2":
        for report in reports:
            if report["runtime"]["system"] == "Darwin":
                report["runtime"]["sysconfig_platform"] = "macosx-10.9-universal2"
    if control == "nonzero-control":
        reports[0]["commands"][1]["returncode"] = 1
    if control == "empty-argument":
        reports[0]["commands"][0]["argv"].append("")
    result = module.aggregate_candidate_reports(recipe_path, reports)
    assert result["status"] == "passed"
    assert result["production_admission"] == "not_requested"
