"""
Common module for shared functionality across SpecFact CLI.

This module contains shared infrastructure components and utilities used throughout
the SpecFact CLI application:
- Logging infrastructure (logger_setup, logging_utils)
- Text and file utilities (text_utils, utils)
"""

from specfact_cli.common.logger_setup import LoggerSetup
from specfact_cli.common.logging_utils import get_bridge_logger
from specfact_cli.common.text_utils import TextUtils
from specfact_cli.common.utils import compute_sha256, dump_json, ensure_directory, load_json


# Define what gets imported with "from specfact_cli.common import *"
__all__ = [
    "LoggerSetup",
    "TextUtils",
    "compute_sha256",
    "dump_json",
    "ensure_directory",
    "get_bridge_logger",
    "load_json",
]
