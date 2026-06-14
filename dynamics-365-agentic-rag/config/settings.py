from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    anthropic_model: str = "claude-opus-4-8"

    d365_tenant_id: str
    d365_client_id: str
    d365_client_secret: str
    d365_base_url: str  # e.g. https://myorg.crm.dynamics.com

    chroma_persist_directory: str = "./chroma_db"
    chroma_embedding_model: str = "all-MiniLM-L6-v2"

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000

    rag_top_k: int = 8
    rag_index_batch_size: int = 100


settings = Settings()
