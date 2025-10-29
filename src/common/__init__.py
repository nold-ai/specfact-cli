"""
Common module for shared functionality across the specfact-cli application.

This module contains shared components and utilities that are used by multiple agents
in the specfact-cli application.
"""

from .logger_setup import LoggerSetup

# Define what gets imported with "from common import *"
__all__ = [
    "LoggerSetup",
]
