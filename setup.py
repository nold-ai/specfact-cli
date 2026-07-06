#!/usr/bin/env python3
"""Setup script for specfact-cli package (kept in sync with pyproject.toml [project].dependencies)."""

from setuptools import find_packages, setup


if __name__ == "__main__":
    _setup = setup(
        name="specfact-cli",
        version="0.48.2",
        description=(
            "AI-bloat defense CLI for Python teams. Run deterministic code review, cleanup forecasts, "
            "and spec/contract evidence for AI-assisted and brownfield delivery."
        ),
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        install_requires=[
            "pydantic>=2.12.3",
            "typing-extensions>=4.15.0",
            "PyYAML>=6.0.3",
            "requests>=2.32.3",
            "azure-identity>=1.17.1",
            "cryptography>=43.0.0",
            "packaging>=24.0",
            "click>=8.1.8,<8.2",
            "typer>=0.20.0,<0.24",
            "rich>=13.5.2,<16.0.0",
            "questionary>=2.0.1",
            "jinja2>=3.1.6",
            "networkx>=3.4.2",
            "graphviz>=0.20.1",
            "gitpython>=3.1.45",
            "ruamel.yaml>=0.18.16",
            "jsonschema>=4.23.0",
            "commentjson>=0.9.0",
            "icontract>=2.7.1",
            "beartype>=0.22.4",
            "watchdog>=6.0.0",
        ],
    )
