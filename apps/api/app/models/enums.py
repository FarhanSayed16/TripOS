import enum

class UserRole(str, enum.Enum):
    agent = "agent"
    admin = "admin"

class OrgStatus(str, enum.Enum):
    pending_approval = "pending_approval"
    active = "active"
    inactive = "inactive"

class QuoteStatus(str, enum.Enum):
    draft = "draft"
    ready = "ready"
    sent = "sent"
    paid = "paid"
    expired = "expired"
    superseded = "superseded"  # ISSUE-06: quote was replaced via refresh
    cancelled = "cancelled"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    captured = "captured"
    failed = "failed"

class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"
    cancelled = "cancelled"

class BookingFailureReason(str, enum.Enum):
    fare_changed = "fare_changed"
    sold_out = "sold_out"
    supplier_timeout = "supplier_timeout"
    supplier_error = "supplier_error"
    missing_pax = "missing_pax"
    unknown = "unknown"

class RefundStatus(str, enum.Enum):
    requested = "requested"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"

class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    dead = "dead"

class PackageStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"
