# /tests/test_infrastructure/test_redis.py

import pytest
import json
from datetime import timedelta
from infrastructure.cache import redis_client, CacheKeys, cache, invalidate
import time

class TestRedisIntegration:
    def test_cache_decorator(self, redis_cleanup):
        @cache(key_pattern="test:{param}", ttl=1)
        def test_function(param):
            return {"value": param.upper()}
        
        # First call - should cache
        result1 = test_function("hello")
        assert result1 == {"value": "HELLO"}
        
        # Verify cache
        cache_key = "test:hello"
        assert redis_client.exists(cache_key)
        
        # Second call - should hit cache
        result2 = test_function("hello")
        assert result2 == result1
        
        # Wait for TTL expiration
        time.sleep(1.1)
        assert not redis_client.exists(cache_key)

    def test_batch_invalidation(self, redis_cleanup):
        # Set up test keys
        keys = [f"test:{i}" for i in range(5)]
        for key in keys:
            redis_client.set(key, "value")
        
        # Invalidate using pattern
        invalidate("test:*")
        
        # Verify all keys are gone
        for key in keys:
            assert not redis_client.exists(key)

    def test_hash_storage(self, redis_cleanup):
        test_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Test Object",
            "nested": {"key": "value"}
        }
        
        @cache(key_pattern="hash_test:{id}", ttl=10)
        def get_test_object(id):
            return test_data
        
        # Call function to cache
        result = get_test_object(test_data["id"])
        assert result == test_data
        
        # Verify hash structure in Redis
        cache_key = f"hash_test:{test_data['id']}"
        stored = redis_client.hgetall(cache_key)
        assert json.loads(stored["name"]) == "Test Object"
        assert json.loads(stored["nested"]) == {"key": "value"}