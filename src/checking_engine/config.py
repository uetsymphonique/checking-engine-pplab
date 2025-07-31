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
    
    # RabbitMQ - host/port/vhost/management
    rabbitmq_host: str = Field(default="localhost", env="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, env="RABBITMQ_PORT")
    rabbitmq_vhost: str = Field(default="/caldera_checking", env="RABBITMQ_VHOST")
    rabbitmq_management_port: int = Field(default=15672, env="RABBITMQ_MANAGEMENT_PORT")

    # RabbitMQ - user/pass cho từng role
    rabbitmq_admin_user: str = Field(default="caldera_admin", env="RABBITMQ_ADMIN_USER")
    rabbitmq_admin_pass: str = Field(default="", env="RABBITMQ_ADMIN_PASS")
    rabbitmq_publisher_user: str = Field(default="caldera_publisher", env="RABBITMQ_PUBLISHER_USER")
    rabbitmq_publisher_pass: str = Field(default="", env="RABBITMQ_PUBLISHER_PASS")
    rabbitmq_consumer_user: str = Field(default="checking_consumer", env="RABBITMQ_CONSUMER_USER")
    rabbitmq_consumer_pass: str = Field(default="", env="RABBITMQ_CONSUMER_PASS")
    rabbitmq_worker_user: str = Field(default="checking_worker", env="RABBITMQ_WORKER_USER")
    rabbitmq_worker_pass: str = Field(default="", env="RABBITMQ_WORKER_PASS")
    rabbitmq_dispatcher_user: str = Field(default="checking_dispatcher", env="RABBITMQ_DISPATCHER_USER")
    rabbitmq_dispatcher_pass: str = Field(default="", env="RABBITMQ_DISPATCHER_PASS")
    rabbitmq_result_consumer_user: str = Field(default="checking_result_consumer", env="RABBITMQ_RESULT_CONSUMER_USER")
    rabbitmq_result_consumer_pass: str = Field(default="", env="RABBITMQ_RESULT_CONSUMER_PASS")
    rabbitmq_monitor_user: str = Field(default="monitor_user", env="RABBITMQ_MONITOR_USER")
    rabbitmq_monitor_pass: str = Field(default="", env="RABBITMQ_MONITOR_PASS")

    # Exchange, queue, routing key
    rabbitmq_exchange: str = Field(default="caldera.checking.exchange", env="RABBITMQ_EXCHANGE")
    rabbitmq_instructions_queue: str = Field(default="caldera.checking.instructions", env="RABBITMQ_INSTRUCTIONS_QUEUE")
    rabbitmq_api_tasks_queue: str = Field(default="caldera.checking.api.tasks", env="RABBITMQ_API_TASKS_QUEUE")
    rabbitmq_agent_tasks_queue: str = Field(default="caldera.checking.agent.tasks", env="RABBITMQ_AGENT_TASKS_QUEUE")
    rabbitmq_api_responses_queue: str = Field(default="caldera.checking.api.responses", env="RABBITMQ_API_RESPONSES_QUEUE")
    rabbitmq_agent_responses_queue: str = Field(default="caldera.checking.agent.responses", env="RABBITMQ_AGENT_RESPONSES_QUEUE")

    routing_key_execution_result: str = Field(default="caldera.execution.result", env="ROUTING_KEY_EXECUTION_RESULT")
    routing_key_api_task: str = Field(default="checking.api.task", env="ROUTING_KEY_API_TASK")
    routing_key_agent_task: str = Field(default="checking.agent.task", env="ROUTING_KEY_AGENT_TASK")
    routing_key_api_response: str = Field(default="checking.api.response", env="ROUTING_KEY_API_RESPONSE")
    routing_key_agent_response: str = Field(default="checking.agent.response", env="ROUTING_KEY_AGENT_RESPONSE")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_json_format: bool = Field(default=False, env="LOG_JSON_FORMAT")
    log_console_output: bool = Field(default=True, env="LOG_CONSOLE_OUTPUT")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields from .env
    }

# Global settings instance
settings = Settings()
print(f"log_level: {settings.log_level}") 