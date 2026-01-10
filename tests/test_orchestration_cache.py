"""Tests for orchestration result caching."""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pydantic_deep.orchestration.cache import (
    CacheConfig,
    CacheKey,
    CacheStrategy,
    ResultCache,
)
from pydantic_deep.orchestration.models import TaskDefinition, TaskResult, TaskStatus


def test_cache_key_generation_basic():
    """Test basic cache key generation."""
    task = TaskDefinition(
        id="test-task",
        description="Test task",
        parameters={"param1": "value1"},
    )

    key1 = CacheKey.generate(task)
    key2 = CacheKey.generate(task)

    # Same task should generate same key
    assert key1 == key2
    assert len(key1) == 64  # SHA-256 hash


def test_cache_key_generation_different_params():
    """Test that different parameters generate different keys."""
    task1 = TaskDefinition(
        id="test-task",
        description="Test task",
        parameters={"param1": "value1"},
    )
    task2 = TaskDefinition(
        id="test-task",
        description="Test task",
        parameters={"param1": "value2"},
    )

    key1 = CacheKey.generate(task1)
    key2 = CacheKey.generate(task2)

    assert key1 != key2


def test_cache_key_generation_with_dependencies():
    """Test cache key includes dependency outputs."""
    task = TaskDefinition(
        id="task2",
        description="Depends on task1",
        depends_on=["task1"],
    )

    dep_result1 = TaskResult(
        task_id="task1",
        status=TaskStatus.COMPLETED,
        output="output1",
    )
    dep_result2 = TaskResult(
        task_id="task1",
        status=TaskStatus.COMPLETED,
        output="output2",
    )

    key1 = CacheKey.generate(task, {"task1": dep_result1}, True)
    key2 = CacheKey.generate(task, {"task1": dep_result2}, True)

    # Different dependency outputs should generate different keys
    assert key1 != key2


def test_cache_key_without_dependencies():
    """Test cache key without including dependencies."""
    task = TaskDefinition(
        id="task2",
        description="Depends on task1",
        depends_on=["task1"],
    )

    dep_result1 = TaskResult(
        task_id="task1",
        status=TaskStatus.COMPLETED,
        output="output1",
    )
    dep_result2 = TaskResult(
        task_id="task1",
        status=TaskStatus.COMPLETED,
        output="output2",
    )

    key1 = CacheKey.generate(task, {"task1": dep_result1}, False)
    key2 = CacheKey.generate(task, {"task1": dep_result2}, False)

    # Without dependencies, same key regardless of dependency outputs
    assert key1 == key2


def test_memory_cache_put_and_get():
    """Test basic put and get from memory cache."""
    config = CacheConfig(strategy=CacheStrategy.MEMORY)
    cache = ResultCache(config)

    task = TaskDefinition(id="test", description="Test task")
    result = TaskResult(
        task_id="test",
        status=TaskStatus.COMPLETED,
        output="test output",
    )

    # Put result in cache
    cache.put(task, result)

    # Get result from cache
    cached = cache.get(task)

    assert cached is not None
    assert cached.output == "test output"


def test_cache_miss():
    """Test cache miss returns None."""
    config = CacheConfig(strategy=CacheStrategy.MEMORY)
    cache = ResultCache(config)

    task = TaskDefinition(id="test", description="Test task")

    # Cache miss
    cached = cache.get(task)
    assert cached is None


def test_cache_disabled():
    """Test that cache is disabled with NONE strategy."""
    config = CacheConfig(strategy=CacheStrategy.NONE)
    cache = ResultCache(config)

    task = TaskDefinition(id="test", description="Test task")
    result = TaskResult(
        task_id="test",
        status=TaskStatus.COMPLETED,
        output="test output",
    )

    # Put and get should not work
    cache.put(task, result)
    cached = cache.get(task)

    assert cached is None


def test_cache_ttl_expiration():
    """Test that cache entries expire based on TTL."""
    config = CacheConfig(
        strategy=CacheStrategy.MEMORY,
        ttl_seconds=0.1,  # 100ms TTL
    )
    cache = ResultCache(config)

    task = TaskDefinition(id="test", description="Test task")
    result = TaskResult(
        task_id="test",
        status=TaskStatus.COMPLETED,
        output="test output",
    )

    # Put result in cache
    cache.put(task, result)

    # Should be in cache immediately
    cached = cache.get(task)
    assert cached is not None

    # Wait for TTL to expire
    import time

    time.sleep(0.15)

    # Should be expired
    cached = cache.get(task)
    assert cached is None


def test_cache_lru_eviction():
    """Test LRU eviction when cache is full."""
    config = CacheConfig(
        strategy=CacheStrategy.MEMORY,
        max_size=2,
    )
    cache = ResultCache(config)

    # Add 2 tasks (at capacity)
    for i in range(2):
        task = TaskDefinition(id=f"task{i}", description=f"Task {i}")
        result = TaskResult(
            task_id=f"task{i}",
            status=TaskStatus.COMPLETED,
            output=f"output {i}",
        )
        cache.put(task, result)

    # Access task0 to make it more recently used
    task0 = TaskDefinition(id="task0", description="Task 0")
    cache.get(task0)

    # Add task2, should evict task1 (LRU)
    task2 = TaskDefinition(id="task2", description="Task 2")
    result2 = TaskResult(
        task_id="task2",
        status=TaskStatus.COMPLETED,
        output="output 2",
    )
    cache.put(task2, result2)

    # task0 should still be in cache
    assert cache.get(task0) is not None

    # task1 should be evicted
    task1 = TaskDefinition(id="task1", description="Task 1")
    assert cache.get(task1) is None

    # task2 should be in cache
    assert cache.get(task2) is not None


def test_cache_invalidate():
    """Test cache invalidation."""
    config = CacheConfig(strategy=CacheStrategy.MEMORY)
    cache = ResultCache(config)

    task = TaskDefinition(id="test-task", description="Test task")
    result = TaskResult(
        task_id="test-task",
        status=TaskStatus.COMPLETED,
        output="test output",
    )

    cache.put(task, result)
    assert cache.get(task) is not None

    # Invalidate
    count = cache.invalidate("test-task")
    assert count > 0

    # Should be gone
    assert cache.get(task) is None


def test_cache_clear():
    """Test clearing all cache entries."""
    config = CacheConfig(strategy=CacheStrategy.MEMORY)
    cache = ResultCache(config)

    # Add multiple tasks
    for i in range(5):
        task = TaskDefinition(id=f"task{i}", description=f"Task {i}")
        result = TaskResult(
            task_id=f"task{i}",
            status=TaskStatus.COMPLETED,
            output=f"output {i}",
        )
        cache.put(task, result)

    # Clear cache
    cache.clear()

    # All should be gone
    for i in range(5):
        task = TaskDefinition(id=f"task{i}", description=f"Task {i}")
        assert cache.get(task) is None


def test_cache_stats():
    """Test cache statistics."""
    config = CacheConfig(strategy=CacheStrategy.MEMORY)
    cache = ResultCache(config)

    task = TaskDefinition(id="test", description="Test task")
    result = TaskResult(
        task_id="test",
        status=TaskStatus.COMPLETED,
        output="test output",
    )

    # Miss
    cache.get(task)

    # Put
    cache.put(task, result)

    # Hit
    cache.get(task)

    # Another miss
    task2 = TaskDefinition(id="test2", description="Test task 2")
    cache.get(task2)

    stats = cache.get_stats()

    assert stats["hits"] == 1
    assert stats["misses"] == 2
    assert stats["hit_rate"] == "33.3%"
    assert stats["cache_size"] == 1


def test_disk_cache_persistence():
    """Test disk cache persists across instances."""
    # Create temporary directory for cache
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        # First cache instance
        config1 = CacheConfig(
            strategy=CacheStrategy.DISK,
            cache_dir=cache_dir,
        )
        cache1 = ResultCache(config1)

        task = TaskDefinition(id="test", description="Test task")
        result = TaskResult(
            task_id="test",
            status=TaskStatus.COMPLETED,
            output="test output",
        )

        cache1.put(task, result)

        # Second cache instance (new ResultCache object)
        config2 = CacheConfig(
            strategy=CacheStrategy.DISK,
            cache_dir=cache_dir,
        )
        cache2 = ResultCache(config2)

        # Should be able to retrieve from disk
        cached = cache2.get(task)
        assert cached is not None
        assert cached.output == "test output"


def test_hybrid_cache():
    """Test hybrid cache (memory + disk)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        config = CacheConfig(
            strategy=CacheStrategy.HYBRID,
            cache_dir=cache_dir,
            max_size=1,  # Small memory cache
        )
        cache = ResultCache(config)

        # Add first task (in memory and disk)
        task1 = TaskDefinition(id="task1", description="Task 1")
        result1 = TaskResult(
            task_id="task1",
            status=TaskStatus.COMPLETED,
            output="output 1",
        )
        cache.put(task1, result1)

        # Add second task (should evict task1 from memory but keep on disk)
        task2 = TaskDefinition(id="task2", description="Task 2")
        result2 = TaskResult(
            task_id="task2",
            status=TaskStatus.COMPLETED,
            output="output 2",
        )
        cache.put(task2, result2)

        # task2 should be in memory
        assert cache._memory_cache.get(CacheKey.generate(task2)) is not None

        # task1 should NOT be in memory (evicted)
        assert cache._memory_cache.get(CacheKey.generate(task1)) is None

        # But task1 should still be retrievable from disk
        cached1 = cache.get(task1)
        assert cached1 is not None
        assert cached1.output == "output 1"


def test_cache_with_dependency_changes():
    """Test that cache invalidates when dependency changes."""
    config = CacheConfig(strategy=CacheStrategy.MEMORY)
    cache = ResultCache(config)

    task = TaskDefinition(
        id="task2",
        description="Depends on task1",
        depends_on=["task1"],
    )

    # First dependency result
    dep_result1 = TaskResult(
        task_id="task1",
        status=TaskStatus.COMPLETED,
        output="output1",
    )

    result = TaskResult(
        task_id="task2",
        status=TaskStatus.COMPLETED,
        output="result based on output1",
    )

    cache.put(task, result, {"task1": dep_result1})

    # Should get cached result with same dependency
    cached = cache.get(task, {"task1": dep_result1})
    assert cached is not None

    # Different dependency result
    dep_result2 = TaskResult(
        task_id="task1",
        status=TaskStatus.COMPLETED,
        output="output2",
    )

    # Should be cache miss (dependency changed)
    cached = cache.get(task, {"task1": dep_result2})
    assert cached is None


def test_cache_without_dependency_tracking():
    """Test cache without dependency tracking."""
    config = CacheConfig(
        strategy=CacheStrategy.MEMORY,
        include_dependencies=False,
    )
    cache = ResultCache(config)

    task = TaskDefinition(
        id="task2",
        description="Depends on task1",
        depends_on=["task1"],
    )

    dep_result1 = TaskResult(
        task_id="task1",
        status=TaskStatus.COMPLETED,
        output="output1",
    )

    result = TaskResult(
        task_id="task2",
        status=TaskStatus.COMPLETED,
        output="cached result",
    )

    cache.put(task, result, {"task1": dep_result1})

    # Different dependency should still hit cache
    # (because dependencies not tracked)
    dep_result2 = TaskResult(
        task_id="task1",
        status=TaskStatus.COMPLETED,
        output="output2",
    )

    cached = cache.get(task, {"task1": dep_result2})
    assert cached is not None
    assert cached.output == "cached result"
