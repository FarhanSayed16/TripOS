import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.commercial import Booking, QuoteItem
from app.models.wallet import WalletLedgerEntry, CommissionRule
from app.models.tenancy import Organization


async def calculate_commission(booking: Booking, db: AsyncSession) -> int:
    """
    Commission = f(agent_markup) via CommissionRule, never inverted from customer_total.
    Formula (Sprint Q / FIX-P33-01):
      - If percentage rule: commission = agent_markup * value / 100
      - If flat_paise rule: commission = value
      - If no rule: commission = 100% of agent_markup
    platform_fee is platform revenue (not agent wallet).
    """
    stmt = select(QuoteItem).where(QuoteItem.quote_id == booking.quote_id)
    quote_items = (await db.execute(stmt)).scalars().all()

    org_id = booking.organization_id
    if not org_id and booking.quote_id:
        from app.models.commercial import Quote

        quote = await db.get(Quote, booking.quote_id)
        org_id = quote.organization_id if quote else None

    rules_stmt = select(CommissionRule).where(
        CommissionRule.is_active == True,  # noqa: E712
        CommissionRule.organization_id.in_([org_id, None]),
    )
    rules = (await db.execute(rules_stmt)).scalars().all()

    org_rules = {r.product_type: r for r in rules if r.organization_id == org_id}
    platform_rules = {r.product_type: r for r in rules if r.organization_id is None}

    def get_rule_for_type(item_type: str):
        if item_type in org_rules:
            return org_rules[item_type]
        if "all" in org_rules:
            return org_rules["all"]
        if item_type in platform_rules:
            return platform_rules[item_type]
        if "all" in platform_rules:
            return platform_rules["all"]
        return None

    total_commission = 0
    for item in quote_items:
        rule = get_rule_for_type("all")
        if rule:
            if rule.rule_type == "percentage":
                item_commission = int((item.agent_markup * rule.value) / 100)
            elif rule.rule_type == "flat_paise":
                item_commission = rule.value
            else:
                item_commission = item.agent_markup
        else:
            item_commission = item.agent_markup
        total_commission += item_commission

    return total_commission


def master_override_share(commission_amount: int) -> tuple[int, int]:
    """Split commission for master/sub using MASTER_COMMISSION_OVERRIDE_BPS."""
    bps = max(0, min(10_000, int(settings.MASTER_COMMISSION_OVERRIDE_BPS or 0)))
    master_amount = int(commission_amount * bps / 10_000)
    return master_amount, commission_amount - master_amount


async def create_commission_entry(
    booking: Booking, db: AsyncSession
) -> WalletLedgerEntry | list[WalletLedgerEntry] | None:
    """Called by worker after booking confirmed. Creates pending ledger entry."""
    commission_amount = await calculate_commission(booking, db)
    if commission_amount <= 0:
        return None

    org_id = booking.organization_id
    if not org_id:
        from app.models.commercial import Quote

        quote = await db.get(Quote, booking.quote_id)
        org_id = quote.organization_id if quote else None
        if org_id:
            booking.organization_id = org_id

    if not org_id:
        return None

    org = (
        await db.execute(select(Organization).where(Organization.id == org_id))
    ).scalar_one_or_none()

    if org and org.parent_organization_id:
        master_amount, agent_amount = master_override_share(commission_amount)
        master_entry = WalletLedgerEntry(
            organization_id=org.parent_organization_id,
            booking_id=booking.id,
            type="commission_earned",
            amount_paise=master_amount,
            status="pending",
            description=(
                f"Master override ({settings.MASTER_COMMISSION_OVERRIDE_BPS} bps) "
                f"for sub-agent booking {booking.id}"
            ),
        )
        agent_entry = WalletLedgerEntry(
            organization_id=org_id,
            booking_id=booking.id,
            type="commission_earned",
            amount_paise=agent_amount,
            status="pending",
            description=f"Commission for booking {booking.id}",
        )
        db.add_all([master_entry, agent_entry])
        await db.commit()
        return [master_entry, agent_entry]

    entry = WalletLedgerEntry(
        organization_id=org_id,
        booking_id=booking.id,
        type="commission_earned",
        amount_paise=commission_amount,
        status="pending",
        description=f"Commission for booking {booking.id}",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def mark_commission_available(booking_id: uuid.UUID, db: AsyncSession):
    """Called after settlement period. Sets pending → available (all rows for booking)."""
    stmt = select(WalletLedgerEntry).where(
        WalletLedgerEntry.booking_id == booking_id,
        WalletLedgerEntry.status == "pending",
        WalletLedgerEntry.type == "commission_earned",
    )
    entries = (await db.execute(stmt)).scalars().all()
    for entry in entries:
        entry.status = "available"
    if entries:
        await db.commit()


async def get_wallet_summary(org_id: uuid.UUID, db: AsyncSession) -> dict:
    """Returns {pending_paise, available_paise, total_earned_paise, total_settled_paise}."""
    stmt = select(WalletLedgerEntry).where(WalletLedgerEntry.organization_id == org_id)
    entries = (await db.execute(stmt)).scalars().all()

    summary = {
        "pending_paise": 0,
        "available_paise": 0,
        "total_earned_paise": 0,
        "total_settled_paise": 0,
    }

    for entry in entries:
        if entry.type == "commission_earned":
            summary["total_earned_paise"] += entry.amount_paise
            if entry.status == "pending":
                summary["pending_paise"] += entry.amount_paise
            elif entry.status == "available":
                summary["available_paise"] += entry.amount_paise
            elif entry.status == "settled":
                summary["total_settled_paise"] += entry.amount_paise
        elif entry.type == "commission_paid":
            summary["available_paise"] += entry.amount_paise
            summary["total_settled_paise"] -= entry.amount_paise

    return summary
