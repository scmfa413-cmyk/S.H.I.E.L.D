"""
Project scaffolding tools for S.H.I.E.L.D.

Tools for creating and managing project structures.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from shield.tools.base import Tool, ToolParameter
from shield.core.types import ToolResult, ToolStatus
from shield.core.logger import get_logger

logger = get_logger(__name__)


class CreateProjectTool(Tool):
    """Create a new project"""
    
    def __init__(self):
        super().__init__(
            name="create_project",
            description="Create a new project with standard structure",
            category="project",
        )
        
        self.register_parameters([
            ToolParameter(
                name="project_name",
                type="string",
                description="Name of the project",
                required=True
            ),
            ToolParameter(
                name="project_type",
                type="string",
                description="Type of project (research, code, analysis)",
                required=False,
                default="general"
            ),
            ToolParameter(
                name="root_path",
                type="string",
                description="Root directory for project",
                required=False,
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute create project"""
        try:
            project_name = kwargs.get("project_name")
            project_type = kwargs.get("project_type", "general")
            root_path = kwargs.get("root_path")
            
            if root_path is None:
                from shield.core.config import Config
                config = Config.get()
                root_path = Path(config.core.data_dir) / "projects" / project_name.lower().replace(" ", "_")
            else:
                root_path = Path(root_path)
            
            # Create standard directory structure
            directories = {
                "general": ["artifacts", "memory"],
                "research": ["sources", "findings", "reports", "artifacts"],
                "code": ["src", "tests", "docs", "artifacts"],
                "analysis": ["data", "results", "reports", "artifacts"],
            }
            
            dirs_to_create = directories.get(project_type, directories["general"])
            
            # Create directories
            created_dirs = []
            for dir_name in dirs_to_create:
                dir_path = root_path / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path.relative_to(root_path)))
            
            # Create metadata file
            metadata = {
                "name": project_name,
                "type": project_type,
                "created_at": str(__import__("datetime").datetime.utcnow()),
                "structure": dirs_to_create,
            }
            
            metadata_path = root_path / "project.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "project_name": project_name,
                    "project_type": project_type,
                    "root_path": str(root_path),
                    "directories": created_dirs,
                    "structure": metadata,
                }
            )
        
        except Exception as e:
            logger.error(f"Create project failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class CreateResearchProjectTool(Tool):
    """Create a research project with optimized structure"""
    
    def __init__(self):
        super().__init__(
            name="create_research_project",
            description="Create a research project with optimized structure",
            category="project",
        )
        
        self.register_parameters([
            ToolParameter(
                name="project_name",
                type="string",
                description="Name of research project",
                required=True
            ),
            ToolParameter(
                name="research_topic",
                type="string",
                description="Main research topic",
                required=False,
            ),
            ToolParameter(
                name="root_path",
                type="string",
                description="Root directory",
                required=False,
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute create research project"""
        try:
            project_name = kwargs.get("project_name")
            research_topic = kwargs.get("research_topic", "")
            root_path = kwargs.get("root_path")
            
            if root_path is None:
                from shield.core.config import Config
                config = Config.get()
                root_path = Path(config.core.data_dir) / "projects" / project_name.lower().replace(" ", "_")
            else:
                root_path = Path(root_path)
            
            # Create research-specific structure
            dirs = [
                "sources",
                "findings",
                "findings/raw",
                "findings/analyzed",
                "reports",
                "reports/drafts",
                "reports/final",
                "artifacts",
                "artifacts/images",
                "artifacts/data",
            ]
            
            for dir_name in dirs:
                (root_path / dir_name).mkdir(parents=True, exist_ok=True)
            
            # Create research template files
            readme_content = f"""# {project_name}

## Topic: {research_topic}

### Project Structure

- **sources/**: Raw research sources and links
- **findings/**: Collected and analyzed findings
  - **raw/**: Raw extracted findings
  - **analyzed/**: Processed and analyzed findings
- **reports/**: Generated reports
  - **drafts/**: Working drafts
  - **final/**: Finalized reports
- **artifacts/**: Supporting materials
  - **images/**: Images and diagrams
  - **data/**: Raw data files

### Research Progress

- [ ] Initial research
- [ ] Source collection
- [ ] Analysis
- [ ] Report generation
- [ ] Final review

### Key Findings

(To be updated as research progresses)

### Sources

(Main sources to be documented)
"""
            
            with open(root_path / "README.md", "w") as f:
                f.write(readme_content)
            
            # Create metadata
            metadata = {
                "name": project_name,
                "type": "research",
                "topic": research_topic,
                "created_at": str(__import__("datetime").datetime.utcnow()),
            }
            
            with open(root_path / "project.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "project_name": project_name,
                    "root_path": str(root_path),
                    "structure": dirs,
                    "files_created": ["README.md", "project.json"],
                }
            )
        
        except Exception as e:
            logger.error(f"Create research project failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class GetProjectStructureTool(Tool):
    """Get project structure and metadata"""
    
    def __init__(self):
        super().__init__(
            name="get_project_structure",
            description="Get project structure and metadata",
            category="project",
        )
        
        self.register_parameters([
            ToolParameter(
                name="project_path",
                type="string",
                description="Path to project",
                required=True
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute get project structure"""
        try:
            project_path = Path(kwargs.get("project_path"))
            
            if not project_path.exists():
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Project path not found: {project_path}"
                )
            
            # Load metadata if exists
            metadata = None
            metadata_path = project_path / "project.json"
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
            
            # Get directory tree
            def get_tree(path, prefix="", max_depth=3, current_depth=0):
                if current_depth > max_depth:
                    return []
                
                items = []
                try:
                    for item in sorted(path.iterdir()):
                        if item.name.startswith("."):
                            continue
                        
                        rel_path = item.relative_to(project_path)
                        if item.is_dir():
                            items.append(f"{prefix}📁 {item.name}/")
                            if current_depth < max_depth:
                                sub_items = get_tree(item, prefix + "  ", max_depth, current_depth + 1)
                                items.extend(sub_items)
                        else:
                            size = item.stat().st_size
                            items.append(f"{prefix}📄 {item.name} ({size} bytes)")
                
                except PermissionError:
                    items.append(f"{prefix}❌ Permission denied")
                
                return items
            
            tree = get_tree(project_path)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "project_path": str(project_path),
                    "metadata": metadata,
                    "structure": tree,
                }
            )
        
        except Exception as e:
            logger.error(f"Get project structure failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


# Export all tools
def register_project_tools():
    """Register all project tools with the global registry"""
    from shield.tools.base import get_tool_registry
    
    registry = get_tool_registry()
    
    tools = [
        CreateProjectTool(),
        CreateResearchProjectTool(),
        GetProjectStructureTool(),
    ]
    
    for tool in tools:
        registry.register(tool)
    
    logger.info(f"Registered {len(tools)} project tools")
