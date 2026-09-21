import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.responses import StreamingResponse

from app.models.tenancy import User
from app.models.commercial import Booking, Quote


async def export_bookings_csv(current_user: User, db: AsyncSession) -> StreamingResponse:
    stmt = (
        select(Booking)
        .join(Quote)
        .options(
            selectinload(Booking.quote).selectinload(Quote.payment),
            selectinload(Booking.quote).selectinload(Quote.items),
        )
        .where(Quote.organization_id == current_user.active_organization_id)
        .order_by(Booking.created_at.desc())
    )
    bookings = (await db.execute(stmt)).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Booking ID",
            "PNR",
            "Status",
            "Failure Reason",
            "Created At",
            "Customer Total (paise)",
            "Payment Status",
        ]
    )

    for b in bookings:
        quote = b.quote
        payment = quote.payment if quote else None
        customer_total = sum(item.customer_total for item in quote.items) if quote and quote.items else 0
        payment_status = payment.status.value if payment else "none"

        writer.writerow(
            [
                str(b.id),
                b.supplier_pnr or "",
                b.status.value if hasattr(b.status, "value") else str(b.status),
                b.failure_reason.value if b.failure_reason else "",
                b.created_at.isoformat() if b.created_at else "",
                customer_total,
                payment_status,
            ]
        )

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bookings.csv"},
    )
