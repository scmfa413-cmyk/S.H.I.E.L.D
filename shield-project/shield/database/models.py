"""
Database models for S.H.I.E.L.D.

Defines SQLAlchemy models for all entities.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, JSON, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import json
from pathlib import Path

Base = declarative_base()


class User(Base):
    """User entity"""
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    preferences = Column(JSON, default=dict)
    
    # Relationships
    sessions = relationship("Session", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    projects = relationship("Project", back_populates="user")
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "preferences": self.preferences,
        }


class Session(Base):
    """Session entity"""
    __tablename__ = "sessions"
    
    session_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    context = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class Conversation(Base):
    """Conversation entity"""
    __tablename__ = "conversations"
    
    conversation_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    project = relationship("Project", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags,
            "message_count": len(self.messages) if self.messages else 0,
        }


class Message(Base):
    """Message entity"""
    __tablename__ = "messages"
    
    message_id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), ForeignKey("conversations.conversation_id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system, agent
    message_type = Column(String(20), default="text")  # text, code, file, report
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    tokens_used = Column(Integer, default=0)
    tool_calls = Column(JSON, default=list)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    embeddings = relationship("Embedding", back_populates="message")
    
    def to_dict(self):
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "message_type": self.message_type,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tokens_used": self.tokens_used,
        }


class Project(Base):
    """Project entity"""
    __tablename__ = "projects"
    
    project_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    root_path = Column(String(512), nullable=False)
    project_type = Column(String(50), default="general")  # research, code, analysis
    status = Column(String(20), default="active")  # active, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    conversations = relationship("Conversation", back_populates="project")
    artifacts = relationship("Artifact", back_populates="project")
    research_topics = relationship("ResearchTopic", back_populates="project")
    
    def to_dict(self):
        return {
            "project_id": self.project_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "root_path": self.root_path,
            "project_type": self.project_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Artifact(Base):
    """Artifact entity (generated files, code, reports)"""
    __tablename__ = "artifacts"
    
    artifact_id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    name = Column(String(255), nullable=False)
    artifact_type = Column(String(50), default="document")  # code, document, report, data
    file_path = Column(String(512), nullable=False)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    size_bytes = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("Project", back_populates="artifacts")
    
    def to_dict(self):
        return {
            "artifact_id": self.artifact_id,
            "project_id": self.project_id,
            "name": self.name,
            "artifact_type": self.artifact_type,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "size_bytes": self.size_bytes,
        }


class ResearchTopic(Base):
    """Research topic entity"""
    __tablename__ = "research_topics"
    
    topic_id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.project_id"), nullable=False)
    title = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    findings_summary = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("Project", back_populates="research_topics")
    sources = relationship("Source", back_populates="topic")


class Source(Base):
    """Research source entity"""
    __tablename__ = "sources"
    
    source_id = Column(String(36), primary_key=True)
    topic_id = Column(String(36), ForeignKey("research_topics.topic_id"), nullable=False)
    url = Column(String(512), nullable=False)
    title = Column(String(255), nullable=True)
    content_hash = Column(String(64), nullable=True)
    snippet = Column(Text, nullable=True)
    source_type = Column(String(50), default="web")  # web, document, internal
    relevance_score = Column(Float, default=1.0)
    fetched_at = Column(DateTime, nullable=True)
    content = Column(Text, nullable=True)
    
    # Relationships
    topic = relationship("ResearchTopic", back_populates="sources")


class Embedding(Base):
    """Embedding entity for semantic search"""
    __tablename__ = "embeddings"
    
    embedding_id = Column(String(36), primary_key=True)
    message_id = Column(String(36), ForeignKey("messages.message_id"), nullable=True)
    artifact_id = Column(String(36), ForeignKey("artifacts.artifact_id"), nullable=True)
    text_chunk = Column(Text, nullable=False)
    vector_id = Column(String(255), nullable=True)  # ChromaDB vector ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="embeddings")


class ToolExecution(Base):
    """Tool execution log"""
    __tablename__ = "tool_executions"
    
    execution_id = Column(String(36), primary_key=True)
    tool_name = Column(String(255), nullable=False)
    parameters = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    status = Column(String(20), default="success")  # success, failed, error
    duration_ms = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Knowledge(Base):
    """General knowledge store"""
    __tablename__ = "knowledge"
    
    knowledge_id = Column(String(36), primary_key=True)
    key = Column(String(255), nullable=False, unique=True)
    value = Column(JSON, nullable=False)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "knowledge_id": self.knowledge_id,
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
