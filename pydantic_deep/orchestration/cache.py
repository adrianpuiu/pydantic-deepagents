"""Result caching for orchestration workflows.

This module provides intelligent caching of task results to avoid re-execution
when inputs haven't changed, significantly improving performance for repeated
workflows.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic_deep.orchestration.models import TaskDefinition, TaskResult


class CacheStrategy(str, Enum):
    """Cache storage strategies."""

    NONE = "none"  # No caching
    MEMORY = "memory"  # In-memory cache only
    DISK = "disk"  # Persistent disk cache
    HYBRID = "hybrid"  # Memory + disk


@dataclass
class CacheConfig:
    """Configuration for result caching."""

    strategy: CacheStrategy = CacheStrategy.MEMORY
    ttl_seconds: float | None = None  # Time-to-live for cache entries
    max_size: int = 1000  # Maximum number of cached results
    cache_dir: Path | None = None  # Directory for disk cache
    include_dependencies: bool = True  # Include dependency outputs in cache key


@dataclass
class CacheEntry:
    """Single cache entry."""

    key: str
    result: TaskResult
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    dependency_keys: list[str] = field(default_factory=list)


class CacheKey:
    """Generates cache keys for tasks."""

    @staticmethod
    def generate(
        task: TaskDefinition,
        dependency_results: dict[str, TaskResult] | None = None,
        include_dependencies: bool = True,
    ) -> str:
        """Generate cache key for a task.

        The cache key is based on:
        - Task description
        - Task parameters
        - Dependency outputs (optional)

        Args:
            task: Task definition.
            dependency_results: Results from dependency tasks.
            include_dependencies: Whether to include dependency outputs in key.

        Returns:
            Cache key string (SHA-256 hash).
        """
        key_components = {
            "task_id": task.id,
            "description": task.description,
            "parameters": task.parameters,
            "required_capabilities": [str(c) for c in task.required_capabilities],
            "required_skills": task.required_skills,
        }

        # Include dependency outputs in cache key
        if include_dependencies and dependency_results:
            dep_outputs = {}
            for dep_id in task.depends_on:
                if dep_id in dependency_results:
                    result = dependency_results[dep_id]
                    # Use only output, not timing or retry info
                    dep_outputs[dep_id] = str(result.output)
            key_components["dependencies"] = dep_outputs

        # Create deterministic JSON and hash it
        key_json = json.dumps(key_components, sort_keys=True)
        return hashlib.sha256(key_json.encode()).hexdigest()


class ResultCache:
    """Intelligent result cache for task execution."""

    def __init__(self, config: CacheConfig | None = None) -> None:
        """Initialize result cache.

        Args:
            config: Cache configuration. If None, uses default config.
        """
        self.config = config or CacheConfig()
        self._memory_cache: dict[str, CacheEntry] = {}

        # Initialize disk cache directory if needed
        if self.config.strategy in (CacheStrategy.DISK, CacheStrategy.HYBRID):
            if self.config.cache_dir is None:
                self.config.cache_dir = Path.home() / ".pydantic-deep" / "cache"
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._invalidations = 0

    def get(
        self,
        task: TaskDefinition,
        dependency_results: dict[str, TaskResult] | None = None,
    ) -> TaskResult | None:
        """Get cached result for a task.

        Args:
            task: Task definition.
            dependency_results: Results from dependency tasks.

        Returns:
            Cached task result or None if not found/expired.
        """
        if self.config.strategy == CacheStrategy.NONE:
            return None

        # Generate cache key
        key = CacheKey.generate(task, dependency_results, self.config.include_dependencies)

        # Try memory cache first (for hybrid and memory strategies)
        if self.config.strategy in (CacheStrategy.MEMORY, CacheStrategy.HYBRID):
            entry = self._memory_cache.get(key)
            if entry and self._is_valid(entry):
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                self._hits += 1
                return entry.result

        # Try disk cache (for hybrid and disk strategies)
        if self.config.strategy in (CacheStrategy.DISK, CacheStrategy.HYBRID):
            result = self._load_from_disk(key)
            if result:
                self._hits += 1
                # Promote to memory cache if hybrid
                if self.config.strategy == CacheStrategy.HYBRID:
                    self._store_in_memory(key, result)
                return result

        self._misses += 1
        return None

    def put(
        self,
        task: TaskDefinition,
        result: TaskResult,
        dependency_results: dict[str, TaskResult] | None = None,
    ) -> None:
        """Store task result in cache.

        Args:
            task: Task definition.
            result: Task result to cache.
            dependency_results: Results from dependency tasks.
        """
        if self.config.strategy == CacheStrategy.NONE:
            return

        # Generate cache key
        key = CacheKey.generate(task, dependency_results, self.config.include_dependencies)

        # Get dependency keys
        dep_keys = []
        if self.config.include_dependencies and dependency_results:
            for dep_id in task.depends_on:
                if dep_id in dependency_results:
                    dep_key = CacheKey.generate(
                        TaskDefinition(id=dep_id, description=""),
                        None,
                        False,
                    )
                    dep_keys.append(dep_key)

        # Store in memory cache
        if self.config.strategy in (CacheStrategy.MEMORY, CacheStrategy.HYBRID):
            self._store_in_memory(key, result, dep_keys)

        # Store in disk cache
        if self.config.strategy in (CacheStrategy.DISK, CacheStrategy.HYBRID):
            self._save_to_disk(key, result)

    def invalidate(self, task_id: str) -> int:
        """Invalidate cache entries for a specific task.

        Args:
            task_id: ID of the task to invalidate.

        Returns:
            Number of entries invalidated.
        """
        count = 0

        # Invalidate from memory cache
        keys_to_remove = [k for k, v in self._memory_cache.items() if task_id in k]
        for key in keys_to_remove:
            del self._memory_cache[key]
            count += 1

        # Invalidate from disk cache
        if self.config.cache_dir:
            for cache_file in self.config.cache_dir.glob(f"*{task_id}*.cache"):
                cache_file.unlink()
                count += 1

        self._invalidations += count
        return count

    def invalidate_dependents(self, task_id: str) -> int:
        """Invalidate all cache entries that depend on a task.

        Args:
            task_id: ID of the task whose dependents should be invalidated.

        Returns:
            Number of entries invalidated.
        """
        count = 0

        # Find entries that depend on this task
        task_key = hashlib.sha256(task_id.encode()).hexdigest()[:16]
        keys_to_remove = []

        for key, entry in self._memory_cache.items():
            if task_key in entry.dependency_keys:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._memory_cache[key]
            count += 1

        self._invalidations += count
        return count

    def clear(self) -> None:
        """Clear all cache entries."""
        self._memory_cache.clear()

        # Clear disk cache
        if self.config.cache_dir and self.config.cache_dir.exists():
            for cache_file in self.config.cache_dir.glob("*.cache"):
                cache_file.unlink()

        # Reset statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._invalidations = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "strategy": self.config.strategy,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "evictions": self._evictions,
            "invalidations": self._invalidations,
            "cache_size": len(self._memory_cache),
            "max_size": self.config.max_size,
        }

    def _is_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is still valid.

        Args:
            entry: Cache entry to validate.

        Returns:
            True if entry is valid, False if expired.
        """
        if self.config.ttl_seconds is None:
            return True

        age = (datetime.now() - entry.created_at).total_seconds()
        return age < self.config.ttl_seconds

    def _store_in_memory(
        self,
        key: str,
        result: TaskResult,
        dependency_keys: list[str] | None = None,
    ) -> None:
        """Store entry in memory cache.

        Args:
            key: Cache key.
            result: Task result.
            dependency_keys: Keys of dependency tasks.
        """
        # Evict if at capacity (LRU)
        if len(self._memory_cache) >= self.config.max_size:
            self._evict_lru()

        entry = CacheEntry(
            key=key,
            result=result,
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            dependency_keys=dependency_keys or [],
        )
        self._memory_cache[key] = entry

    def _evict_lru(self) -> None:
        """Evict least recently used entry from cache."""
        if not self._memory_cache:
            return

        # Find LRU entry
        lru_key = min(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k].accessed_at,
        )

        del self._memory_cache[lru_key]
        self._evictions += 1

    def _save_to_disk(self, key: str, result: TaskResult) -> None:
        """Save result to disk cache.

        Args:
            key: Cache key.
            result: Task result to save.
        """
        if not self.config.cache_dir:
            return

        cache_file = self.config.cache_dir / f"{key}.cache"
        try:
            with cache_file.open("wb") as f:
                pickle.dump(result, f)
        except Exception:
            # Silently fail on cache write errors
            pass

    def _load_from_disk(self, key: str) -> TaskResult | None:
        """Load result from disk cache.

        Args:
            key: Cache key.

        Returns:
            Cached task result or None.
        """
        if not self.config.cache_dir:
            return None

        cache_file = self.config.cache_dir / f"{key}.cache"
        if not cache_file.exists():
            return None

        # Check TTL
        if self.config.ttl_seconds is not None:
            age = (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds()
            if age >= self.config.ttl_seconds:
                cache_file.unlink()
                return None

        try:
            with cache_file.open("rb") as f:
                return pickle.load(f)
        except Exception:
            # Silently fail on cache read errors
            return None


__all__ = [
    "ResultCache",
    "CacheConfig",
    "CacheStrategy",
    "CacheKey",
    "CacheEntry",
]
