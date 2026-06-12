"""
Research Agent for S.H.I.E.L.D.

Autonomous agent for conducting research, analyzing sources, and generating insights.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from shield.agents.base import Agent
from shield.core.logger import get_logger
from shield.tools.base import get_tool_registry
from shield.memory import get_memory, get_vector_store

logger = get_logger(__name__)


class ResearchAgent(Agent):
    """
    Autonomous research agent.
    
    Capabilities:
    - Multi-source web search
    - Content fetching and analysis
    - Finding deduplication
    - Contradiction detection
    - Pattern identification
    - Insight generation
    """
    
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            role="Research Specialist",
            description="Conducts comprehensive research on topics using web sources",
        )
        self.registry = get_tool_registry()
        self.memory = get_memory()
        self.vector_store = get_vector_store()
    
    async def execute_research(
        self,
        query: str,
        project_id: Optional[str] = None,
        max_sources: int = 10,
        depth: str = "comprehensive",
    ) -> Dict[str, Any]:
        """
        Execute research on a topic.
        
        Args:
            query: Research query
            project_id: Associated project
            max_sources: Maximum sources to analyze
            depth: Research depth (quick, standard, comprehensive)
        
        Returns:
            Research results with findings
        """
        logger.info(f"Starting research: {query}")
        
        # Create conversation for this research
        conv_id = self.memory.create_conversation(
            title=f"Research: {query}",
            description=f"Research findings for: {query}",
            project_id=project_id,
        )
        
        # Phase 1: Search
        logger.info("Phase 1: Searching sources...")
        search_results = await self._search_sources(query, max_sources)
        
        # Add to memory
        self.memory.add_message(
            conv_id,
            "agent",
            f"Found {len(search_results)} sources",
            message_type="text",
            metadata={"phase": "search"},
        )
        
        # Phase 2: Fetch content
        logger.info("Phase 2: Fetching content from top sources...")
        fetched_content = await self._fetch_content(search_results[:5])
        
        self.memory.add_message(
            conv_id,
            "agent",
            f"Fetched {len(fetched_content)} sources",
            message_type="text",
            metadata={"phase": "fetch"},
        )
        
        # Phase 3: Store in database
        logger.info("Phase 3: Storing research...")
        topic_id = self.memory.create_research_topic(
            project_id or conv_id,
            title=query,
            query=query,
        )
        
        for i, result in enumerate(search_results):
            self.memory.add_source(
                topic_id,
                url=result.get("url", ""),
                title=result.get("title", ""),
                snippet=result.get("snippet", ""),
                relevance_score=1.0 - (i * 0.05),  # Descending score
            )
        
        # Phase 4: Analyze findings
        logger.info("Phase 4: Analyzing findings...")
        analysis = await self._analyze_findings(
            search_results,
            fetched_content,
        )
        
        self.memory.add_message(
            conv_id,
            "agent",
            json.dumps(analysis, indent=2),
            message_type="text",
            metadata={"phase": "analysis"},
        )
        
        # Phase 5: Create embeddings for semantic search
        logger.info("Phase 5: Creating embeddings...")
        for result in search_results:
            self.vector_store.add_research_embedding(
                research_id=f"research_{topic_id}_{result.get('url', '').split('/')[-1]}",
                text=f"{result.get('title', '')}: {result.get('snippet', '')}",
                topic=query,
                url=result.get("url", ""),
            )
        
        # Return comprehensive results
        return {
            "query": query,
            "conversation_id": conv_id,
            "topic_id": topic_id,
            "sources_found": len(search_results),
            "sources_fetched": len(fetched_content),
            "analysis": analysis,
            "sources": search_results,
        }
    
    async def _search_sources(
        self,
        query: str,
        max_sources: int,
    ) -> List[Dict[str, Any]]:
        """Search for sources using multiple engines"""
        results = []
        
        try:
            # Try DuckDuckGo
            search_tool = self.registry.get_tool("search_duckduckgo")
            if search_tool:
                result = await search_tool.execute(query=query, max_results=max_sources // 2)
                if result.output:
                    results.extend(result.output.get("results", []))
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {str(e)}")
        
        try:
            # Try Tavily
            search_tool = self.registry.get_tool("search_tavily")
            if search_tool:
                result = await search_tool.execute(query=query, max_results=max_sources // 2)
                if result.output:
                    results.extend(result.output.get("results", []))
        except Exception as e:
            logger.warning(f"Tavily search failed: {str(e)}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in results:
            url = result.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results[:max_sources]
    
    async def _fetch_content(
        self,
        sources: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        """Fetch content from sources"""
        content = {}
        fetch_tool = self.registry.get_tool("fetch_page_content")
        
        if not fetch_tool:
            logger.warning("fetch_page_content tool not available")
            return content
        
        for source in sources:
            try:
                url = source.get("url", "")
                result = await fetch_tool.execute(url=url, max_chars=5000)
                
                if result.status.value == "success":
                    content[url] = result.output.get("content", "")
            
            except Exception as e:
                logger.warning(f"Failed to fetch {source.get('url')}: {str(e)}")
        
        return content
    
    async def _analyze_findings(
        self,
        sources: List[Dict[str, Any]],
        content: Dict[str, str],
    ) -> Dict[str, Any]:
        """Analyze findings for patterns and insights"""
        
        # Extract key themes
        all_text = "\n".join(
            [s.get("snippet", "") for s in sources] + list(content.values())
        )
        
        # Count common words (simple analysis)
        words = all_text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Skip small words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "sources_analyzed": len(sources),
            "content_fetched": len(content),
            "total_size_kb": sum(len(c) for c in content.values()) / 1024,
            "top_themes": [word for word, count in top_words],
            "unique_sources": len(set(s.get("url") for s in sources)),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Convenience factory
_research_agent_instance: Optional[ResearchAgent] = None


def get_research_agent() -> ResearchAgent:
    """Get or create research agent"""
    global _research_agent_instance
    if _research_agent_instance is None:
        _research_agent_instance = ResearchAgent()
    return _research_agent_instance
