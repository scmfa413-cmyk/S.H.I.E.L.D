"""
Core engine for S.H.I.E.L.D.

Provides base classes, configuration management, logging, and type definitions.
"""

from shield.core.config import Config, ShieldConfig
from shield.core.logger import setup_logger, get_logger, initialize_logging, get_global_logger
from shield.core.types import (
    Message,
    MessageRole,
    MessageType,
    Objective,
    Mission,
    MissionStatus,
    TaskStatus,
    AgentStatus,
    ToolStatus,
    ToolResult,
    ExecutionContext,
    SearchResult,
    ShieldException,
    ToolError,
    AgentError,
    MissionError,
)

__all__ = [
    # Configuration
    "Config",
    "ShieldConfig",
    # Logging
    "setup_logger",
    "get_logger",
    "initialize_logging",
    "get_global_logger",
    # Types and Data Classes
    "Message",
    "MessageRole",
    "MessageType",
    "Objective",
    "Mission",
    "MissionStatus",
    "TaskStatus",
    "AgentStatus",
    "ToolStatus",
    "ToolResult",
    "ExecutionContext",
    "SearchResult",
    # Exceptions
    "ShieldException",
    "ToolError",
    "AgentError",
    "MissionError",
]
