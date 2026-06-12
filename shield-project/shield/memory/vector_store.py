"""
Vector store integration with ChromaDB for S.H.I.E.L.D.

Handles semantic search and embedding storage.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
import chromadb
from chromadb.config import Settings as ChromaSettings

from shield.core.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    Semantic memory using ChromaDB.
    
    Stores and searches embeddings for:
    - Conversation messages
    - Research findings
    - Code snippets
    - Project context
    """
    
    def __init__(self, persist_path: Path):
        """
        Initialize vector store.
        
        Args:
            persist_path: Path to ChromaDB storage
        """
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistence
        settings = ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(self.persist_path),
            anonymized_telemetry=False,
        )
        
        self.client = chromadb.Client(settings)
        
        # Initialize collections
        self.message_collection = self._get_or_create_collection("messages")
        self.artifact_collection = self._get_or_create_collection("artifacts")
        self.research_collection = self._get_or_create_collection("research")
        self.project_collection = self._get_or_create_collection("projects")
        
        logger.info(f"Vector store initialized at: {self.persist_path}")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a collection"""
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    # ========== MESSAGE EMBEDDINGS ==========
    
    def add_message_embedding(
        self,
        message_id: str,
        text: str,
        role: str = "user",
        conversation_id: str = None,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """
        Add message embedding.
        
        Args:
            message_id: Message ID
            text: Message text
            role: Message role
            conversation_id: Associated conversation
            metadata: Additional metadata
        """
        try:
            meta = metadata or {}
            meta["role"] = role
            if conversation_id:
                meta["conversation_id"] = conversation_id
            
            self.message_collection.add(
                ids=[message_id],
                documents=[text],
                metadatas=[meta],
            )
            
            logger.debug(f"Added message embedding: {message_id}")
        except Exception as e:
            logger.error(f"Failed to add message embedding: {str(e)}")
    
    def search_messages(
        self,
        query: str,
        n_results: int = 5,
        conversation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search message embeddings.
        
        Args:
            query: Search query
            n_results: Number of results
            conversation_id: Filter by conversation
        
        Returns:
            List of matching messages
        """
        try:
            where_filter = None
            if conversation_id:
                where_filter = {"conversation_id": conversation_id}
            
            results = self.message_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )
            
            matches = []
            for i, doc_id in enumerate(results["ids"][0]):
                if i < len(results["documents"][0]):
                    matches.append({
                        "id": doc_id,
                        "text": results["documents"][0][i],
                        "similarity": results["distances"][0][i],
                        "metadata": results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {},
                    })
            
            return matches
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    # ========== ARTIFACT EMBEDDINGS ==========
    
    def add_artifact_embedding(
        self,
        artifact_id: str,
        text: str,
        artifact_type: str = "document",
        project_id: str = None,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Add artifact embedding"""
        try:
            meta = metadata or {}
            meta["artifact_type"] = artifact_type
            if project_id:
                meta["project_id"] = project_id
            
            self.artifact_collection.add(
                ids=[artifact_id],
                documents=[text],
                metadatas=[meta],
            )
            
            logger.debug(f"Added artifact embedding: {artifact_id}")
        except Exception as e:
            logger.error(f"Failed to add artifact embedding: {str(e)}")
    
    def search_artifacts(
        self,
        query: str,
        n_results: int = 5,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search artifact embeddings"""
        try:
            where_filter = None
            if project_id:
                where_filter = {"project_id": project_id}
            
            results = self.artifact_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )
            
            matches = []
            for i, doc_id in enumerate(results["ids"][0]):
                if i < len(results["documents"][0]):
                    matches.append({
                        "id": doc_id,
                        "text": results["documents"][0][i][:200],  # Truncate for display
                        "similarity": results["distances"][0][i],
                        "metadata": results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {},
                    })
            
            return matches
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    # ========== RESEARCH EMBEDDINGS ==========
    
    def add_research_embedding(
        self,
        research_id: str,
        text: str,
        topic: str = None,
        url: str = None,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Add research finding embedding"""
        try:
            meta = metadata or {}
            if topic:
                meta["topic"] = topic
            if url:
                meta["url"] = url
            
            self.research_collection.add(
                ids=[research_id],
                documents=[text],
                metadatas=[meta],
            )
            
            logger.debug(f"Added research embedding: {research_id}")
        except Exception as e:
            logger.error(f"Failed to add research embedding: {str(e)}")
    
    def search_research(
        self,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search research findings"""
        try:
            results = self.research_collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            
            matches = []
            for i, doc_id in enumerate(results["ids"][0]):
                if i < len(results["documents"][0]):
                    matches.append({
                        "id": doc_id,
                        "text": results["documents"][0][i][:300],
                        "similarity": results["distances"][0][i],
                        "metadata": results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {},
                    })
            
            return matches
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    # ========== PROJECT CONTEXT ==========
    
    def add_project_context(
        self,
        project_id: str,
        context_text: str,
        context_type: str = "general",
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Add project context embedding"""
        doc_id = f"{project_id}_{context_type}_{uuid4()}"
        
        try:
            meta = metadata or {}
            meta["project_id"] = project_id
            meta["context_type"] = context_type
            
            self.project_collection.add(
                ids=[doc_id],
                documents=[context_text],
                metadatas=[meta],
            )
            
            logger.debug(f"Added project context: {project_id}")
        except Exception as e:
            logger.error(f"Failed to add project context: {str(e)}")
    
    def get_project_context(
        self,
        project_id: str,
        query: str = None,
        n_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get project context (all or search)"""
        try:
            if query:
                # Search within project
                results = self.project_collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where={"project_id": project_id},
                )
            else:
                # Get all project context
                results = self.project_collection.get(
                    where={"project_id": project_id},
                )
            
            matches = []
            for i, doc_id in enumerate(results.get("ids", [])):
                if i < len(results.get("documents", [])):
                    matches.append({
                        "id": doc_id,
                        "text": results["documents"][i],
                        "metadata": results["metadatas"][i] if i < len(results["metadatas"]) else {},
                    })
            
            return matches
        except Exception as e:
            logger.error(f"Failed to get project context: {str(e)}")
            return []
    
    # ========== GENERAL OPERATIONS ==========
    
    def global_search(
        self,
        query: str,
        n_results: int = 20,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all collections.
        
        Args:
            query: Search query
            n_results: Results per collection
        
        Returns:
            Results organized by collection
        """
        return {
            "messages": self.search_messages(query, n_results),
            "artifacts": self.search_artifacts(query, n_results),
            "research": self.search_research(query, n_results),
        }
    
    def delete_project_embeddings(self, project_id: str) -> bool:
        """Delete all embeddings for a project"""
        try:
            self.artifact_collection.delete(where={"project_id": project_id})
            self.project_collection.delete(where={"project_id": project_id})
            logger.info(f"Deleted embeddings for project: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project embeddings: {str(e)}")
            return False
    
    def persist(self) -> None:
        """Persist vector store to disk"""
        try:
            self.client.persist()
            logger.info("Vector store persisted")
        except Exception as e:
            logger.error(f"Failed to persist vector store: {str(e)}")


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def initialize_vector_store(persist_path: Path = None) -> VectorStore:
    """Initialize the global vector store"""
    global _vector_store
    
    if persist_path is None:
        from shield.core.config import Config
        config = Config.get()
        persist_path = config.memory.vector_db_path
    
    _vector_store = VectorStore(Path(persist_path))
    return _vector_store


def get_vector_store() -> VectorStore:
    """Get the global vector store"""
    global _vector_store
    if _vector_store is None:
        _vector_store = initialize_vector_store()
    return _vector_store
