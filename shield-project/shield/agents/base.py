"""
Agent framework for S.H.I.E.L.D.

Defines base Agent class and agent orchestration system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import json

from shield.core.types import (
    Message,
    MessageRole,
    TaskStatus,
    AgentStatus,
    Objective,
    ExecutionContext,
)
from shield.core.logger import get_logger
from shield.tools.base import ToolRegistry, get_tool_registry

logger = get_logger(__name__)


@dataclass
class AgentState:
    """Agent execution state"""
    agent_id: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    memory_buffer: List[Message] = field(default_factory=list)
    context_stack: List[Dict[str, Any]] = field(default_factory=list)
    execution_count: int = 0
    error_count: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)


class Agent(ABC):
    """
    Base class for all agents in S.H.I.E.L.D.
    
    Agents are autonomous entities that can:
    - Think and reason about problems
    - Make decisions
    - Call tools
    - Communicate with other agents
    - Learn from interactions
    
    Specialized agents inherit from this class:
    - ResearchAgent: Web research and information gathering
    - CodeAgent: Code generation and analysis
    - AnalysisAgent: Data and document analysis
    - ExecutionAgent: Task automation and system control
    - LearningAgent: Memory management and optimization
    """
    
    def __init__(
        self,
        agent_type: str,
        name: str,
        description: str,
        tools: Optional[List[str]] = None,
    ):
        """
        Initialize agent.
        
        Args:
            agent_type: Agent type identifier (e.g., "research", "code")
            name: Human-readable agent name
            description: Agent description
            tools: List of tool names this agent can use
        """
        self.agent_id = str(uuid4())
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.tools = tools or []
        
        # State management
        self.state = AgentState(agent_id=self.agent_id)
        
        # Tool registry
        self.tool_registry = get_tool_registry()
        
        # Message history
        self.messages: List[Message] = []
        
        # Capabilities
        self.capabilities: Set[str] = set()
        self._register_capabilities()
        
        logger.info(f"Agent initialized: {name} ({agent_type}) - ID: {self.agent_id}")
    
    def _register_capabilities(self) -> None:
        """Register agent capabilities"""
        # Default capabilities
        self.capabilities.add("think")
        self.capabilities.add("communicate")
        
        # Tool-based capabilities
        for tool_name in self.tools:
            self.capabilities.add(f"use_{tool_name}")
    
    def add_message(self, message: Message) -> None:
        """Add message to history"""
        self.messages.append(message)
        self.state.memory_buffer.append(message)
    
    def get_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages"""
        return self.messages[-limit:]
    
    def clear_messages(self) -> None:
        """Clear message history"""
        self.messages.clear()
        self.state.memory_buffer.clear()
    
    def set_status(self, status: AgentStatus) -> None:
        """Set agent status"""
        self.state.status = status
        self.state.last_activity = datetime.utcnow()
        logger.debug(f"Agent {self.name} status: {status.value}")
    
    @abstractmethod
    async def execute_task(
        self,
        objective: Objective,
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """
        Execute a task/objective.
        
        Args:
            objective: Objective to execute
            context: Execution context
        
        Returns:
            Result dictionary with execution output
        """
        pass
    
    @abstractmethod
    async def think(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Think about a problem and generate reasoning.
        
        Args:
            prompt: Problem description
            context: Additional context
        
        Returns:
            Reasoning output
        """
        pass
    
    async def plan(self, objective: Objective) -> List[Dict[str, Any]]:
        """
        Create a plan to achieve an objective.
        
        Args:
            objective: Objective to plan for
        
        Returns:
            List of subtasks/steps
        """
        prompt = f"""
        Create a detailed plan to accomplish the following objective:
        
        Objective: {objective.description}
        
        Provide step-by-step subtasks, identifying:
        1. Required tools
        2. Prerequisites
        3. Success criteria
        4. Potential risks
        """
        
        reasoning = await self.think(prompt)
        
        # Parse reasoning into plan steps
        plan_steps = [
            {
                "description": reasoning,
                "tools": objective.tools_required,
                "priority": 1,
            }
        ]
        
        return plan_steps
    
    async def reflect(self, execution_result: Dict[str, Any]) -> str:
        """
        Reflect on execution results.
        
        Args:
            execution_result: Result from task execution
        
        Returns:
            Reflection/analysis of results
        """
        prompt = f"""
        Reflect on the following execution result:
        
        Result: {json.dumps(execution_result, indent=2)}
        
        Analyze:
        1. Did we achieve the objective?
        2. What went well?
        3. What could be improved?
        4. What did we learn?
        """
        
        return await self.think(prompt)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "name": self.name,
            "description": self.description,
            "status": self.state.status.value,
            "tools": self.tools,
            "capabilities": list(self.capabilities),
            "messages_count": len(self.messages),
            "execution_count": self.state.execution_count,
            "error_count": self.state.error_count,
        }


class AgentOrchestrator:
    """
    Orchestrates multiple agents for collaborative task execution.
    
    Responsibilities:
    - Agent registration and management
    - Task assignment to appropriate agents
    - Inter-agent communication
    - Task dependency management
    - Result aggregation
    """
    
    def __init__(self):
        """Initialize orchestrator"""
        self.agents: Dict[str, Agent] = {}
        self.agent_types: Dict[str, List[str]] = {}
        logger.info("Agent orchestrator initialized")
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent instance
        """
        self.agents[agent.agent_id] = agent
        
        # Index by type
        if agent.agent_type not in self.agent_types:
            self.agent_types[agent.agent_type] = []
        self.agent_types[agent.agent_type].append(agent.agent_id)
        
        logger.info(f"Agent registered: {agent.name} ({agent.agent_id})")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[Agent]:
        """Get all agents of a specific type"""
        agent_ids = self.agent_types.get(agent_type, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def get_agents_for_tools(self, tools: List[str]) -> List[Agent]:
        """Get agents capable of using specific tools"""
        matching_agents = []
        for agent in self.agents.values():
            if all(tool in agent.tools for tool in tools):
                matching_agents.append(agent)
        return matching_agents
    
    def get_all_agents(self) -> List[Agent]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    async def assign_task(
        self,
        objective: Objective,
        agent: Optional[Agent] = None,
    ) -> Dict[str, Any]:
        """
        Assign a task to an agent.
        
        Args:
            objective: Objective to execute
            agent: Specific agent (if None, find suitable agent)
        
        Returns:
            Execution result
        """
        if agent is None:
            # Find suitable agent
            agents = self.get_agents_by_type(objective.agent_type)
            if not agents:
                logger.error(f"No agent found for type: {objective.agent_type}")
                return {"error": f"No agent available for {objective.agent_type}"}
            agent = agents[0]
        
        agent.set_status(AgentStatus.EXECUTING)
        objective.assigned_agent_id = agent.agent_id
        
        try:
            context = ExecutionContext(
                mission_id="",  # Will be set by caller
                objective_id=objective.id,
                agent_id=agent.agent_id,
            )
            
            result = await agent.execute_task(objective, context)
            agent.state.execution_count += 1
            
            return result
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}", exc_info=True)
            agent.state.error_count += 1
            return {"error": str(e)}
        finally:
            agent.set_status(AgentStatus.IDLE)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """Get list of all agents with metadata"""
        return [agent.to_dict() for agent in self.agents.values()]


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the global agent orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
