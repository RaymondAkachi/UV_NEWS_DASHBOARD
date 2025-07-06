import logging
import time
import os
from pathlib import Path
from typing import Optional, Callable, Any
from dotenv import load_dotenv
import redis
from redis.exceptions import ConnectionError, TimeoutError
from tenacity import retry, wait_exponential, stop_after_attempt, before_log, after_log, retry_if_exception_type
import json

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Environment Variable Loading ---
# BASE_DIR = Path(__file__).resolve().parent.parent
# dotenv_path = BASE_DIR / 'app' / '.env'

# if not dotenv_path.exists():
#     raise FileNotFoundError(f".env file not found at {dotenv_path}")

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL not set in .env file")

logger.info(f"REDIS_URL loaded: {REDIS_URL}")

# --- Circuit Breaker Class ---


class CircuitBreaker:
    def __init__(self, cooldown: int = 60):
        self.is_open = False
        self.last_failure_time = 0
        self.cooldown = cooldown

    def can_execute(self) -> bool:
        """Check if operations can proceed based on circuit breaker state."""
        if self.is_open and (time.time() - self.last_failure_time) < self.cooldown:
            logger.warning("Circuit breaker is open, skipping operation")
            return False
        return True

    def record_failure(self):
        """Mark the circuit breaker as open after a failure."""
        self.is_open = True
        self.last_failure_time = time.time()
        logger.error("Circuit breaker opened due to Redis failure")

    def record_success(self):
        """Mark the circuit breaker as closed after a successful operation."""
        if self.is_open:
            self.is_open = False
            logger.info("Circuit breaker closed after successful operation")

# --- Redis Client Wrapper ---


class RedisClient:
    RETRIABLE_EXCEPTIONS = (ConnectionError, TimeoutError)

    def __init__(self):
        self.redis_url = REDIS_URL
        self.client: Optional[redis.Redis] = None
        self.circuit_breaker = CircuitBreaker(cooldown=60)

    def initialize(self) -> None:
        """Initialize the Redis client with connection validation."""
        try:
            self.client = redis.Redis.from_url(
                self.redis_url, decode_responses=True)
            self.client.ping()
            logger.info("Successfully connected to Redis")
        except (ConnectionError, TimeoutError) as e:
            logger.critical(f"Failed to initialize Redis client: {e}")
            raise

    def ensure_client(self) -> None:
        """Ensure the Redis client is initialized and valid."""
        if self.client is None or not self._check_connection():
            logger.warning(
                "Redis client invalid or not initialized, reinitializing")
            self.initialize()

    def _check_connection(self) -> bool:
        """Check if the Redis connection is healthy."""
        try:
            return self.client.ping()
        except (ConnectionError, TimeoutError):
            return False

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RETRIABLE_EXCEPTIONS),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.WARNING),
        reraise=True
    )
    def execute_command(self, command_func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute a Redis command with retry logic."""
        self.ensure_client()
        try:
            result = command_func(*args, **kwargs)
            self.circuit_breaker.record_success()
            return result
        except self.RETRIABLE_EXCEPTIONS:
            self.circuit_breaker.record_failure()
            raise

    def set(self, key: str, value: str) -> bool:
        """Set a key-value pair in Redis."""
        if not self.circuit_breaker.can_execute():
            return False
        try:
            self.execute_command(self.client.set, key, value)
            logger.info(f"Set Redis key: {key}")
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to set Redis key '{key}': {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """Get a value from Redis by key."""
        if not self.circuit_breaker.can_execute():
            return None
        try:
            value = self.execute_command(self.client.get, key)
            logger.info(
                f"Retrieved Redis key '{key}'")
            return value
        except redis.RedisError as e:
            logger.error(f"Failed to get Redis key '{key}': {e}")
            data = {
                "line_graph": {},
                "pie_chart": {
                    "good": 0,
                    "okay": 0,
                    "bad": 0
                },
                "top_sources": []
            }
            return json.dumps(data)

    def close(self) -> None:
        """Close the Redis client connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("Redis client connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")
            self.client = None

# --- Test Redis Usage ---


def main_test():
    redis_client = RedisClient()
    try:
        redis_client.initialize()

        logger.info("--- Basic Set/Get Test ---")
        success = redis_client.set("mykey", "myvalue")
        logger.info(f"Set 'mykey': {'Success' if success else 'Failed'}")
        res = redis_client.get("mykey")
        logger.info(f"Retrieved 'mykey': {res}")

        logger.info("--- Circuit Breaker Test (initial state) ---")
        success = redis_client.set("breaker_key_1", "breaker_value_1")
        logger.info(
            f"Set 'breaker_key_1': {'Success' if success else 'Failed'}")
        res_breaker = redis_client.get("breaker_key_1")
        logger.info(f"Retrieved 'breaker_key_1': {res_breaker}")

        logger.info("--- Simulating Redis connection failure ---")
        try:
            redis_client.client.connection_pool.disconnect()
            redis_client.execute_command(
                redis_client.client.set, "error_test_key", "error_test_value")
        except redis.RedisError as e:
            logger.info(f"Test error handling caught: {e}")

        logger.info("--- Attempting command after simulated failure ---")
        success = redis_client.set("post_error_key", "post_error_value")
        logger.info(
            f"Set 'post_error_key': {'Success' if success else 'Failed'}")

        logger.info("--- Circuit Breaker Test (after potential failure) ---")
        success = redis_client.set("breaker_key_2", "breaker_value_2")
        logger.info(
            f"Set 'breaker_key_2': {'Success' if success else 'Failed'}")
        logger.info(
            f"Circuit breaker state: {'open' if redis_client.circuit_breaker.is_open else 'closed'}")

    except Exception as e:
        logger.critical(f"Test failed: {e}")
    finally:
        redis_client.close()


if __name__ == "__main__":
    main_test()
