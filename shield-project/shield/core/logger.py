"""
Logging system for S.H.I.E.L.D.

Provides structured logging with both console and file output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # Format message
        log_format = (
            f"[%(asctime)s] {record.levelname} - "
            f"%(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = False,
    json_format: bool = False,
) -> logging.Logger:
    """
    Set up a logger with console and/or file handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, no file logging)
        console_output: Enable console output
        file_output: Enable file output
        json_format: Use JSON format for logs
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = ColoredFormatter()
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if file_output and log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for logging with extra data"""
    
    def __init__(self, logger: logging.Logger, **extra_data):
        """Initialize log context"""
        self.logger = logger
        self.extra_data = extra_data
    
    def __enter__(self):
        """Enter context"""
        for handler in self.logger.handlers:
            if hasattr(handler, "formatter") and isinstance(handler.formatter, JSONFormatter):
                # Store extra data on the handler
                handler.extra_data = self.extra_data
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        for handler in self.logger.handlers:
            if hasattr(handler, "extra_data"):
                delattr(handler, "extra_data")


# Global logger instance
_global_logger: Optional[logging.Logger] = None


def initialize_logging(config) -> None:
    """Initialize global logging from configuration"""
    global _global_logger
    
    log_file = config.core.data_dir / "shield.log" if hasattr(config, "core") else None
    
    _global_logger = setup_logger(
        "shield",
        log_level=config.core.log_level if hasattr(config, "core") else "INFO",
        log_file=log_file,
        console_output=True,
        file_output=True,
        json_format=False,
    )


def get_global_logger() -> logging.Logger:
    """Get the global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger(
            "shield",
            log_level="INFO",
            console_output=True,
            file_output=False,
        )
    return _global_logger
