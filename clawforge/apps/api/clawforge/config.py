"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Anthropic (Claude)
    anthropic_api_key: str = ""
    claude_model_routing: str = "claude-3-5-haiku-latest"  # For routing/simple tasks
    claude_model_coding: str = "claude-sonnet-4-20250514"  # For code generation (default)
    # Options: "claude-sonnet-4-20250514" (~$0.28/app) or "claude-opus-4-5-20251101" (~$1.40/app)
    use_opus_for_coding: bool = False  # Set True to use Opus (5x cost, marginally better)

    # Ollama (Local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"  # 7B is safer for most machines
    use_local_llm: bool = True  # Use Ollama for routing when available

    # GitHub
    github_token: str = ""
    github_default_org: str = ""  # Optional: default organization for repos
    github_webhook_secret: str = ""  # For webhook signature verification

    # Database (Legacy - replaced by Supabase)
    database_url: str = "sqlite+aiosqlite:///./clawforge.db"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""  # For server-side operations

    # ChromaDB (RAG)
    chroma_persist_dir: str = "./chroma_db"

    # Cost Tracking
    max_cost_per_workflow: float = 5.0  # Maximum $ per workflow run


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
