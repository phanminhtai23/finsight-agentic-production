"""Repository abstractions.

Services depend on these ``Protocol`` interfaces, not on concrete SQLAlchemy
implementations (Dependency Inversion). Concrete repos live alongside and are wired
through the DI layer.
"""

from typing import Protocol, TypeVar
from uuid import UUID

T = TypeVar("T")


class Repository(Protocol[T]):
    """Generic async CRUD contract."""

    async def get(self, entity_id: UUID) -> T | None: ...

    async def add(self, entity: T) -> T: ...

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[T]: ...

    async def delete(self, entity_id: UUID) -> None: ...
