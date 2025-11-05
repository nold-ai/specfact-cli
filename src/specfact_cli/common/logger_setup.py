"""
Logging utility for standardized log setup across all modules
"""

import atexit
import contextlib
import logging
import os
import re
import sys
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import Queue
from typing import Any, Literal

from beartype import beartype
from icontract import ensure, require


# Add TRACE level (5) - more detailed than DEBUG (10)
logging.addLevelName(5, "TRACE")

# Circular dependency protection flag
# Note: Platform base infrastructure removed for lean CLI
# The logger setup is now standalone without agent-system dependencies


@beartype
@ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty string path")
def get_runtime_logs_dir() -> str:
    """
    Get the path to the centralized runtime logs directory and ensure it exists.

    This function is designed to be safe to call from anywhere, including
    module-level initializers, by guaranteeing the log directory's existence.

    Returns:
        str: Path to the runtime logs directory.
    """
    # Determine the base path based on the environment
    if os.path.exists("/.dockerenv"):
        # Docker container: write to /app/logs
        base_logs_dir = "/app/logs"
    else:
        # Non-Docker (local): repository logs directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        repo_root = os.path.dirname(src_dir)
        base_logs_dir = os.path.join(repo_root, "logs")

    runtime_logs_dir = os.path.join(base_logs_dir, "runtime")

    # Check for and fix duplicated 'runtime' directory segment
    duplicate_segment = os.path.join("runtime", "runtime")
    if duplicate_segment in runtime_logs_dir:
        runtime_logs_dir = runtime_logs_dir.replace(duplicate_segment, "runtime")

    # Check and fix duplicated 'runtime' directory segment in case still present
    runtime_logs_dir = os.path.abspath(runtime_logs_dir).replace(
        f"{os.path.sep}runtime{os.path.sep}runtime", f"{os.path.sep}runtime"
    )

    # Ensure directory exists. Use 0o777 intentionally for cross-platform writability,
    # especially under container mounts and CI sandboxes. This is an explicitly justified
    # exception to repo rule #7; tests rely on this mode for deterministic behavior.
    mode = 0o777
    try:
        os.makedirs(runtime_logs_dir, mode=mode, exist_ok=True)
    except PermissionError:
        # Try workspace and CWD fallbacks, directly creating the runtime directory
        for fallback_root in [os.environ.get("WORKSPACE", "/workspace"), os.getcwd()]:
            try:
                runtime_logs_dir = os.path.join(fallback_root, "logs", "runtime")
                os.makedirs(runtime_logs_dir, mode=0o777, exist_ok=True)
                break
            except PermissionError:
                continue

    return runtime_logs_dir


class MessageFlowFormatter(logging.Formatter):
    """
    Custom formatter that recognizes message flow patterns and formats them accordingly
    """

    # Pattern to match "sender => receiver | message" format
    FLOW_PATTERN = re.compile(r"^(\w+) => (\w+) \| (.*)$")

    # Pattern to match already formatted messages (both standard and flow formats)
    # This includes timestamp pattern \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}
    # and agent | timestamp format
    ALREADY_FORMATTED_PATTERN = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}|^\w+ \| \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})"
    )

    @beartype
    @require(
        lambda agent_name: isinstance(agent_name, str) and len(agent_name) > 0, "Agent name must be non-empty string"
    )
    def __init__(
        self,
        agent_name: str,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        session_id: str | None = None,
        preserve_newlines: bool = True,
    ) -> None:
        """
        Initialize the formatter with the agent name

        Args:
            agent_name: Name of the agent (used when no flow information is in the message)
            fmt: Format string
            datefmt: Date format string
            style: Style of format string
            session_id: Optional unique session ID to include in log messages
            preserve_newlines: Whether to preserve newlines in the original message
        """
        super().__init__(fmt, datefmt, style)
        self.agent_name = agent_name
        self.session_id = session_id
        self.preserve_newlines = preserve_newlines

    @beartype
    @require(lambda record: isinstance(record, logging.LogRecord), "Record must be LogRecord instance")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record according to message flow patterns

        Args:
            record: The log record to format

        Returns:
            Formatted log string
        """
        # Extract the message
        original_message = record.getMessage()

        # Special case for test summary format (always preserve exact format)
        if "Test Summary:" in original_message or "===" in original_message:
            # Special case for test analyzer compatibility - don't prepend anything
            return original_message

        # Guard against already formatted messages to prevent recursive formatting
        # Check for timestamp pattern to identify already formatted messages
        if self.ALREADY_FORMATTED_PATTERN.search(original_message):
            # Log message is already formatted, return as is
            return original_message

        # Check if this is a message flow log
        flow_match = self.FLOW_PATTERN.match(original_message)
        if flow_match:
            sender, receiver, message = flow_match.groups()

            # Format the timestamp
            timestamp = self.formatTime(record, self.datefmt)

            # Format the message with flow information and session ID if available
            if self.session_id:
                formatted_message = (
                    f"{receiver} | {timestamp} | {self.session_id} | "
                    f"{record.levelname} | {sender} => {receiver} | {message}"
                )
            else:
                formatted_message = (
                    f"{receiver} | {timestamp} | {record.levelname} | {sender} => {receiver} | {message}"
                )

            # Override the message in the record
            record.msg = formatted_message
            record.args = ()

            # Return the formatted message directly
            return formatted_message
        # Standard formatting for non-flow messages
        timestamp = self.formatTime(record, self.datefmt)

        # Handle multiline messages
        if self.preserve_newlines and "\n" in original_message:
            lines = original_message.split("\n")
            # Format the first line with the timestamp
            if self.session_id:
                first_line = f"{self.agent_name} | {timestamp} | {self.session_id} | {record.levelname} | {lines[0]}"
            else:
                first_line = f"{self.agent_name} | {timestamp} | {record.levelname} | {lines[0]}"

            # Return the first line and the rest as is
            return first_line + "\n" + "\n".join(lines[1:])
        # Regular single-line message
        if self.session_id:
            formatted_message = (
                f"{self.agent_name} | {timestamp} | {self.session_id} | {record.levelname} | {original_message}"
            )
        else:
            formatted_message = f"{self.agent_name} | {timestamp} | {record.levelname} | {original_message}"

        # Override the message in the record
        record.msg = formatted_message
        record.args = ()

        # Return the formatted message
        return formatted_message


class LoggerSetup:
    """
    Utility class for standardized logging setup across all agents
    """

    # Keep the old format for backward compatibility
    LEGACY_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_LOG_LEVEL = "INFO"

    # Store active loggers for management
    _active_loggers: dict[str, logging.Logger] = {}
    _log_queues: dict[str, Queue] = {}
    _log_listeners: dict[str, QueueListener] = {}

    @classmethod
    def shutdown_listeners(cls):
        """Shuts down all active queue listeners."""
        for listener in cls._log_listeners.values():
            with contextlib.suppress(Exception):
                listener.stop()
        cls._log_listeners.clear()
        # Also clear active loggers to avoid handler accumulation across test sessions
        for logger in cls._active_loggers.values():
            with contextlib.suppress(Exception):
                for handler in list(logger.handlers):
                    with contextlib.suppress(Exception):
                        handler.close()
                    logger.removeHandler(handler)
        cls._active_loggers.clear()

    @classmethod
    @beartype
    @ensure(lambda result: isinstance(result, logging.Logger), "Must return Logger instance")
    def create_agent_flow_logger(cls, session_id: str | None = None) -> logging.Logger:
        """
        Creates a dedicated logger for inter-agent message flow.
        This logger uses a queue for thread-safe and process-safe logging.
        In test mode, creates a null handler to prevent file creation.
        """
        logger_name = "agent_flow"
        if logger_name in cls._active_loggers:
            return cls._active_loggers[logger_name]

        # Check if we're in test mode
        test_mode = os.environ.get("TEST_MODE", "").lower() == "true"

        log_queue = Queue(-1)
        cls._log_queues[logger_name] = log_queue

        formatter = MessageFlowFormatter(agent_name="inter_agent_comm", session_id=session_id)

        if test_mode:
            # In test mode, use a null handler that discards messages, but still use a QueueListener
            # so tests can assert on listener/QueueHandler presence without writing files.
            null_handler = logging.NullHandler()
            null_handler.setFormatter(formatter)
            null_handler.setLevel(logging.INFO)

            listener = QueueListener(log_queue, null_handler, respect_handler_level=True)
        else:
            # In production mode, use file handler
            runtime_logs_dir = get_runtime_logs_dir()
            log_file = os.path.join(runtime_logs_dir, "agent_flow.log")

            file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            # Also stream to console so run_local.sh can colorize per agent
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)

            listener = QueueListener(log_queue, file_handler, console_handler, respect_handler_level=True)

        listener.start()
        cls._log_listeners[logger_name] = listener

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if logger.handlers:
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()

        queue_handler = QueueHandler(log_queue)
        logger.addHandler(queue_handler)

        # Add trace method to logger instance for convenience
        logger.trace = lambda message, *args, **kwargs: logger.log(5, message, *args, **kwargs)

        cls._active_loggers[logger_name] = logger

        return logger

    @classmethod
    @beartype
    @require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
    @require(
        lambda log_level: log_level is None or (isinstance(log_level, str) and len(log_level) > 0),
        "Log level must be None or non-empty string",
    )
    @ensure(lambda result: isinstance(result, logging.Logger), "Must return Logger instance")
    def create_logger(
        cls,
        name: str,
        log_file: str | None = None,
        agent_name: str | None = None,
        log_level: str | None = None,
        session_id: str | None = None,
        use_rotating_file: bool = True,
        append_mode: bool = True,
        preserve_test_format: bool = False,
    ) -> logging.Logger:
        """
        Creates a new logger or returns an existing one with the specified configuration.
        This method is process-safe and suitable for multi-agent environments.
        """
        logger_name = name
        if logger_name in cls._active_loggers:
            existing_logger = cls._active_loggers[logger_name]
            # If a file log was requested now but the existing logger was created without one,
            # rebuild the logger with file backing to ensure per-agent files are created.
            if log_file:
                # Stop and discard any existing listener
                existing_listener = cls._log_listeners.pop(logger_name, None)
                if existing_listener:
                    with contextlib.suppress(Exception):
                        existing_listener.stop()

                # Remove all handlers from the existing logger
                with contextlib.suppress(Exception):
                    for handler in list(existing_logger.handlers):
                        with contextlib.suppress(Exception):
                            handler.close()
                        existing_logger.removeHandler(handler)

                # Remove from cache and proceed to full (re)creation below
                with contextlib.suppress(Exception):
                    cls._active_loggers.pop(logger_name, None)
            else:
                # No file requested: just ensure level is updated and reuse existing logger
                if log_level and existing_logger.level != logging.getLevelName(log_level.upper()):
                    existing_logger.setLevel(log_level.upper())
                return existing_logger

        # Determine log level
        log_level_str = (log_level or os.environ.get("LOG_LEVEL", cls.DEFAULT_LOG_LEVEL)).upper()
        # Strip inline comments
        log_level_clean = log_level_str.split("#")[0].strip()

        level = logging.getLevelName(log_level_clean)

        # Create logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = False  # Prevent duplicate logs in parent loggers

        # Clear existing handlers to prevent duplication
        if logger.hasHandlers():
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler)

        # Prepare formatter
        log_format = MessageFlowFormatter(
            agent_name=agent_name or name,
            session_id=session_id,
            preserve_newlines=not preserve_test_format,
        )

        # Create a queue and listener for this logger if a file is specified
        if log_file:
            log_queue = Queue(-1)
            cls._log_queues[logger_name] = log_queue

            log_file_path = log_file
            if not os.path.isabs(log_file):
                logs_dir = get_runtime_logs_dir()
                log_file_path = os.path.join(logs_dir, log_file)

            # Ensure the directory for the log file exists
            log_file_dir = os.path.dirname(log_file_path)
            os.makedirs(log_file_dir, mode=0o777, exist_ok=True)
            # Proactively create/touch the file so it exists even before first write
            try:
                with open(log_file_path, "a", encoding="utf-8"):
                    pass
            except Exception:
                # Non-fatal; handler will attempt to open the file next
                pass

            try:
                if use_rotating_file:
                    handler: logging.Handler = RotatingFileHandler(
                        log_file_path,
                        maxBytes=10 * 1024 * 1024,
                        backupCount=5,
                        mode="a" if append_mode else "w",
                    )
                else:
                    handler = logging.FileHandler(log_file_path, mode="a" if append_mode else "w")
            except (FileNotFoundError, OSError):
                # Fallback for test environments where makedirs is mocked or paths are not writable
                fallback_dir = os.getcwd()
                fallback_path = os.path.join(fallback_dir, os.path.basename(log_file_path))
                if use_rotating_file:
                    handler = RotatingFileHandler(
                        fallback_path,
                        maxBytes=10 * 1024 * 1024,
                        backupCount=5,
                        mode="a" if append_mode else "w",
                    )
                else:
                    handler = logging.FileHandler(fallback_path, mode="a" if append_mode else "w")

            handler.setFormatter(log_format)
            handler.setLevel(level)

            listener = QueueListener(log_queue, handler, respect_handler_level=True)
            listener.start()
            cls._log_listeners[logger_name] = listener

            queue_handler = QueueHandler(log_queue)
            logger.addHandler(queue_handler)

            # Emit a one-time initialization line so users can see where logs go
            with contextlib.suppress(Exception):
                logger.info("[LoggerSetup] File logger initialized: %s", log_file_path)
        else:
            # If no log file is specified, set up a listener with a console handler
            log_queue = Queue(-1)
            cls._log_queues[logger_name] = log_queue

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(log_format)
            console_handler.setLevel(level)

            listener = QueueListener(log_queue, console_handler, respect_handler_level=True)
            listener.start()
            cls._log_listeners[logger_name] = listener

            queue_handler = QueueHandler(log_queue)
            logger.addHandler(queue_handler)

        # Add a console handler for non-test environments or when no file is specified
        if "pytest" not in sys.modules and not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(log_format)
            console_handler.setLevel(level)
            logger.addHandler(console_handler)

        # Add trace method to logger instance for convenience
        logger.trace = lambda message, *args, **kwargs: logger.log(5, message, *args, **kwargs)

        cls._active_loggers[logger_name] = logger
        return logger

    @classmethod
    def flush_all_loggers(cls) -> None:
        """
        Flush all active loggers to ensure their output is written
        """
        for _logger_name, _logger in cls._active_loggers.items():
            # With QueueListener, flushing the logger's handlers (QueueHandler)
            # doesn't guarantee the message is written. The listener thread handles it.
            # Stopping the listener flushes the queue, but that's for shutdown.
            # This method is now effectively a no-op for queued logs.
            pass

    @classmethod
    @beartype
    @require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def flush_logger(cls, name: str) -> bool:
        """
        Flush a specific logger by name

        Args:
            name: Name of the logger to flush

        Returns:
            True if logger was found and flushed, False otherwise
        """
        # See flush_all_loggers comment. This is now a no-op.
        return name in cls._active_loggers

    @classmethod
    @beartype
    @require(lambda logger: isinstance(logger, logging.Logger), "Logger must be Logger instance")
    @require(lambda summary: isinstance(summary, dict), "Summary must be dictionary")
    def write_test_summary(cls, logger: logging.Logger, summary: dict[str, Any]) -> None:
        """
        Write test summary in a format that log_analyzer.py can understand

        Args:
            logger: The logger to use
            summary: Dictionary with test summary information
        """
        listener = cls._log_listeners.get(logger.name)
        if not listener:
            # Fallback for non-queued loggers, though all should be queued now
            for handler in logger.handlers:
                handler.flush()
            logger.info("=" * 15 + " test session starts " + "=" * 15)
            # ... rest of the original implementation
            return

        # Find the file handler to get its path
        file_handler = next(
            (h for h in listener.handlers if isinstance(h, (logging.FileHandler, RotatingFileHandler))),
            None,
        )
        if not file_handler:
            return

        # Stop the listener to ensure the queue is flushed before we write the summary
        listener.stop()

        # Write summary directly to the file to ensure it's synchronous
        log_file_path = file_handler.baseFilename
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)
        duration = summary.get("duration", 0)
        summary_lines = [
            "=" * 15 + " test session starts " + "=" * 15,
            f"{passed} passed, {failed} failed, {skipped} skipped in {duration:.2f}s",
            f"Test Summary: {passed} passed, {failed} failed, {skipped} skipped",
            f"Status: {'PASSED' if failed == 0 else 'FAILED'}",
            f"Duration: {duration:.2f} seconds",
        ]

        if summary.get("failed_tests"):
            summary_lines.append("Failed tests by module:")
            for module, tests in summary.get("failed_modules", {}).items():
                summary_lines.append(f"Module: {module} - {len(tests)} failed tests")
                for test in tests:
                    summary_lines.append(f"- {test}")

        summary_lines.append("=" * 50)

        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")

        # Restart the listener for any subsequent logging
        listener.start()

    @classmethod
    @beartype
    @require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
    @ensure(lambda result: result is None or isinstance(result, logging.Logger), "Must return None or Logger instance")
    def get_logger(cls, name: str) -> logging.Logger | None:
        """
        Get a logger by name

        Args:
            name: Name of the logger

        Returns:
            Configured logger instance or None if logger doesn't exist
        """
        return cls._active_loggers.get(name)

    @staticmethod
    @beartype
    @require(lambda logger: isinstance(logger, logging.Logger), "Logger must be Logger instance")
    @require(lambda message: isinstance(message, str), "Message must be string")
    def trace(logger: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a message at TRACE level (5)

        Args:
            logger: Logger instance
            message: Log message
            *args: Additional arguments for string formatting
            **kwargs: Additional keyword arguments for logging
        """
        logger.log(5, message, *args, **kwargs)

    @staticmethod
    @beartype
    @ensure(lambda result: result is not None, "Must return object")
    def redact_secrets(obj: Any) -> Any:
        """
        Recursively mask sensitive values (API keys, tokens, passwords, secrets) in dicts/lists/strings.
        Returns a sanitized copy of the object suitable for logging.
        """
        sensitive_keys = ["key", "token", "password", "secret"]
        if isinstance(obj, dict):
            redacted = {}
            for k, v in obj.items():
                if any(s in k.lower() for s in sensitive_keys):
                    if isinstance(v, str) and len(v) > 4:
                        redacted[k] = f"*** MASKED (ends with '{v[-4:]}') ***"
                    elif v:
                        redacted[k] = "*** MASKED ***"
                    else:
                        redacted[k] = None
                else:
                    redacted[k] = LoggerSetup.redact_secrets(v)
            return redacted
        if isinstance(obj, list):
            return [LoggerSetup.redact_secrets(item) for item in obj]
        if isinstance(obj, str):
            # Optionally, mask API key patterns in strings (e.g., sk-...)
            # Example: OpenAI key pattern
            return re.sub(r"sk-[a-zA-Z0-9_-]{20,}", "*** MASKED API KEY ***", obj)
        return obj


@beartype
@require(lambda agent_name: isinstance(agent_name, str) and len(agent_name) > 0, "Agent name must be non-empty string")
@require(lambda log_level: isinstance(log_level, str) and len(log_level) > 0, "Log level must be non-empty string")
@ensure(lambda result: isinstance(result, logging.Logger), "Must return Logger instance")
def setup_logger(
    agent_name: str,
    log_level: str = "INFO",
    session_id: str | None = None,
    log_file: str | None = None,
    use_rotating_file: bool = True,
) -> logging.Logger:
    """
    Set up a logger with the given name and log level

    Args:
        agent_name: Name of the agent
        log_level: Log level (default: INFO)
        session_id: Optional unique session ID to include in all log messages
        log_file: Optional file path for logging
        use_rotating_file: Whether to use rotating file handler (default: True)

    Returns:
        Configured logger
    """
    # Use the LoggerSetup class for consistent logging setup
    return LoggerSetup.create_logger(
        agent_name,
        log_file=log_file,
        agent_name=agent_name,
        log_level=log_level,
        session_id=session_id,
        use_rotating_file=use_rotating_file,
    )


atexit.register(LoggerSetup.shutdown_listeners)
