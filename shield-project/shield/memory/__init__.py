"""
Memory module for S.H.I.E.L.D.

Handles persistent storage, vector database, and context management.
"""

from shield.memory.memory_manager import MemoryManager, get_memory, initialize_memory
from shield.memory.vector_store import VectorStore, get_vector_store, initialize_vector_store

__all__ = [
    "MemoryManager",
    "get_memory",
    "initialize_memory",
    "VectorStore",
    "get_vector_store",
    "initialize_vector_store",
]
