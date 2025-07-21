"""
Configuration settings for ScoutAI Enterprise system
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "scout_ai_afl")
    user: str = os.getenv("DB_USER", "scout_ai")
    password: str = os.getenv("DB_PASSWORD", "scout_ai_password")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, local
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    model: str = os.getenv("LLM_MODEL", "gpt-4")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))

@dataclass
class AuthConfig:
    """Authentication configuration"""
    secret_key: str = os.getenv("SECRET_KEY", "scout-ai-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
@dataclass
class Config:
    """Main configuration class"""
    database: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    auth: AuthConfig = AuthConfig()
    data_source_path: str = os.getenv("AFL_DATA_PATH", "data/afl_data_source")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
# Global config instance
config = Config()