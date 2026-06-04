import logging
import functools

logger = logging.getLogger(__name__)

def safe_run(func):
    """Decorator untuk catch error tanpa crash sistem"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return {
                "error": str(e),
                "function": func.__name__
            }
    return wrapper
