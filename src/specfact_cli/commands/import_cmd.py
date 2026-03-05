"""Backward-compatible app shim for project import command."""

from importlib import import_module

from specfact_cli.modules._bundle_import import bootstrap_local_bundle_sources


bootstrap_local_bundle_sources(__file__)

app = import_module("specfact_project.import_cmd.commands").app

__all__ = ["app"]
