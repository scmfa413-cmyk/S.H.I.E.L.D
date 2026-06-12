"""
LLM handler for S.H.I.E.L.D.

Provides integration with local Ollama models and LangChain.
"""

from typing import Optional, Dict, Any, List
import httpx
import asyncio
from shield.core.config import Config
from shield.core.logger import get_logger
from shield.core.types import LLMError, LLMConnectionError, LLMGenerationError

logger = get_logger(__name__)


class OllamaHandler:
    """
    Handles communication with Ollama local LLM.
    
    Provides:
    - Model management
    - Text generation
    - Streaming support
    - Error handling and retries
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        Initialize Ollama handler.
        
        Args:
            base_url: Ollama server URL
            model: Model name to use
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = httpx.AsyncClient(timeout=60.0)
        
        logger.info(f"Ollama handler initialized: {model} at {base_url}")
    
    async def check_connection(self) -> bool:
        """
        Check if Ollama server is reachable.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {str(e)}")
            return False
    
    async def list_models(self) -> List[str]:
        """
        List available models on Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            system_prompt: System message for context
            temperature: Sampling temperature override
            max_tokens: Max tokens override
        
        Returns:
            Generated text
        
        Raises:
            LLMConnectionError: If cannot connect to Ollama
            LLMGenerationError: If generation fails
        """
        # Use provided values or defaults
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temp,
                "stream": False,
                "options": {
                    "num_predict": tokens,
                }
            }
            
            logger.debug(f"Sending request to Ollama: {self.model}")
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama returned status {response.status_code}"
                logger.error(error_msg)
                raise LLMGenerationError(error_msg)
            
            data = response.json()
            generated_text = data.get("message", {}).get("content", "")
            
            logger.debug(f"Generated {len(generated_text)} characters")
            return generated_text
        
        except httpx.ConnectError as e:
            error_msg = f"Cannot connect to Ollama at {self.base_url}: {str(e)}"
            logger.error(error_msg)
            raise LLMConnectionError(error_msg)
        except Exception as e:
            error_msg = f"LLM generation failed: {str(e)}"
            logger.error(error_msg)
            raise LLMGenerationError(error_msg)
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """
        Generate text with streaming.
        
        Args:
            prompt: Input prompt
            system_prompt: System message
            temperature: Temperature override
        
        Yields:
            Text chunks as they are generated
        """
        temp = temperature if temperature is not None else self.temperature
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temp,
                "stream": True,
            }
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status_code != 200:
                    raise LLMGenerationError(f"Status {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = httpx._content.parse_json(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except Exception as e:
                            logger.debug(f"Error parsing stream line: {str(e)}")
                            continue
        
        except Exception as e:
            logger.error(f"Streaming generation failed: {str(e)}")
            raise LLMGenerationError(str(e))
    
    async def close(self) -> None:
        """Close the client connection"""
        await self.client.aclose()


class LLMHandler:
    """
    Main LLM handler that abstracts provider specifics.
    
    Currently supports:
    - Ollama (local, open-source models)
    - Future: OpenAI, Anthropic, etc.
    """
    
    def __init__(self, config=None):
        """
        Initialize LLM handler.
        
        Args:
            config: ShieldConfig instance
        """
        if config is None:
            config = Config.get()
        
        self.config = config
        self.provider = config.llm.provider.lower()
        
        if self.provider == "ollama":
            self.handler = OllamaHandler(
                base_url=config.llm.base_url or "http://localhost:11434",
                model=config.llm.model,
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        logger.info(f"LLM handler initialized: {self.provider}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text"""
        return await self.handler.generate(prompt, system_prompt, **kwargs)
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Generate text with streaming"""
        return self.handler.generate_stream(prompt, system_prompt, **kwargs)
    
    async def check_connection(self) -> bool:
        """Check connection to LLM"""
        return await self.handler.check_connection()
    
    async def close(self) -> None:
        """Close LLM handler"""
        await self.handler.close()
