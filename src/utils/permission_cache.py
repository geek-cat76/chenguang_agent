import json

from redis.asyncio import Redis


PERM_CACHE_PREFIX = "user:perms:"
ROLE_CACHE_PREFIX = "user:roles:"
CACHE_TTL = 1800


class PermissionCache:
    """Manage the cached permission and role codes for a user."""

    def __init__(self, redis: Redis):
        self.redis = redis

    @staticmethod
    def _decode_codes(data: str | bytes | None) -> set[str] | None:
        if data is None:
            return None
        try:
            values = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(values, list) or not all(
            isinstance(value, str) for value in values
        ):
            return None
        return set(values)

    async def get_permissions(self, user_id: int) -> set[str] | None:
        """Return None on a miss; an empty set is a valid cached value."""
        data = await self.redis.get(f"{PERM_CACHE_PREFIX}{user_id}")
        return self._decode_codes(data)

    async def set_permissions(self, user_id: int, permissions: set[str]) -> None:
        await self.redis.set(
            f"{PERM_CACHE_PREFIX}{user_id}",
            json.dumps(sorted(permissions)),
            ex=CACHE_TTL,
        )

    async def get_roles(self, user_id: int) -> set[str] | None:
        """Return None on a miss; an empty set is a valid cached value."""
        data = await self.redis.get(f"{ROLE_CACHE_PREFIX}{user_id}")
        return self._decode_codes(data)

    async def set_roles(self, user_id: int, roles: set[str]) -> None:
        await self.redis.set(
            f"{ROLE_CACHE_PREFIX}{user_id}",
            json.dumps(sorted(roles)),
            ex=CACHE_TTL,
        )

    async def set_user_cache(
        self,
        user_id: int,
        permissions: set[str],
        roles: set[str],
    ) -> None:
        """Atomically write both cache entries with the same TTL."""
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(
                f"{PERM_CACHE_PREFIX}{user_id}",
                json.dumps(sorted(permissions)),
                ex=CACHE_TTL,
            )
            pipe.set(
                f"{ROLE_CACHE_PREFIX}{user_id}",
                json.dumps(sorted(roles)),
                ex=CACHE_TTL,
            )
            await pipe.execute()

    async def delete_user_cache(self, user_id: int) -> None:
        """Invalidate both RBAC cache entries for one user."""
        await self.redis.delete(
            f"{PERM_CACHE_PREFIX}{user_id}",
            f"{ROLE_CACHE_PREFIX}{user_id}",
        )

    async def delete_user_cache_batch(self, user_ids: list[int]) -> None:
        """Invalidate both RBAC cache entries for each affected user."""
        unique_user_ids = list(dict.fromkeys(user_ids))
        if not unique_user_ids:
            return

        keys = [
            key
            for user_id in unique_user_ids
            for key in (
                f"{PERM_CACHE_PREFIX}{user_id}",
                f"{ROLE_CACHE_PREFIX}{user_id}",
            )
        ]
        await self.redis.delete(*keys)
