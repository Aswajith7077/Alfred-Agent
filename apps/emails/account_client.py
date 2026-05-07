from schema import EmailAccount
from schema import EmailFilter
from typing import List, Optional
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import logging

logger = logging.getLogger(__name__)


class AccountClient:
    def __init__(self, account: EmailAccount):
        self.account = account

    # ── Core fetch with filtering ────────────────────────────────────

    def fetch_emails(self, filter: Optional[EmailFilter] = None) -> List[dict]:
        if filter is None:
            filter = EmailFilter()

        criteria = filter.to_imap_criteria()

        with imaplib.IMAP4_SSL(self.account.imap_host, self.account.imap_port) as imap:

            folder = getattr(filter, 'folder', 'INBOX') or 'INBOX'
            imap.login(self.account.address, self.account.app_password)
            status, data = imap.select(folder)

            if status != 'OK':
                logger.error(f"Failed to select folder '{folder}': {data}")
                return []

            _, message_ids = imap.search(None, criteria)
            ids = message_ids[0].split()

            if not ids:
                return []

            # take last N, then reverse for newest-first
            ids = ids[-filter.limit :]
            emails = []

            for mid in reversed(ids):
                _, msg_data = imap.fetch(mid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                parsed = self._parse(msg)

                # post-filter: attachment check (IMAP can't do natively)
                if filter.has_attachment and not parsed["has_attachment"]:
                    continue

                emails.append(parsed)

        return emails

    # ── Convenience filter methods ───────────────────────────────────

    def fetch_unread(self, limit=10) -> List[dict]:
        return self.fetch_emails(EmailFilter(unread_only=True, limit=limit))

    def fetch_from_sender(self, sender: str, limit=10) -> List[dict]:
        return self.fetch_emails(EmailFilter(from_address=sender, limit=limit))

    def fetch_by_subject(self, keyword: str, limit=10) -> List[dict]:
        return self.fetch_emails(EmailFilter(subject_contains=keyword, limit=limit))

    def fetch_since(self, date: str, limit=20) -> List[dict]:
        """date format: '01-Jan-2025'"""
        return self.fetch_emails(EmailFilter(since_date=date, limit=limit))

    def fetch_with_attachments(self, limit=10) -> List[dict]:
        return self.fetch_emails(EmailFilter(has_attachment=True, limit=limit))

    def search(self, query: str, limit=10) -> List[dict]:
        """
        Free-form search — maps natural keywords to IMAP criteria.
        e.g. 'unread from boss' or 'invoice subject since January'
        Agent can call this directly.
        """
        f = EmailFilter(limit=limit)

        q = query.lower()
        if "unread" in q:
            f.unread_only = True
        if "attachment" in q:
            f.has_attachment = True
        if "from " in q:
            f.from_address = q.split("from ")[-1].split()[0]
        if "subject " in q:
            f.subject_contains = q.split("subject ")[-1].strip()

        return self.fetch_emails(f)

    # ── Parsing ──────────────────────────────────────────────────────

    def _parse(self, msg) -> dict:
        subject, enc = decode_header(msg["Subject"] or "")[0]
        if isinstance(subject, bytes):
            subject = subject.decode(enc or "utf-8", errors="ignore")

        body = ""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in disposition:
                    attachments.append(part.get_filename())
                elif content_type == "text/plain" and not body:
                    body = part.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

        return {
            "account": self.account.name,
            "from": msg["From"],
            "to": msg["To"],
            "subject": subject,
            "date": msg["Date"],
            "body": body[:2000],  # cap for LLM context
            "has_attachment": len(attachments) > 0,
            "attachments": attachments,
            "message_id": msg["Message-ID"],
        }

    # ── Sending ──────────────────────────────────────────────────────

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        reply_to_id: Optional[str] = None,  # for threading
        html: bool = False,
    ) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.account.address
            msg["To"] = to
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = cc
            if bcc:
                msg["Bcc"] = bcc

            # threading support — reply stays in same thread
            if reply_to_id:
                msg["In-Reply-To"] = reply_to_id
                msg["References"] = reply_to_id

            msg.attach(MIMEText(body, "html" if html else "plain"))

            with smtplib.SMTP(self.account.smtp_host, self.account.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.account.address, self.account.app_password)
                smtp.sendmail(self.account.address, to, msg.as_string())

            logger.info(f"[{self.account.name}] Sent → {to}")
            return True

        except Exception as e:
            logger.error(f"[{self.account.name}] Send failed: {e}")
            return False

    # ── Drafting — saved to Drafts folder via IMAP ───────────────────

    def save_draft(self, to: str, subject: str, body: str) -> dict:
        """Actually saves to Gmail Drafts folder — not just a local dict."""
        msg = MIMEMultipart("alternative")
        msg["From"] = self.account.address
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with imaplib.IMAP4_SSL(
                self.account.imap_host, self.account.imap_port
            ) as imap:
                import time
                imap.login(self.account.address, self.account.app_password)
                # append to Drafts — works on Gmail, Outlook, most providers
                imap.append(
                    "[Gmail]/Drafts",
                    "\\Draft",
                    imaplib.Time2Internaldate(time.time()),
                    msg.as_bytes(),
                )
            logger.info(f"[{self.account.name}] Draft saved")
            return {"status": "saved", "to": to, "subject": subject}

        except Exception as e:
            logger.error(f"[{self.account.name}] Draft save failed: {e}")
            # fallback to local draft
            return {"status": "local_draft", "to": to, "subject": subject, "body": body}
