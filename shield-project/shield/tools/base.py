"""
Tool framework for S.H.I.E.L.D.

Defines base Tool class and tool registry for extensible tool system.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
import inspect
import json
from shield.core.types import ToolParameter, ToolResult, ToolStatus
from shield.core.logger import get_logger

if TYPE_CHECKING:
    from shield.core.base import ExecutionContext

logger = get_logger(__name__)


class Tool(ABC):
    """
    Base class for all tools in S.H.I.E.L.D.
    
    Tools are atomic operations that agents can call to execute actions:
    - File I/O operations
    - Web searches
    - Command execution
    - Code analysis
    - Database queries
    - etc.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: str = "general",
        enabled: bool = True,
    ):
        """
        Initialize tool.
        
        Args:
            name: Unique tool identifier
            description: Human-readable description
            category: Tool category (e.g., "file", "web", "code", "system")
            enabled: Whether tool is enabled
        """
        self.name = name
        self.description = description
        self.category = category
        self.enabled = enabled
        self._parameters: Dict[str, ToolParameter] = {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.
        
        Args:
            **kwargs: Tool-specific parameters
        
        Returns:
            ToolResult with execution status and output
        
        Raises:
            ToolError: If execution fails
        """
        pass
    
    def register_parameter(self, param: ToolParameter) -> None:
        """Register a parameter for this tool"""
        self._parameters[param.name] = param
    
    def register_parameters(self, params: List[ToolParameter]) -> None:
        """Register multiple parameters"""
        for param in params:
            self.register_parameter(param)
    
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters"""
        return self._parameters.copy()
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters.
        
        Args:
            **kwargs: Parameters to validate
        
        Returns:
            True if valid, False otherwise
        """
        for param_name, param in self._parameters.items():
            if param.required and param_name not in kwargs:
                logger.warning(f"Missing required parameter: {param_name}")
                return False
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM integration.
        
        Returns JSON schema compatible with OpenAI function calling.
        """
        parameters = {}
        required = []
        
        for param_name, param in self._parameters.items():
            parameters[param_name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                parameters[param_name]["default"] = param.default
            
            if param.required:
                required.append(param_name)
        
        schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required,
                }
            }
        }
        
        return schema
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "enabled": self.enabled,
            "parameters": {k: asdict(v) for k, v in self._parameters.items()},
        }


class ToolRegistry:
    """
    Registry for managing all available tools.
    
    Provides tool discovery, loading, and execution.
    """
    
    def __init__(self):
        """Initialize tool registry"""
        self._tools: Dict[str, Tool] = {}
        self._tool_categories: Dict[str, List[str]] = {}
        logger.info("Tool registry initialized")
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
        
        Raises:
            ValueError: If tool name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        
        self._tools[tool.name] = tool
        
        # Add to category index
        if tool.category not in self._tool_categories:
            self._tool_categories[tool.category] = []
        self._tool_categories[tool.category].append(tool.name)
        
        logger.info(f"Tool registered: {tool.name} (category: {tool.category})")
    
    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def get_all(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def get_by_category(self, category: str) -> List[Tool]:
        """Get tools by category"""
        tool_names = self._tool_categories.get(category, [])
        return [self._tools[name] for name in tool_names]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of all tools with metadata"""
        return [tool.to_dict() for tool in self._tools.values()]
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all tools (for LLM integration)"""
        return [tool.get_schema() for tool in self._tools.values() if tool.enabled]
    
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters
        
        Returns:
            ToolResult
        
        Raises:
            ToolNotFoundError: If tool doesn't exist
        """
        tool = self.get(tool_name)
        if not tool:
            error_msg = f"Tool not found: {tool_name}"
            logger.error(error_msg)
            return ToolResult(
                status=ToolStatus.FAILED,
                error=error_msg,
                tool_name=tool_name,
            )
        
        if not tool.enabled:
            error_msg = f"Tool is disabled: {tool_name}"
            logger.warning(error_msg)
            return ToolResult(
                status=ToolStatus.SKIPPED,
                error=error_msg,
                tool_name=tool_name,
            )
        
        # Validate input
        if not tool.validate_input(**kwargs):
            error_msg = f"Invalid input parameters for tool: {tool_name}"
            logger.error(error_msg)
            return ToolResult(
                status=ToolStatus.FAILED,
                error=error_msg,
                tool_name=tool_name,
                input_params=kwargs,
            )
        
        try:
            logger.debug(f"Executing tool: {tool_name} with params: {kwargs}")
            result = await tool.execute(**kwargs)
            result.tool_name = tool_name
            result.input_params = kwargs
            return result
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ToolResult(
                status=ToolStatus.ERROR,
                error=error_msg,
                tool_name=tool_name,
                input_params=kwargs,
            )
    
    def unregister(self, name: str) -> bool:
        """Unregister a tool"""
        if name not in self._tools:
            return False
        
        tool = self._tools.pop(name)
        
        # Remove from category index
        if tool.category in self._tool_categories:
            self._tool_categories[tool.category].remove(name)
        
        logger.info(f"Tool unregistered: {name}")
        return True
    
    def enable_tool(self, name: str) -> bool:
        """Enable a tool"""
        tool = self.get(name)
        if tool:
            tool.enabled = True
            logger.info(f"Tool enabled: {name}")
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """Disable a tool"""
        tool = self.get(name)
        if tool:
            tool.enabled = False
            logger.info(f"Tool disabled: {name}")
            return True
        return False


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
