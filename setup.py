#!/usr/bin/env python3
"""Setup script for specfact-cli package."""

from setuptools import find_packages, setup


if __name__ == "__main__":
    _setup = setup(
        name="specfact-cli",
        version="0.31.0",
        description=(
            "The swiss knife CLI for agile DevOps teams. Keep backlog, specs, tests, and code in sync with "
            "validation and contract enforcement for new projects and long-lived codebases."
        ),
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        install_requires=[
            "pydantic>=2.11.5",
            "python-dotenv>=1.1.0",
            "PyYAML>=6.0.2",
            "requests>=2.32.3",
            "azure-identity>=1.17.1",
            "typer>=0.15.0",
            "rich>=14.0.0",
            "jinja2>=3.1.0",
            "networkx>=3.2",
            "gitpython>=3.1.0",
            "icontract>=2.7.1",
            "beartype>=0.22.2",
            "crosshair-tool>=0.0.97",
            "hypothesis>=6.140.3",
        ],
    )
