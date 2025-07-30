import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://checking_user:checking_password@localhost:5432/checking_engine_db",
        env="DATABASE_URL"
    )
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_name: str = Field(default="checking_engine_db", env="DATABASE_NAME")
    database_user: str = Field(default="checking_user", env="DATABASE_USER")
    database_password: str = Field(default="checking_password", env="DATABASE_PASSWORD")
    
    # Application Configuration
    app_name: str = Field(default="Checking Engine", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=1337, env="PORT")
    
    # RabbitMQ Configuration (for later phases)
    rabbitmq_host: str = Field(default="localhost", env="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, env="RABBITMQ_PORT")
    rabbitmq_vhost: str = Field(default="/caldera_checking", env="RABBITMQ_VHOST")
    rabbitmq_username: str = Field(default="checking_consumer", env="RABBITMQ_USERNAME")
    rabbitmq_password: str = Field(default="your_password_here", env="RABBITMQ_PASSWORD")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields from .env
    }

# Global settings instance
settings = Settings() 