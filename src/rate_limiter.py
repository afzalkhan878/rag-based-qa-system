"""
Rate Limiter Module
Implements token bucket rate limiting for API requests
"""
import time
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints
    
    Prevents abuse and ensures fair usage
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}  # user_id -> list of timestamps
        
        logger.info(f"RateLimiter initialized: {max_requests} requests per {window_seconds} seconds")
    
    def allow_request(self, user_id: str) -> bool:
        """
        Check if request is allowed for user
        
        Args:
            user_id: Unique user identifier
        
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        current_time = time.time()
        
        # Initialize user if not exists
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Clean old requests outside window
        cutoff_time = current_time - self.window_seconds
        self.requests[user_id] = [
            timestamp for timestamp in self.requests[user_id]
            if timestamp > cutoff_time
        ]
        
        # Check if under limit
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(current_time)
            logger.debug(f"Request allowed for {user_id}. Count: {len(self.requests[user_id])}/{self.max_requests}")
            return True
        else:
            logger.warning(f"Rate limit exceeded for {user_id}")
            return False
    
    def get_remaining_requests(self, user_id: str) -> int:
        """
        Get remaining requests for user in current window
        
        Args:
            user_id: User identifier
        
        Returns:
            Number of remaining requests
        """
        if user_id not in self.requests:
            return self.max_requests
        
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        # Count recent requests
        recent_requests = sum(1 for ts in self.requests[user_id] if ts > cutoff_time)
        
        return max(0, self.max_requests - recent_requests)
    
    def reset_user(self, user_id: str):
        """Reset rate limit for a user"""
        if user_id in self.requests:
            del self.requests[user_id]
            logger.info(f"Rate limit reset for {user_id}")
