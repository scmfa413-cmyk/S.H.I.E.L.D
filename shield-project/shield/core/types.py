"""
Base types and exceptions for S.H.I.E.L.D.

Defines core data structures and exception hierarchy.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from uuid import uuid4


# ============================================================================
# ENUMERATIONS
# ============================================================================

class MessageRole(str, Enum):
    """Role in a conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"
    TOOL = "tool"


class MessageType(str, Enum):
    """Type of message"""
    TEXT = "text"
    CODE = "code"
    FILE = "file"
    COMMAND = "command"
    REPORT = "report"
    ERROR = "error"


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    BUSY = "busy"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETE = "complete"


class TaskStatus(str, Enum):
    """Task/Objective status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MissionStatus(str, Enum):
    """Mission status"""
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolStatus(str, Enum):
    """Tool execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"
    SKIPPED = "skipped"


# ============================================================================
# EXCEPTIONS
# ============================================================================

class ShieldException(Exception):
    """Base exception for S.H.I.E.L.D."""
    pass


class ConfigurationError(ShieldException):
    """Configuration error"""
    pass


class ToolError(ShieldException):
    """Tool execution error"""
    pass


class ToolNotFoundError(ToolError):
    """Tool not found error"""
    pass


class ToolExecutionError(ToolError):
    """Tool execution failed"""
    pass


class ToolTimeoutError(ToolError):
    """Tool execution timed out"""
    pass


class AgentError(ShieldException):
    """Agent error"""
    pass


class AgentNotFoundError(AgentError):
    """Agent not found"""
    pass


class MissionError(ShieldException):
    """Mission error"""
    pass


class MissionExecutionError(MissionError):
    """Mission execution failed"""
    pass


class MemoryError(ShieldException):
    """Memory/storage error"""
    pass


class LLMError(ShieldException):
    """LLM integration error"""
    pass


class LLMConnectionError(LLMError):
    """Cannot connect to LLM"""
    pass


class LLMGenerationError(LLMError):
    """LLM generation failed"""
    pass


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Message:
    """
    A message in the conversation.
    
    Represents a unit of communication between user, assistant, agents, and tools.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    role: MessageRole = MessageRole.USER
    type: MessageType = MessageType.TEXT
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Additional context
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    parent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["role"] = self.role.value
        data["type"] = self.type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary"""
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if "role" in data and isinstance(data["role"], str):
            data["role"] = MessageRole(data["role"])
        if "type" in data and isinstance(data["type"], str):
            data["type"] = MessageType(data["type"])
        return cls(**data)


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: str  # str, int, float, bool, list, dict
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolResult:
    """Result of tool execution"""
    status: ToolStatus = ToolStatus.SUCCESS
    output: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    tool_name: str = ""
    input_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "tool_name": self.tool_name,
            "input_params": self.input_params,
            "metadata": self.metadata,
        }


@dataclass
class Objective:
    """A task objective within a mission"""
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    agent_type: str = ""  # e.g., "research", "analysis", "code", "execution"
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0  # Higher = more important
    
    # Dependencies
    prerequisites: List[str] = field(default_factory=list)  # IDs of prerequisite objectives
    
    # Execution
    assigned_agent_id: Optional[str] = None
    tools_required: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data


@dataclass
class Mission:
    """
    A mission - collection of objectives to accomplish.
    
    Represents a user request decomposed into actionable objectives.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    objectives: List[Objective] = field(default_factory=list)
    status: MissionStatus = MissionStatus.QUEUED
    
    # Constraints and configuration
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    
    # Results
    result: Optional[Dict[str, Any]] = None
    report: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["status"] = self.status.value
        data["objectives"] = [obj.to_dict() for obj in self.objectives]
        data["created_at"] = self.created_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data


@dataclass
class ExecutionContext:
    """Context for mission/objective execution"""
    mission_id: str
    objective_id: Optional[str] = None
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Memory references
    memory_tags: List[str] = field(default_factory=list)
    
    # Execution settings
    timeout_seconds: Optional[int] = None
    max_retries: int = 3


# ============================================================================
# RESPONSE MODELS
# ============================================================================

@dataclass
class CommandResponse:
    """Response from command execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class SearchResult:
    """Web search result"""
    title: str
    url: str
    snippet: str
    source: str  # e.g., "duckduckgo", "tavily"
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
