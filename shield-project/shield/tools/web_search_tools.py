"""
Web search tools for S.H.I.E.L.D.

Tools for searching the web and gathering information.
"""

import asyncio
from typing import List, Dict, Any, Optional
import httpx

from shield.tools.base import Tool, ToolParameter
from shield.core.types import ToolResult, ToolStatus, SearchResult
from shield.core.logger import get_logger

logger = get_logger(__name__)


class DuckDuckGoSearchTool(Tool):
    """Search using DuckDuckGo"""
    
    def __init__(self):
        super().__init__(
            name="search_duckduckgo",
            description="Search the web using DuckDuckGo",
            category="web",
        )
        
        self.register_parameters([
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type="integer",
                description="Maximum number of results",
                required=False,
                default=10
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute DuckDuckGo search"""
        try:
            from duckduckgo_search import DDGS
            
            query = kwargs.get("query")
            max_results = kwargs.get("max_results", 10)
            
            logger.info(f"Searching DuckDuckGo: {query}")
            
            # Search using duckduckgo_search
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "source": "duckduckgo",
                })
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "query": query,
                    "result_count": len(formatted_results),
                    "results": formatted_results,
                }
            )
        
        except ImportError:
            return ToolResult(
                status=ToolStatus.FAILED,
                error="duckduckgo_search not installed"
            )
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class TavilySearchTool(Tool):
    """Search using Tavily API"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="search_tavily",
            description="Search the web using Tavily API (research-optimized)",
            category="web",
        )
        
        self.api_key = api_key
        
        self.register_parameters([
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type="integer",
                description="Maximum number of results",
                required=False,
                default=5
            ),
            ToolParameter(
                name="include_answer",
                type="boolean",
                description="Include AI-generated answer",
                required=False,
                default=True
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute Tavily search"""
        try:
            from shield.core.config import Config
            
            if not self.api_key:
                config = Config.get()
                self.api_key = config.tools.tavily_api_key
            
            if not self.api_key:
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error="Tavily API key not configured"
                )
            
            query = kwargs.get("query")
            max_results = kwargs.get("max_results", 5)
            include_answer = kwargs.get("include_answer", True)
            
            logger.info(f"Searching Tavily: {query}")
            
            # Use Tavily API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "max_results": max_results,
                        "include_answer": include_answer,
                    },
                    timeout=30.0,
                )
            
            if response.status_code != 200:
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Tavily API error: {response.status_code}"
                )
            
            data = response.json()
            
            # Format results
            formatted_results = []
            for result in data.get("results", []):
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", ""),
                    "source": "tavily",
                })
            
            output = {
                "query": query,
                "result_count": len(formatted_results),
                "results": formatted_results,
            }
            
            if include_answer and "answer" in data:
                output["answer"] = data["answer"]
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=output
            )
        
        except Exception as e:
            logger.error(f"Tavily search failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


class FetchPageContentTool(Tool):
    """Fetch and extract content from a webpage"""
    
    def __init__(self):
        super().__init__(
            name="fetch_page_content",
            description="Fetch and extract main content from a webpage",
            category="web",
        )
        
        self.register_parameters([
            ToolParameter(
                name="url",
                type="string",
                description="URL to fetch",
                required=True
            ),
            ToolParameter(
                name="max_chars",
                type="integer",
                description="Maximum characters to return",
                required=False,
                default=5000
            ),
        ])
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute fetch page content"""
        try:
            url = kwargs.get("url")
            max_chars = kwargs.get("max_chars", 5000)
            
            logger.info(f"Fetching page: {url}")
            
            # Fetch content
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10.0,
                    follow_redirects=True,
                )
            
            if response.status_code != 200:
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"HTTP {response.status_code}"
                )
            
            # Extract text (simple method - could use html2text or readability)
            try:
                from html.parser import HTMLParser
                
                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.in_script = False
                    
                    def handle_starttag(self, tag, attrs):
                        if tag in ["script", "style"]:
                            self.in_script = True
                    
                    def handle_endtag(self, tag):
                        if tag in ["script", "style"]:
                            self.in_script = False
                        elif tag in ["p", "div", "h1", "h2", "h3"]:
                            self.text.append("\n")
                    
                    def handle_data(self, data):
                        if not self.in_script:
                            text = data.strip()
                            if text:
                                self.text.append(text)
                
                parser = TextExtractor()
                parser.feed(response.text)
                content = " ".join(parser.text)
                
            except Exception:
                # Fallback: just extract text from HTML
                import re
                content = re.sub(r"<[^>]+>", " ", response.text)
                content = re.sub(r"\s+", " ", content)
            
            # Limit to max_chars
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output={
                    "url": url,
                    "content": content,
                    "content_length": len(content),
                    "status_code": response.status_code,
                }
            )
        
        except Exception as e:
            logger.error(f"Fetch page failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )


# Export all tools
def register_web_search_tools(tavily_api_key: Optional[str] = None):
    """Register all web search tools with the global registry"""
    from shield.tools.base import get_tool_registry
    
    registry = get_tool_registry()
    
    tools = [
        DuckDuckGoSearchTool(),
        TavilySearchTool(tavily_api_key),
        FetchPageContentTool(),
    ]
    
    for tool in tools:
        registry.register(tool)
    
    logger.info(f"Registered {len(tools)} web search tools")
