import time
from typing import Dict, Tuple
from fastapi import HTTPException, status
from app.core.logging import logger

class InMemoryRateLimiter:
    def __init__(self):
        # Maps identifier -> (window_start_time, request_count)
        self.clients: Dict[str, Tuple[float, int]] = {}

    def check_rate_limit(self, identifier: str, limit_per_minute: int = 60):
        now = time.time()
        if identifier not in self.clients:
            self.clients[identifier] = (now, 1)
            return True

        start_time, count = self.clients[identifier]
        if now - start_time < 60:
            if count >= limit_per_minute:
                logger.warning(f"Rate limit exceeded for client: {identifier} ({count}/{limit_per_minute})")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {limit_per_minute} requests per minute allowed."
                )
            self.clients[identifier] = (start_time, count + 1)
        else:
            # Reset window
            self.clients[identifier] = (now, 1)
        return True

rate_limiter = InMemoryRateLimiter()
