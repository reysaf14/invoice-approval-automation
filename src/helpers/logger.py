"""
Standard Logger Helper for Invoice Approval Automation.

Usage:
    from src.helpers.logger import get_logger
    logger = get_logger("ingestion")
    logger.info("Processing invoice %s", invoice_id)
"""

import logging
import sys
from datetime import datetime


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create a logger with standard format.

    Args:
        name: Logger name (e.g. 'ingestion', 'approval', 'reminder').
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


def log_invoice_event(
    logger: logging.Logger,
    event: str,
    invoice_id: str,
    status: str = "",
    extra: str = "",
) -> None:
    """Log an invoice processing event.

    Args:
        logger: Logger instance.
        event: Event type (e.g. 'INGESTED', 'APPROVED', 'REJECTED', 'DUPLICATE').
        invoice_id: Invoice UUID.
        status: Current status (optional).
        extra: Additional context (optional).
    """
    parts = [f"event={event}", f"invoice_id={invoice_id}"]
    if status:
        parts.append(f"status={status}")
    if extra:
        parts.append(extra)
    logger.info(" | ".join(parts))


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: str = "",
) -> None:
    """Log an error with context.

    Args:
        logger: Logger instance.
        error: Exception that occurred.
        context: Additional context (optional).
    """
    msg = f"ERROR: {type(error).__name__}: {str(error)}"
    if context:
        msg = f"{context} | {msg}"
    logger.error(msg)
