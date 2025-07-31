import aio_pika
import logging
from typing import Optional
from checking_engine.config import settings

logger = logging.getLogger("checking_engine.mq.connection")

ROLE_USER_PASS = {
    "admin": (settings.rabbitmq_admin_user, settings.rabbitmq_admin_pass),
    "publisher": (settings.rabbitmq_publisher_user, settings.rabbitmq_publisher_pass),
    "consumer": (settings.rabbitmq_consumer_user, settings.rabbitmq_consumer_pass),
    "worker": (settings.rabbitmq_worker_user, settings.rabbitmq_worker_pass),
    "dispatcher": (settings.rabbitmq_dispatcher_user, settings.rabbitmq_dispatcher_pass),
    "result_consumer": (settings.rabbitmq_result_consumer_user, settings.rabbitmq_result_consumer_pass),
    "monitor": (settings.rabbitmq_monitor_user, settings.rabbitmq_monitor_pass),
}

async def get_rabbitmq_connection(role: str, *, timeout: float = 5.0, heartbeat: int = 600, blocked_connection_timeout: int = 300) -> aio_pika.RobustConnection:
    """
    Get a robust RabbitMQ connection for a given role.
    role: one of [admin, publisher, consumer, worker, dispatcher, result_consumer, monitor]
    """
    if role not in ROLE_USER_PASS:
        raise ValueError(f"Unknown RabbitMQ role: {role}")
    username, password = ROLE_USER_PASS[role]
    if not username or not password:
        raise ValueError(f"RabbitMQ credentials not set for role: {role}")
    logger.info(f"Connecting to RabbitMQ as user '{username}' (role={role}) vhost='{settings.rabbitmq_vhost}' host={settings.rabbitmq_host}:{settings.rabbitmq_port}")
    conn = await aio_pika.connect_robust(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        login=username,
        password=password,
        virtualhost=settings.rabbitmq_vhost,
        timeout=timeout,
        heartbeat=heartbeat,
        blocked_connection_timeout=blocked_connection_timeout,
    )
    return conn

async def test_connect_all_roles():
    """
    Test connection for all defined RabbitMQ roles. Log result for each.
    """
    import asyncio
    for role in ROLE_USER_PASS:
        try:
            logger.info(f"[TEST] Connecting as role: {role}")
            conn = await get_rabbitmq_connection(role)
            await conn.close()
            logger.info(f"[TEST] Connection successful for role: {role}")
        except Exception as e:
            logger.error(f"[TEST] Connection FAILED for role: {role} - {e}")
    logger.info("[TEST] All role connection tests complete.")

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_connect_all_roles())