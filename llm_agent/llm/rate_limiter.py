"""
Rate limiter implementation to control API requests per minute
"""
import time
import asyncio
from datetime import datetime, timedelta
from typing import List

class RateLimiter:
    """Rate limiter using sliding window"""
    
    def __init__(self, rpm: int):
        """
        Initialize rate limiter
        
        Args:
            rpm: Maximum requests per minute
        """
        self.rpm = rpm
        self.requests: List[float] = []
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> None:
        """
        Acquire permission to make a request. 
        Blocks until a request slot is available.
        """
        async with self.lock:
            now = time.time()
            window_start = now - 60  # 1 minute window
            
            # Remove requests older than the window
            while self.requests and self.requests[0] <= window_start:
                self.requests.pop(0)
                
            # If at rate limit, wait until oldest request expires
            if len(self.requests) >= self.rpm:
                wait_time = self.requests[0] - window_start
                await asyncio.sleep(wait_time)
                # Recursive call to recheck after waiting
                await self.acquire()
            else:
                # Add current request timestamp
                self.requests.append(now)

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
