"""
File management tools for S.H.I.E.L.D.

Tools for reading, writing, and analyzing files.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib

from shield.tools.base import Tool, ToolParameter
from shield.core.types import ToolResult, ToolStatus
from shield.core.logger import get_logger

logger = get_logger(__name__)


class ReadFileTool(Tool):
    """Read file contents"""
    
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read contents of a file (txt, py, json, yaml, md, csv)",
            category="file",
        )
        
        self.register_parameters([
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to file to read",
                required=True
            ),
            ToolParameter(
                name="lines_only",
                type="boolean",
                description="Return as list of lines instead of full text",
                required=False,
                default=False
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute read file"""
        try:
            file_path = Path(kwargs.get("file_path"))
            lines_only = kwargs.get("lines_only", False)
            
            if not file_path.exists():
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"File not found: {file_path}"
                )
            
            if not file_path.is_file():
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Not a file: {file_path}"
                )
            
            # Read file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if lines_only:
                output = content.splitlines()
            else:
                output = content
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "content": output,
                    "file_path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "line_count": len(content.splitlines()),
                }
            )
        
        except Exception as e:
            logger.error(f"Read file failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class WriteFileTool(Tool):
    """Write or create a file"""
    
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write content to a file (creates if not exists)",
            category="file",
        )
        
        self.register_parameters([
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to file to write",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write",
                required=True
            ),
            ToolParameter(
                name="append",
                type="boolean",
                description="Append instead of overwrite",
                required=False,
                default=False
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute write file"""
        try:
            file_path = Path(kwargs.get("file_path"))
            content = kwargs.get("content")
            append = kwargs.get("append", False)
            
            # Create parent directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            mode = "a" if append else "w"
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "file_path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "mode": mode,
                }
            )
        
        except Exception as e:
            logger.error(f"Write file failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class ListDirectoryTool(Tool):
    """List directory contents"""
    
    def __init__(self):
        super().__init__(
            name="list_directory",
            description="List files and folders in a directory",
            category="file",
        )
        
        self.register_parameters([
            ToolParameter(
                name="directory_path",
                type="string",
                description="Path to directory",
                required=True
            ),
            ToolParameter(
                name="recursive",
                type="boolean",
                description="List recursively",
                required=False,
                default=False
            ),
            ToolParameter(
                name="max_depth",
                type="integer",
                description="Max depth for recursive listing",
                required=False,
                default=3
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute list directory"""
        try:
            dir_path = Path(kwargs.get("directory_path"))
            recursive = kwargs.get("recursive", False)
            max_depth = kwargs.get("max_depth", 3)
            
            if not dir_path.exists():
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Directory not found: {dir_path}"
                )
            
            if not dir_path.is_dir():
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Not a directory: {dir_path}"
                )
            
            # List contents
            def get_items(path: Path, depth: int = 0) -> list:
                if depth > max_depth:
                    return []
                
                items = []
                try:
                    for item in sorted(path.iterdir()):
                        item_info = {
                            "name": item.name,
                            "type": "directory" if item.is_dir() else "file",
                            "path": str(item.relative_to(dir_path)),
                        }
                        
                        if item.is_file():
                            item_info["size_bytes"] = item.stat().st_size
                        
                        items.append(item_info)
                        
                        # Recurse if directory
                        if recursive and item.is_dir() and depth < max_depth:
                            item_info["contents"] = get_items(item, depth + 1)
                
                except PermissionError:
                    pass
                
                return items
            
            contents = get_items(dir_path)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "directory": str(dir_path),
                    "item_count": len(contents),
                    "contents": contents,
                }
            )
        
        except Exception as e:
            logger.error(f"List directory failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class CreateDirectoryTool(Tool):
    """Create a directory"""
    
    def __init__(self):
        super().__init__(
            name="create_directory",
            description="Create a directory (including parent directories)",
            category="file",
        )
        
        self.register_parameters([
            ToolParameter(
                name="directory_path",
                type="string",
                description="Path to directory to create",
                required=True
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute create directory"""
        try:
            dir_path = Path(kwargs.get("directory_path"))
            
            if dir_path.exists() and dir_path.is_dir():
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    output={
                        "directory": str(dir_path),
                        "status": "already_exists",
                    }
                )
            
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "directory": str(dir_path),
                    "status": "created",
                }
            )
        
        except Exception as e:
            logger.error(f"Create directory failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class CopyFileTool(Tool):
    """Copy a file"""
    
    def __init__(self):
        super().__init__(
            name="copy_file",
            description="Copy a file from source to destination",
            category="file",
        )
        
        self.register_parameters([
            ToolParameter(
                name="source_path",
                type="string",
                description="Source file path",
                required=True
            ),
            ToolParameter(
                name="destination_path",
                type="string",
                description="Destination file path",
                required=True
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute copy file"""
        try:
            import shutil
            
            source = Path(kwargs.get("source_path"))
            destination = Path(kwargs.get("destination_path"))
            
            if not source.exists():
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Source file not found: {source}"
                )
            
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "source": str(source),
                    "destination": str(destination),
                    "size_bytes": destination.stat().st_size,
                }
            )
        
        except Exception as e:
            logger.error(f"Copy file failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class DeleteFileTool(Tool):
    """Delete a file"""
    
    def __init__(self):
        super().__init__(
            name="delete_file",
            description="Delete a file",
            category="file",
        )
        
        self.register_parameters([
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to file to delete",
                required=True
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute delete file"""
        try:
            file_path = Path(kwargs.get("file_path"))
            
            if not file_path.exists():
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"File not found: {file_path}"
                )
            
            file_path.unlink()
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "file_path": str(file_path),
                    "status": "deleted",
                }
            )
        
        except Exception as e:
            logger.error(f"Delete file failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


# Export all tools
def register_file_tools():
    """Register all file tools with the global registry"""
    from shield.tools.base import get_tool_registry
    
    registry = get_tool_registry()
    
    tools = [
        ReadFileTool(),
        WriteFileTool(),
        ListDirectoryTool(),
        CreateDirectoryTool(),
        CopyFileTool(),
        DeleteFileTool(),
    ]
    
    for tool in tools:
        registry.register(tool)
    
    logger.info(f"Registered {len(tools)} file tools")
