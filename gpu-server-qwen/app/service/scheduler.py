"""
GPU scheduler for managing busy state and job queue.
Thread-safe state management.
"""
import threading
from typing import Optional
from app.service.logger import log_event
import logging

logger = logging.getLogger(__name__)


class GPUScheduler:
    """Manages GPU busy state and current job tracking."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._busy = False
        self._current_job_id: Optional[str] = None
        self._queue_length = 0
    
    @property
    def busy(self) -> bool:
        """Check if GPU is busy."""
        with self._lock:
            return self._busy
    
    @property
    def current_job_id(self) -> Optional[str]:
        """Get current job ID."""
        with self._lock:
            return self._current_job_id
    
    @property
    def queue_length(self) -> int:
        """Get queue length."""
        with self._lock:
            return self._queue_length
    
    def can_accept_job(self) -> bool:
        """
        Check if GPU can accept a new job.
        
        Returns:
            True if GPU is free, False if busy
        """
        with self._lock:
            return not self._busy
    
    def accept_job(self, job_id: str) -> bool:
        """
        Accept a new job. Sets GPU to busy.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job accepted, False if GPU is busy
        """
        with self._lock:
            if self._busy:
                log_event(
                    logger,
                    "gpu_busy_rejected",
                    f"GPU busy, rejecting job {job_id}",
                    job_id=job_id
                )
                return False
            
            self._busy = True
            self._current_job_id = job_id
            self._queue_length += 1
            
            log_event(
                logger,
                "job_accepted",
                f"Job {job_id} accepted, GPU now busy",
                job_id=job_id
            )
            
            return True
    
    def complete_job(self, job_id: str) -> None:
        """
        Mark job as complete. Frees GPU.
        
        Args:
            job_id: Job identifier
        """
        with self._lock:
            if self._current_job_id == job_id:
                self._busy = False
                self._current_job_id = None
                if self._queue_length > 0:
                    self._queue_length -= 1
                
                log_event(
                    logger,
                    "job_completed",
                    f"Job {job_id} completed, GPU now free",
                    job_id=job_id
                )
            else:
                logger.warning(f"Completed job {job_id} but current job is {self._current_job_id}")
                if self._queue_length > 0:
                    self._queue_length -= 1
    
    def get_status(self) -> dict:
        """
        Get current GPU status.
        
        Returns:
            Dictionary with busy, current_job_id, queue_length
        """
        with self._lock:
            return {
                "busy": self._busy,
                "current_job_id": self._current_job_id,
                "queue_length": self._queue_length,
            }


# Global scheduler instance
_scheduler: Optional[GPUScheduler] = None


def get_scheduler() -> GPUScheduler:
    """Get global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = GPUScheduler()
    return _scheduler

