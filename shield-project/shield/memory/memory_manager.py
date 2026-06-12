"""
Memory manager for S.H.I.E.L.D.

Handles conversation persistence, project memory, and knowledge storage.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from shield.database.connection import get_db_session
from shield.database.models import (
    Conversation, Message, Project, Artifact, ResearchTopic, Source, User, Knowledge
)
from shield.core.types import Message as MessageType, MessageRole
from shield.core.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """
    Central memory management service for S.H.I.E.L.D.
    
    Handles:
    - Conversation persistence across sessions
    - Project memory storage
    - Knowledge storage
    - Memory retrieval and search
    - Memory cleanup
    """
    
    def __init__(self, user_id: str):
        """
        Initialize memory manager.
        
        Args:
            user_id: User ID for memory scoping
        """
        self.user_id = user_id
        logger.info(f"Memory manager initialized for user: {user_id}")
    
    # ========== USER MANAGEMENT ==========
    
    def get_or_create_user(self, username: str = "default") -> str:
        """Get or create user"""
        with get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                user_id = str(uuid4())
                user = User(user_id=user_id, username=username)
                session.add(user)
                session.commit()
                logger.info(f"Created new user: {username}")
                return user_id
            return user.user_id
    
    # ========== CONVERSATION MANAGEMENT ==========
    
    def create_conversation(
        self,
        title: str,
        description: str = "",
        project_id: Optional[str] = None,
        tags: List[str] = None,
    ) -> str:
        """
        Create a new conversation.
        
        Args:
            title: Conversation title
            description: Description
            project_id: Associated project
            tags: Tags for organization
        
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid4())
        
        with get_db_session() as session:
            conversation = Conversation(
                conversation_id=conversation_id,
                user_id=self.user_id,
                project_id=project_id,
                title=title,
                description=description,
                tags=tags or [],
            )
            session.add(conversation)
            session.commit()
            logger.info(f"Created conversation: {title} ({conversation_id})")
        
        return conversation_id
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: Dict[str, Any] = None,
        tool_calls: List[Dict] = None,
    ) -> str:
        """
        Add a message to conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role (user, assistant, etc.)
            content: Message content
            message_type: Message type (text, code, etc.)
            metadata: Additional metadata
            tool_calls: Tool calls made
        
        Returns:
            Message ID
        """
        message_id = str(uuid4())
        
        with get_db_session() as session:
            message = Message(
                message_id=message_id,
                conversation_id=conversation_id,
                role=role,
                message_type=message_type,
                content=content,
                metadata=metadata or {},
                tool_calls=tool_calls or [],
            )
            session.add(message)
            session.commit()
        
        return message_id
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation details"""
        with get_db_session() as session:
            conv = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            
            if not conv:
                return None
            
            # Get messages
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()
            
            return {
                "conversation": conv.to_dict(),
                "messages": [msg.to_dict() for msg in messages],
                "message_count": len(messages),
            }
    
    def list_conversations(
        self,
        project_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List conversations for user.
        
        Args:
            project_id: Filter by project
            limit: Max results
        
        Returns:
            List of conversation details
        """
        with get_db_session() as session:
            query = session.query(Conversation).filter(
                Conversation.user_id == self.user_id
            )
            
            if project_id:
                query = query.filter(Conversation.project_id == project_id)
            
            conversations = query.order_by(
                desc(Conversation.updated_at)
            ).limit(limit).all()
            
            return [conv.to_dict() for conv in conversations]
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search conversations by title or description.
        
        Args:
            query: Search query
            limit: Max results
        
        Returns:
            List of matching conversations
        """
        with get_db_session() as session:
            conversations = session.query(Conversation).filter(
                and_(
                    Conversation.user_id == self.user_id,
                    or_(
                        Conversation.title.ilike(f"%{query}%"),
                        Conversation.description.ilike(f"%{query}%"),
                    )
                )
            ).order_by(desc(Conversation.updated_at)).limit(limit).all()
            
            return [conv.to_dict() for conv in conversations]
    
    # ========== PROJECT MANAGEMENT ==========
    
    def create_project(
        self,
        name: str,
        description: str = "",
        project_type: str = "general",
        root_path: Optional[Path] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Description
            project_type: Type (research, code, analysis)
            root_path: Project root directory
            metadata: Additional metadata
        
        Returns:
            Project ID
        """
        project_id = str(uuid4())
        
        if root_path is None:
            from shield.core.config import Config
            config = Config.get()
            root_path = Path(config.core.data_dir) / "projects" / name.lower().replace(" ", "_")
        
        root_path = Path(root_path)
        root_path.mkdir(parents=True, exist_ok=True)
        
        with get_db_session() as session:
            project = Project(
                project_id=project_id,
                user_id=self.user_id,
                name=name,
                description=description,
                root_path=str(root_path),
                project_type=project_type,
                metadata=metadata or {},
            )
            session.add(project)
            session.commit()
            logger.info(f"Created project: {name} ({project_id})")
        
        return project_id
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details"""
        with get_db_session() as session:
            project = session.query(Project).filter(
                Project.project_id == project_id
            ).first()
            
            if not project:
                return None
            
            # Get artifacts and conversations
            artifacts = session.query(Artifact).filter(
                Artifact.project_id == project_id
            ).all()
            
            conversations = session.query(Conversation).filter(
                Conversation.project_id == project_id
            ).all()
            
            return {
                "project": project.to_dict(),
                "artifacts": [art.to_dict() for art in artifacts],
                "artifact_count": len(artifacts),
                "conversation_count": len(conversations),
            }
    
    def list_projects(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all projects for user"""
        with get_db_session() as session:
            projects = session.query(Project).filter(
                Project.user_id == self.user_id
            ).order_by(desc(Project.updated_at)).limit(limit).all()
            
            return [proj.to_dict() for proj in projects]
    
    # ========== ARTIFACT MANAGEMENT ==========
    
    def create_artifact(
        self,
        project_id: str,
        name: str,
        file_path: Path,
        artifact_type: str = "document",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Create an artifact record.
        
        Args:
            project_id: Project ID
            name: Artifact name
            file_path: Path to file
            artifact_type: Type (code, document, report, data)
            metadata: Additional metadata
        
        Returns:
            Artifact ID
        """
        artifact_id = str(uuid4())
        file_path = Path(file_path)
        
        size_bytes = file_path.stat().st_size if file_path.exists() else 0
        
        with get_db_session() as session:
            artifact = Artifact(
                artifact_id=artifact_id,
                project_id=project_id,
                name=name,
                artifact_type=artifact_type,
                file_path=str(file_path),
                size_bytes=size_bytes,
                metadata=metadata or {},
            )
            session.add(artifact)
            session.commit()
            logger.info(f"Created artifact: {name}")
        
        return artifact_id
    
    def list_artifacts(self, project_id: str) -> List[Dict[str, Any]]:
        """List artifacts for project"""
        with get_db_session() as session:
            artifacts = session.query(Artifact).filter(
                Artifact.project_id == project_id
            ).order_by(Artifact.created_at).all()
            
            return [art.to_dict() for art in artifacts]
    
    # ========== RESEARCH TOPICS & SOURCES ==========
    
    def create_research_topic(
        self,
        project_id: str,
        title: str,
        query: str,
    ) -> str:
        """Create a research topic"""
        topic_id = str(uuid4())
        
        with get_db_session() as session:
            topic = ResearchTopic(
                topic_id=topic_id,
                project_id=project_id,
                title=title,
                query=query,
            )
            session.add(topic)
            session.commit()
            logger.info(f"Created research topic: {title}")
        
        return topic_id
    
    def add_source(
        self,
        topic_id: str,
        url: str,
        title: str = "",
        content: str = "",
        snippet: str = "",
        source_type: str = "web",
        relevance_score: float = 1.0,
    ) -> str:
        """Add a research source"""
        source_id = str(uuid4())
        
        with get_db_session() as session:
            source = Source(
                source_id=source_id,
                topic_id=topic_id,
                url=url,
                title=title,
                snippet=snippet,
                content=content,
                source_type=source_type,
                relevance_score=relevance_score,
                fetched_at=datetime.utcnow(),
            )
            session.add(source)
            session.commit()
        
        return source_id
    
    def get_research_findings(self, topic_id: str) -> Dict[str, Any]:
        """Get research findings for topic"""
        with get_db_session() as session:
            topic = session.query(ResearchTopic).filter(
                ResearchTopic.topic_id == topic_id
            ).first()
            
            if not topic:
                return None
            
            sources = session.query(Source).filter(
                Source.topic_id == topic_id
            ).order_by(Source.relevance_score.desc()).all()
            
            return {
                "topic": {
                    "title": topic.title,
                    "query": topic.query,
                    "created_at": topic.created_at.isoformat(),
                },
                "sources": [
                    {
                        "url": src.url,
                        "title": src.title,
                        "snippet": src.snippet,
                        "relevance_score": src.relevance_score,
                    }
                    for src in sources
                ],
                "source_count": len(sources),
            }
    
    # ========== KNOWLEDGE STORAGE ==========
    
    def store_knowledge(
        self,
        key: str,
        value: Any,
        category: str = None,
    ) -> None:
        """
        Store general knowledge.
        
        Args:
            key: Knowledge key
            value: Knowledge value (will be JSON serialized)
            category: Knowledge category
        """
        with get_db_session() as session:
            # Try to update existing
            knowledge = session.query(Knowledge).filter(Knowledge.key == key).first()
            
            if knowledge:
                knowledge.value = value
                knowledge.updated_at = datetime.utcnow()
            else:
                knowledge = Knowledge(
                    knowledge_id=str(uuid4()),
                    key=key,
                    value=value,
                    category=category,
                )
                session.add(knowledge)
            
            session.commit()
    
    def retrieve_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve knowledge by key"""
        with get_db_session() as session:
            knowledge = session.query(Knowledge).filter(Knowledge.key == key).first()
            return knowledge.value if knowledge else None
    
    # ========== STATISTICS ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        with get_db_session() as session:
            conv_count = session.query(Conversation).filter(
                Conversation.user_id == self.user_id
            ).count()
            
            msg_count = session.query(Message).join(Conversation).filter(
                Conversation.user_id == self.user_id
            ).count()
            
            proj_count = session.query(Project).filter(
                Project.user_id == self.user_id
            ).count()
            
            art_count = session.query(Artifact).join(Project).filter(
                Project.user_id == self.user_id
            ).count()
            
            return {
                "conversations": conv_count,
                "messages": msg_count,
                "projects": proj_count,
                "artifacts": art_count,
            }


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def initialize_memory(user_id: str = "default") -> MemoryManager:
    """Initialize the global memory manager"""
    global _memory_manager
    _memory_manager = MemoryManager(user_id)
    return _memory_manager


def get_memory() -> MemoryManager:
    """Get the global memory manager"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = initialize_memory()
    return _memory_manager
