"""
Configuration constants for AI Personalities
"""

import os

# Default paths and names
DEFAULT_DB_PATH = "./chroma_db"
DEFAULT_COLLECTION_NAME = "personality"
DEFAULT_CHARACTER_NAME = "unknown"
DEFAULT_SERVER_NAME = "ai-personalities"

# Environment variable keys
ENV_CHUNKS_DIR = "CHUNKS_DIR"
ENV_DB_PATH = "CHROMA_DB_PATH"
ENV_COLLECTION_NAME = "COLLECTION_NAME"
ENV_CHARACTER_NAME = "CHARACTER_NAME"
ENV_SERVER_NAME = "SERVER_NAME"


def get_db_path() -> str:
    """Get database path from environment or default"""
    return os.environ.get(ENV_DB_PATH, DEFAULT_DB_PATH)


def get_collection_name() -> str:
    """Get collection name from environment or default"""
    return os.environ.get(ENV_COLLECTION_NAME, DEFAULT_COLLECTION_NAME)


def get_character_name() -> str:
    """Get character name from environment or default"""
    return os.environ.get(ENV_CHARACTER_NAME, DEFAULT_CHARACTER_NAME)


def get_chunks_dir() -> str | None:
    """Get chunks directory from environment"""
    return os.environ.get(ENV_CHUNKS_DIR)


def get_server_name() -> str:
    """Get server name from environment or default"""
    return os.environ.get(ENV_SERVER_NAME, DEFAULT_SERVER_NAME)
