"""
Rate limiter implementation to control API requests per minute
"""
import time
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ..logging import AgentLogger

class RateLimiter:
    """Rate limiter using sliding window with enhanced logging"""
    
    def __init__(self, rpm: int, logger: Optional[AgentLogger] = None):
        """
        Initialize rate limiter
        
        Args:
            rpm: Maximum requests per minute
            logger: Optional logger for debugging
        """
        self.rpm = rpm
        self.requests: List[float] = []
        self.lock = asyncio.Lock()
        self.logger = logger
        
        if logger:
            logger.debug(
                "Initialized rate limiter",
                context={
                    "rpm_limit": rpm,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
    def _get_metrics(self) -> Dict[str, Any]:
        """Get current rate limiter metrics"""
        now = time.time()
        window_start = now - 60
        
        metrics = {
            "current_rpm": self.get_current_rpm(),
            "wait_time": self.get_wait_time(),
            "queue_size": len(self.requests),
            "window_start": datetime.fromtimestamp(window_start).isoformat(),
            "window_end": datetime.fromtimestamp(now).isoformat(),
            "requests_in_window": sum(1 for ts in self.requests if ts > window_start)
        }
        
        return metrics
        
    async def acquire(self) -> None:
        """
        Acquire permission to make a request. 
        Blocks until a request slot is available.
        """
        if self.logger:
            self.logger.debug(
                "Attempting to acquire rate limit slot",
                context=self._get_metrics()
            )
            
        async with self.lock:
            now = time.time()
            window_start = now - 60  # 1 minute window
            
            # Remove requests older than the window
            expired = 0
            while self.requests and self.requests[0] <= window_start:
                self.requests.pop(0)
                expired += 1
                
            if expired > 0 and self.logger:
                self.logger.debug(
                    f"Removed {expired} expired request(s) from window",
                    context={"expired_count": expired}
                )
                
            # If at rate limit, wait until oldest request expires
            if len(self.requests) >= self.rpm:
                wait_time = self.requests[0] - window_start
                if self.logger:
                    self.logger.debug(
                        f"Rate limit reached, waiting {wait_time:.2f} seconds",
                        context={
                            "wait_time": wait_time,
                            **self._get_metrics()
                        }
                    )
                await asyncio.sleep(wait_time)
                # Recursive call to recheck after waiting
                await self.acquire()
            else:
                # Add current request timestamp
                self.requests.append(now)
                if self.logger:
                    self.logger.debug(
                        "Rate limit slot acquired",
                        context=self._get_metrics()
                    )

    def get_current_rpm(self) -> int:
        """Get current requests per minute"""
        now = time.time()
        window_start = now - 60
        return sum(1 for ts in self.requests if ts > window_start)

    def get_wait_time(self) -> float:
        """Get time until next request slot is available"""
        if len(self.requests) < self.rpm:
            return 0
        
        now = time.time()
        window_start = now - 60
        return max(0, self.requests[0] - window_start)
