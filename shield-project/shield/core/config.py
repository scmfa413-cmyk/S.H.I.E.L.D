"""
Configuration management for S.H.I.E.L.D.

Handles loading, validation, and management of application settings.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
import yaml
import json
from dotenv import load_dotenv


class CoreConfig(BaseModel):
    """Core configuration settings"""
    log_level: str = "INFO"
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".shield" / "data")
    max_context_length: int = 4000
    debug: bool = False
    version: str = "0.1.0"

    class Config:
        use_enum_values = True


class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: str = "ollama"  # ollama, openai, anthropic
    model: str = "mistral"
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: int = 2000
    base_url: Optional[str] = "http://localhost:11434"
    api_key: Optional[str] = None

    @field_validator("temperature")
    def validate_temperature(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v


class MemoryConfig(BaseModel):
    """Memory and database configuration"""
    vector_db_path: Path = Field(default_factory=lambda: Path.home() / ".shield" / "data" / "chroma")
    sqlite_db_path: Path = Field(default_factory=lambda: Path.home() / ".shield" / "data" / "shield.db")
    retention_days: int = 365
    max_conversations: int = 1000
    embedding_model: str = "all-MiniLM-L6-v2"


class ToolsConfig(BaseModel):
    """Tools configuration"""
    web_search_provider: str = "duckduckgo"  # duckduckgo, tavily, brave
    tavily_api_key: Optional[str] = None
    code_execution_sandbox: bool = True
    code_execution_timeout: int = 30
    enable_browser: bool = True
    browser_headless: bool = True


class SecurityConfig(BaseModel):
    """Security configuration"""
    encrypt_sensitive: bool = True
    audit_log: bool = True
    api_key_encryption: bool = True
    sandbox_code_execution: bool = True
    max_file_size_mb: int = 500


class AgentConfig(BaseModel):
    """Agent configuration"""
    num_workers: int = 4
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 5


class PluginConfig(BaseModel):
    """Plugin configuration"""
    enabled: bool = True
    plugin_path: Path = Field(default_factory=lambda: Path.home() / ".shield" / "plugins")
    auto_load: bool = True
    enabled_plugins: list = Field(default_factory=list)


class ShieldConfig(BaseSettings):
    """
    Main configuration class for S.H.I.E.L.D.
    
    Combines all subsystem configurations and provides centralized management.
    """
    
    core: CoreConfig = Field(default_factory=CoreConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)

    class Config:
        case_sensitive = False
        env_nested_delimiter = "__"
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **data):
        """Initialize configuration with environment variables and files"""
        # Load .env file
        load_dotenv()
        
        # Override with environment variables
        for key, value in os.environ.items():
            if key.startswith("SHIELD_"):
                data[key.lower()] = value
        
        super().__init__(**data)

    @staticmethod
    def from_yaml(config_path: Path) -> "ShieldConfig":
        """Load configuration from YAML file"""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)
        
        return ShieldConfig(**config_dict)

    @staticmethod
    def from_json(config_path: Path) -> "ShieldConfig":
        """Load configuration from JSON file"""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, "r") as f:
            config_dict = json.load(f)
        
        return ShieldConfig(**config_dict)

    def save_yaml(self, output_path: Path) -> None:
        """Save configuration to YAML file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)

    def save_json(self, output_path: Path) -> None:
        """Save configuration to JSON file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        self.core.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.plugins.plugin_path.mkdir(parents=True, exist_ok=True)


class Config:
    """
    Singleton configuration manager for S.H.I.E.L.D.
    
    Provides lazy loading and caching of configuration.
    """
    
    _instance: Optional[ShieldConfig] = None
    _config_path: Optional[Path] = None

    @classmethod
    def initialize(cls, config_path: Optional[Path] = None) -> ShieldConfig:
        """Initialize the configuration"""
        if cls._instance is not None:
            return cls._instance

        if config_path is None:
            cls._instance = ShieldConfig()
        elif config_path.suffix == ".yaml":
            cls._instance = ShieldConfig.from_yaml(config_path)
        elif config_path.suffix == ".json":
            cls._instance = ShieldConfig.from_json(config_path)
        else:
            raise ValueError(f"Unsupported config file type: {config_path.suffix}")

        cls._instance.ensure_directories()
        cls._config_path = config_path
        return cls._instance

    @classmethod
    def get(cls) -> ShieldConfig:
        """Get the global configuration instance"""
        if cls._instance is None:
            cls.initialize()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the configuration (mainly for testing)"""
        cls._instance = None
        cls._config_path = None


# Default configuration template
DEFAULT_CONFIG = """
# S.H.I.E.L.D. Configuration File

core:
  log_level: INFO
  data_dir: ~/.shield/data
  max_context_length: 4000
  debug: false
  version: 0.1.0

llm:
  provider: ollama
  model: mistral
  temperature: 0.7
  max_tokens: 2000
  base_url: http://localhost:11434
  api_key: null

memory:
  vector_db_path: ~/.shield/data/chroma
  sqlite_db_path: ~/.shield/data/shield.db
  retention_days: 365
  max_conversations: 1000
  embedding_model: all-MiniLM-L6-v2

tools:
  web_search_provider: duckduckgo
  tavily_api_key: null
  code_execution_sandbox: true
  code_execution_timeout: 30
  enable_browser: true
  browser_headless: true

security:
  encrypt_sensitive: true
  audit_log: true
  api_key_encryption: true
  sandbox_code_execution: true
  max_file_size_mb: 500

agents:
  num_workers: 4
  timeout_seconds: 300
  max_retries: 3
  retry_delay_seconds: 5

plugins:
  enabled: true
  plugin_path: ~/.shield/plugins
  auto_load: true
  enabled_plugins: []
"""
