"""
Database module for S.H.I.E.L.D.

Data persistence layer with SQLite and PostgreSQL support.
"""

from shield.database.models import Base, User, Session, Conversation, Message, Project, Artifact
from shield.database.connection import (
    DatabaseConnection, initialize_database, get_database, get_db_session, SessionContext
)

__all__ = [
    # Models
    "Base",
    "User",
    "Session",
    "Conversation",
    "Message",
    "Project",
    "Artifact",
    # Connection
    "DatabaseConnection",
    "initialize_database",
    "get_database",
    "get_db_session",
    "SessionContext",
]
