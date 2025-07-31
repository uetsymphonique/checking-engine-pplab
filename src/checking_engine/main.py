from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from checking_engine.config import settings
from checking_engine.database.connection import db
from checking_engine.api.v1.router import router as v1_router
from checking_engine.mq.consumers import CalderaExecutionConsumer
from checking_engine.utils.logging import get_logger, setup_logging

# Initialize logging with config settings
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    json_format=settings.log_json_format,
    console_output=settings.log_console_output
)

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Checking Engine application")
    
    # Initialize database
    await db.initialize()
    logger.info("Database initialized")
    
    # Initialize RabbitMQ consumer
    consumer = CalderaExecutionConsumer()
    try:
        await consumer.start_consuming()
        logger.info("RabbitMQ consumer started successfully")
        
        # Store consumer in app state for shutdown
        app.state.consumer = consumer
        
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}")
        # Don't fail app startup if RabbitMQ is down
        app.state.consumer = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Checking Engine application")
    
    # Stop consumer
    if hasattr(app.state, 'consumer') and app.state.consumer:
        try:
            await app.state.consumer.stop_consuming()
            logger.info("RabbitMQ consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping consumer: {e}")
    
    # Close database
    await db.close()
    logger.info("Database connection closed")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(v1_router, prefix="/api/v1") 