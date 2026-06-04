import random
import asyncio

class RateLimiter:
    def __init__(self, min_delay=3, max_delay=7):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.daily_count = 0
        self.max_daily = 20

    async def wait(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def wait_between_pages(self):
        
        delay = random.uniform(15, 30)
        await asyncio.sleep(delay)

    async def wait_between_sessions(self):
        
        delay = random.uniform(120, 300)
        await asyncio.sleep(delay)

    def is_daily_limit_reached(self):
        return self.daily_count >= self.max_daily

    def increment(self):
        self.daily_count += 1
