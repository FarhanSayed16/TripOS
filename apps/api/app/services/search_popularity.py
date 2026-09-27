"""Hot-route popularity from search_requests (live-inventory Phase 5)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import SearchRequest
from app.schemas.inventory import InventoryType, PassengerQuery, SearchQuery

logger = structlog.get_logger()


@dataclass
class PopularRoute:
    inv_type: str
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str]
    adults: int
    children: int
    infants: int
    hits: int

    def to_search_query(self) -> SearchQuery:
        inv = (
            InventoryType.HOTEL
            if self.inv_type == InventoryType.HOTEL.value or self.inv_type == "hotel"
            else InventoryType.FLIGHT
        )
        ret = None
        if self.return_date and self.return_date not in ("-", "null", "None"):
            ret = date.fromisoformat(str(self.return_date)[:10])
        return SearchQuery(
            type=inv,
            origin=self.origin,
            destination=self.destination,
            departure_date=date.fromisoformat(str(self.departure_date)[:10]),
            return_date=ret,
            passengers=PassengerQuery(
                adults=max(1, int(self.adults or 1)),
                children=max(0, int(self.children or 0)),
                infants=max(0, int(self.infants or 0)),
            ),
        )


def _payload_field(key: str):
    return SearchRequest.payload[key].as_string()


async def get_popular_routes(
    db: AsyncSession,
    *,
    days: int = 7,
    limit: int = 50,
) -> list[PopularRoute]:
    """
    Rank search_requests.payload routes by hit count over the last `days`.
    Uses JSONB key extraction (Postgres).
    """
    days = max(1, min(int(days), 30))
    limit = max(1, min(int(limit), 200))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    type_c = _payload_field("type")
    origin_c = _payload_field("origin")
    dest_c = _payload_field("destination")
    dep_c = _payload_field("departure_date")
    # return_date may be null in JSON
    ret_c = SearchRequest.payload["return_date"].as_string()
    adults_c = SearchRequest.payload["passengers"]["adults"].as_string()
    children_c = SearchRequest.payload["passengers"]["children"].as_string()
    infants_c = SearchRequest.payload["passengers"]["infants"].as_string()

    stmt = (
        select(
            type_c.label("inv_type"),
            origin_c.label("origin"),
            dest_c.label("destination"),
            dep_c.label("departure_date"),
            ret_c.label("return_date"),
            adults_c.label("adults"),
            children_c.label("children"),
            infants_c.label("infants"),
            func.count().label("hits"),
        )
        .where(SearchRequest.created_at >= cutoff)
        .group_by(
            type_c,
            origin_c,
            dest_c,
            dep_c,
            ret_c,
            adults_c,
            children_c,
            infants_c,
        )
        .order_by(func.count().desc())
        .limit(limit)
    )

    try:
        rows = (await db.execute(stmt)).all()
    except Exception as e:
        logger.warning("popular_routes_query_failed", error=str(e))
        return []

    out: list[PopularRoute] = []
    for row in rows:
        if not row.origin or not row.destination or not row.departure_date:
            continue
        try:
            out.append(
                PopularRoute(
                    inv_type=row.inv_type or "flight",
                    origin=str(row.origin).upper(),
                    destination=str(row.destination).upper(),
                    departure_date=str(row.departure_date)[:10],
                    return_date=(
                        str(row.return_date)[:10]
                        if row.return_date and str(row.return_date) not in ("None", "null")
                        else None
                    ),
                    adults=int(row.adults or 1),
                    children=int(row.children or 0),
                    infants=int(row.infants or 0),
                    hits=int(row.hits or 0),
                )
            )
        except Exception as e:
            logger.warning("popular_route_parse_failed", error=str(e), row=str(row))
    return out
