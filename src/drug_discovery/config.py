"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the drug discovery platform.

    All values must be supplied via environment variables or a .env file.
    See .env.example for required variables.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # PostgreSQL
    postgres_url: str = "postgresql+asyncpg://localhost:5432/drug_discovery"

    # MongoDB
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "drug_discovery"

    # Neo4j
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # Ingestion
    ncbi_api_key: str = ""
    pubmed_max_results: int = 50

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    models_cache_dir: str = "models_cache"


settings = Settings()
