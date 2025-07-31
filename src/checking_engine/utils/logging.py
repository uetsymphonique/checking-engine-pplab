import logging
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
import sys
from pathlib import Path

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Get correlation ID from context
        cid = correlation_id.get()
        
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": cid,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            record.levelname = colored_levelname
        
        # Format the message
        formatted = super().format(record)
        
        # Add correlation ID if present
        cid = correlation_id.get()
        if cid:
            formatted += f" [CID: {cid}]"
        
        return formatted

class CorrelationFilter(logging.Filter):
    """Filter to add correlation ID to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        cid = correlation_id.get()
        if cid:
            record.correlation_id = cid
        return True

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,  # Default to simple format
    console_output: bool = True
) -> None:
    """
    Setup logging configuration for the checking engine
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        json_format: Whether to use JSON structured logging
        console_output: Whether to output to console
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(CorrelationFilter())
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(CorrelationFilter())
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name (usually module name)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def set_correlation_id(cid: Optional[str] = None) -> str:
    """
    Set correlation ID for request tracing
    
    Args:
        cid: Optional correlation ID, generates new one if not provided
    
    Returns:
        The correlation ID that was set
    """
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid

def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return correlation_id.get()

def clear_correlation_id() -> None:
    """Clear current correlation ID"""
    correlation_id.set(None)

def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    extra_fields: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log message with additional context fields
    
    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        extra_fields: Additional fields to include in log
        **kwargs: Additional keyword arguments
    """
    log_method = getattr(logger, level.lower())
    
    # Create log record with extra fields
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        message,
        (),
        None
    )
    
    # Add extra fields
    if extra_fields:
        record.extra_fields = extra_fields
    if kwargs:
        if not hasattr(record, 'extra_fields'):
            record.extra_fields = {}
        record.extra_fields.update(kwargs)
    
    logger.handle(record)

# Note: Removed convenience functions to avoid hard-coded log levels
# Use logger.debug(), logger.info(), etc. directly with proper log levels

# Context manager for correlation ID
class CorrelationContext:
    """Context manager for correlation ID"""
    
    def __init__(self, cid: Optional[str] = None):
        self.cid = cid
        self.previous_cid = None
    
    def __enter__(self):
        self.previous_cid = get_correlation_id()
        set_correlation_id(self.cid)
        return self.cid
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_cid:
            set_correlation_id(self.previous_cid)
        else:
            clear_correlation_id()

# Note: Logging is now initialized in main.py with config settings
# setup_logging() 