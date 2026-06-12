"""
Tools module for S.H.I.E.L.D.

Provides base tool classes and tool registry.
"""

from shield.tools.base import Tool, ToolRegistry, get_tool_registry
from shield.tools.file_tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    CreateDirectoryTool,
    CopyFileTool,
    DeleteFileTool,
    register_file_tools,
)
from shield.tools.web_search_tools import (
    DuckDuckGoSearchTool,
    TavilySearchTool,
    FetchPageContentTool,
    register_web_search_tools,
)
from shield.tools.project_tools import (
    CreateProjectTool,
    CreateResearchProjectTool,
    GetProjectStructureTool,
    register_project_tools,
)

__all__ = [
    "Tool",
    "ToolRegistry",
    "get_tool_registry",
    # File tools
    "ReadFileTool",
    "WriteFileTool",
    "ListDirectoryTool",
    "CreateDirectoryTool",
    "CopyFileTool",
    "DeleteFileTool",
    "register_file_tools",
    # Web search tools
    "DuckDuckGoSearchTool",
    "TavilySearchTool",
    "FetchPageContentTool",
    "register_web_search_tools",
    # Project tools
    "CreateProjectTool",
    "CreateResearchProjectTool",
    "GetProjectStructureTool",
    "register_project_tools",
]

# Initialize all tools on import
def initialize_all_tools(tavily_api_key=None):
    """Register all tools with the global registry"""
    register_file_tools()
    register_web_search_tools(tavily_api_key)
    register_project_tools()
