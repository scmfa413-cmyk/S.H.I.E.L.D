# S.H.I.E.L.D. Developer Quick Reference - Phase 1

## Quick Start

### Setup
```bash
# Navigate to project
cd shield-project

# Install dependencies
pip install -e .
# or: pip install -r requirements.txt

# Ensure Ollama is running
ollama serve  # In another terminal

# Initialize
shield init
shield health
```

### Configuration
```python
from shield.core import Config

# Get global config
config = Config.get()

# Access settings
print(config.llm.model)           # Current model
print(config.core.log_level)      # Log level
print(config.llm.temperature)     # LLM temperature
print(config.memory.sqlite_db_path)  # Database path
```

### Using the Logger
```python
from shield.core import get_logger

logger = get_logger(__name__)

logger.info("Starting operation")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

### Creating a Tool

```python
from shield.tools import Tool, ToolParameter, get_tool_registry
from shield.core.types import ToolResult, ToolStatus

class MyTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Description of what this tool does",
            category="custom"  # or "file", "web", "code", etc.
        )
        
        # Register parameters
        self.register_parameters([
            ToolParameter(
                name="input_text",
                type="string",
                description="Text to process",
                required=True
            ),
            ToolParameter(
                name="options",
                type="object",
                description="Additional options",
                required=False
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool"""
        try:
            # Get parameters
            input_text = kwargs.get("input_text")
            options = kwargs.get("options", {})
            
            # Process
            result = f"Processed: {input_text}"
            
            # Return result
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=result,
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e),
            )

# Register the tool
registry = get_tool_registry()
registry.register(MyTool())

# Now it's available
registry.get("my_tool")
tool = registry.get("my_tool")
```

### Creating an Agent

```python
from shield.agents import Agent, get_orchestrator
from shield.core.types import Objective, ExecutionContext
from shield.core.llm_handler import LLMHandler
from shield.core import Config

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            agent_type="my_type",  # e.g., "research", "code"
            name="MyAgent",
            description="What this agent does",
            tools=["tool_name1", "tool_name2"]  # Tools it can use
        )
        
        # Optional: Initialize LLM handler
        self.llm = LLMHandler()
    
    async def execute_task(
        self,
        objective: Objective,
        context: ExecutionContext,
    ) -> dict:
        """Execute an objective"""
        self.set_status(AgentStatus.EXECUTING)
        
        try:
            # Log what we're doing
            logger.info(f"Executing: {objective.description}")
            
            # Think about the problem
            reasoning = await self.think(objective.description)
            
            # Create a plan
            plan = await self.plan(objective)
            
            # Execute plan...
            
            # Return result
            result = {
                "status": "completed",
                "output": "...",
                "reasoning": reasoning,
            }
            
            # Reflect on results
            reflection = await self.reflect(result)
            result["reflection"] = reflection
            
            return result
        except Exception as e:
            logger.error(f"Task failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def think(
        self,
        prompt: str,
        context: Optional[dict] = None,
    ) -> str:
        """Use LLM to think about a problem"""
        system_prompt = """You are a helpful AI assistant. 
        Provide clear, structured thinking."""
        
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        
        return response

# Register the agent
orchestrator = get_orchestrator()
my_agent = MyAgent()
orchestrator.register_agent(my_agent)
```

### Working with Types

```python
from shield.core.types import (
    Message, MessageRole, MessageType,
    Objective, Mission, MissionStatus,
    ToolResult, ToolStatus,
)
from datetime import datetime

# Create a message
message = Message(
    role=MessageRole.USER,
    type=MessageType.TEXT,
    content="Hello S.H.I.E.L.D.",
)

# Create an objective
objective = Objective(
    description="Research AI trends",
    agent_type="research",
    tools_required=["web_search"],
)

# Create a mission
mission = Mission(
    description="Research and generate report",
    objectives=[objective],
    status=MissionStatus.QUEUED,
)

# Convert to dict for storage
mission_dict = mission.to_dict()

# Restore from dict
mission_restored = Mission(**mission_dict)
```

### Using the Tool Registry

```python
from shield.tools import get_tool_registry

registry = get_tool_registry()

# List all tools
tools = registry.get_all()

# Get by category
search_tools = registry.get_by_category("web")

# Get schemas for LLM
schemas = registry.get_schemas()

# Execute a tool
result = await registry.execute(
    tool_name="web_search",
    query="AI trends 2025",
    max_results=5
)

if result.status.value == "success":
    print(f"Result: {result.output}")
else:
    print(f"Error: {result.error}")
```

### Using the Agent Orchestrator

```python
from shield.agents import get_orchestrator

orchestrator = get_orchestrator()

# Register agents
orchestrator.register_agent(my_agent_1)
orchestrator.register_agent(my_agent_2)

# Get agents
all_agents = orchestrator.get_all_agents()
research_agents = orchestrator.get_agents_by_type("research")

# Assign task
result = await orchestrator.assign_task(
    objective=my_objective,
    agent=my_agent  # Optional: specific agent
)
```

### CLI Usage

```bash
# Show help
shield --help

# Initialize
shield init

# Check health
shield health

# Show status
shield status

# List tools
shield tools

# List agents
shield agents

# Show configuration
shield config --show

# Save configuration
shield config --save-yaml ./my_config.yaml

# Version
shield version
```

## Common Patterns

### Pattern 1: Tool + Agent Integration
```python
# Tool provides capability
class AnalyzePDF(Tool):
    async def execute(self, file_path, **kwargs):
        # Read and analyze PDF
        pass

# Agent uses tool
class AnalysisAgent(Agent):
    async def execute_task(self, objective, context):
        # Call tool
        result = await self.tool_registry.execute("analyze_pdf")
        # Process result
```

### Pattern 2: Multi-Agent Coordination
```python
# Agent 1 researches
class ResearchAgent(Agent):
    async def execute_task(self, objective, context):
        # Research and return findings
        pass

# Agent 2 analyzes findings
class AnalysisAgent(Agent):
    async def execute_task(self, objective, context):
        # Get findings from context/memory
        # Analyze them
        pass

# Orchestrator coordinates
orchestrator.register_agent(ResearchAgent())
orchestrator.register_agent(AnalysisAgent())
# Orchestrator assigns tasks in sequence
```

### Pattern 3: Async Streaming
```python
# Use LLM streaming for real-time output
async def stream_generation(prompt):
    llm = LLMHandler()
    async for chunk in llm.generate_stream(prompt):
        print(chunk, end="", flush=True)
    await llm.close()

# Run it
import asyncio
asyncio.run(stream_generation("Write a poem"))
```

## File Organization

When adding new code:

```
shield/
├── core/
│   └── new_module.py        # Core functionality
├── agents/
│   └── my_agent.py          # New agent type
├── tools/
│   └── my_tool.py           # New tool
├── memory/
│   └── storage.py           # Memory implementation
├── cli/
│   ├── commands/
│   │   └── my_command.py    # New CLI command
│   └── main.py
└── __init__.py

tests/
├── unit/
│   └── test_my_module.py
└── integration/
    └── test_integration.py
```

## Debugging Tips

### Enable Debug Mode
```bash
# Via .env
SHIELD_CORE__DEBUG=true

# Via config
config.core.debug = True
```

### Increase Log Level
```bash
# Via .env
SHIELD_CORE__LOG_LEVEL=DEBUG

# Via config
config.core.log_level = "DEBUG"
```

### Check Tool Schemas
```python
from shield.tools import get_tool_registry

registry = get_tool_registry()
for schema in registry.get_schemas():
    print(schema)
```

### Trace Agent Execution
```python
agent = MyAgent()
logger = get_logger("agent_trace")

# Messages are automatically logged
for msg in agent.get_messages():
    logger.info(f"Role: {msg.role}, Content: {msg.content[:100]}...")
```

## Next Steps

After Phase 1, focus on:

1. **Phase 2: Memory Layer**
   - Implement database connections
   - Add conversation storage
   - Create vector search

2. **Phase 3: Core Tools**
   - File reading/analysis
   - Web search integration
   - Command execution

3. **Phase 4: Specialized Agents**
   - Research agent with web search
   - Code generation agent
   - Document analysis agent

## Resources

- `ARCHITECTURE.md` - Detailed system design
- `README.md` - Getting started and overview
- `PHASE_1_COMPLETE.md` - What's implemented
- Source code with inline documentation

---

**Happy building! 🛡️**
