from typing import TypeVar, Generic, Sequence, Any

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PageParams(BaseModel):
    limit: int = 50
    offset: int = 0


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    limit: int
    offset: int


async def paginate(
    db: AsyncSession,
    stmt: Select[Any],
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse:
    """Count + page a SQLAlchemy select. Preserves options/order on the page query."""
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    page_stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(page_stmt)
    items = result.scalars().unique().all()
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
