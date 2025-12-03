"""
Structured JSON logging for GPU server.
All logs must be in JSON format with required fields.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from app.service.config import get_node_id, get_log_level


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "node_id": get_node_id(),
        }
        
        # Add event type if present
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        
        # Add job_id if present
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        
        # Add error details if exception
        if record.exc_info:
            log_data["error"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging() -> None:
    """Setup JSON logging for the application."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, get_log_level().upper(), logging.INFO))
    root_logger.addHandler(handler)
    
    # Prevent duplicate logs
    root_logger.propagate = False


def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    job_id: Optional[str] = None,
    **extra_fields
) -> None:
    """
    Log a structured event.
    
    Args:
        logger: Logger instance
        event_type: Event type (request_received, validation_passed, etc.)
        message: Log message
        job_id: Optional job ID
        **extra_fields: Additional fields to include
    """
    extra = {
        "event_type": event_type,
        "extra_fields": extra_fields,
    }
    if job_id:
        extra["job_id"] = job_id
    
    logger.info(message, extra=extra)

