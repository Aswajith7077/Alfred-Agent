from pydantic import BaseModel
from typing import Optional


class EmailAccount(BaseModel):
    name: str  # "Personal", "Work", "Client"
    address: str  # full email address
    app_password: str  # 16-char app password
    imap_host: str = "imap.gmail.com"
    smtp_host: str = "smtp.gmail.com"
    imap_port: int = 993
    smtp_port: int = 587
    protected: bool = False


class EmailFilter(BaseModel):
    """All filtering options in one place."""

    unread_only: bool = False
    from_address: Optional[str] = None  # "boss@company.com"
    to_address: Optional[str] = None
    subject_contains: Optional[str] = None  # "Invoice"
    body_contains: Optional[str] = None  # "urgent"
    since_date: Optional[str] = None  # "01-Jan-2025" (IMAP format)
    before_date: Optional[str] = None  # "31-Jan-2025"
    has_attachment: bool = False
    folder: str = "INBOX"
    limit: int = 10

    def to_imap_criteria(self) -> str:
        """Build IMAP search string from filter options."""
        parts = []

        if self.unread_only:
            parts.append("UNSEEN")
        if self.from_address:
            parts.append(f'FROM "{self.from_address}"')
        if self.to_address:
            parts.append(f'TO "{self.to_address}"')
        if self.subject_contains:
            parts.append(f'SUBJECT "{self.subject_contains}"')
        if self.body_contains:
            parts.append(f'BODY "{self.body_contains}"')
        if self.since_date:
            parts.append(f'SINCE "{self.since_date}"')
        if self.before_date:
            parts.append(f'BEFORE "{self.before_date}"')

        # IMAP doesn't have native attachment filter
        # handled in post-filter below
        return " ".join(parts) if parts else "ALL"
