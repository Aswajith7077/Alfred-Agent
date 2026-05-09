from typing import List
from agents import BaseTool
from schema import EmailAccount
from schema import EmailFilter
from .account_client import AccountClient
from .registry import EmailRegistry
import logging

logger = logging.getLogger(__name__)


class Email(BaseTool):
    def __init__(self, registry: EmailRegistry):
        self.registry = registry
        self.clients: dict[str, AccountClient] = {}
        self._sync_clients()

    def _sync_clients(self):
        """Rebuild clients from current registry state."""
        self.clients = {
            acc.name: AccountClient(acc)
            for acc in self.registry.all()
        }

    # Account Management Actions

    def add_account(self, account: EmailAccount) -> bool:
        ok = self.registry.add(account)
        if ok:
            self.clients[account.name] = AccountClient(account)
        return ok

    def remove_account(self, name: str) -> bool:
        ok = self.registry.remove(name)
        if ok:
            self.clients.pop(name, None)
        return ok

    def list_accounts(self) -> List[dict]:
        return self.registry.list_accounts()


    # Email Actions

    def fetch_all(self, limit=5, unread_only=False) -> dict:
        """Fetch from all 3 accounts at once."""
        results = {}
        for name, client in self.clients.items():
            try:
                results[name] = client.fetch_emails(
                    limit=limit, unread_only=unread_only
                )
            except Exception as e:
                logger.error(f"[EMAIL] Failed to fetch {name}: {e}")
                results[name] = []
        return results

    def fetch_from(self, account_name: str, **kwargs) -> List[dict]:
        return self.clients[account_name].fetch_emails(**kwargs)

    def send(self, account_name: str, to: str, subject: str, body: str) -> bool:
        return self.clients[account_name].send_email(to, subject, body)

    def draft(self, account_name: str, to: str, subject: str, body: str) -> dict:
        return self.clients[account_name].draft_email(to, subject, body)

    # Agent Tools

    def get_agent_tools(self) -> List:
        from langchain.tools import tool
        service = self

        @tool
        def fetch_emails(
            account: str,
            folder: str = "INBOX",
            unread_only: bool = False,
            from_address: str = None,
            subject_contains: str = None,
            since_date: str = None,
            has_attachment: bool = False,
            limit: int = 10,
        ) -> List[dict]:
            """
            Fetch emails from an account folder.

            FOLDER NAMES (use exactly as shown):
            Gmail:
            INBOX, [Gmail]/Drafts, [Gmail]/Sent Mail, [Gmail]/Spam, [Gmail]/Trash, [Gmail]/Starred, [Gmail]/All Mail
            Outlook:
            INBOX, Drafts, Sent, Trash, Junk, Archive

            PARAMETERS:
            - account       : account name (required)
            - folder        : folder to fetch from (default: INBOX)
            - unread_only   : True = unread only, False = all
            - from_address  : filter by sender email
            - subject_contains : filter by subject keyword
            - since_date    : filter emails after date (format: '01-Jan-2025')
            - has_attachment: True = only emails with attachments
            - limit         : max emails to return (default: 10)

            RETURNS: list of dicts with keys: subject, from, to, body, date, attachments

            TO SEND A DRAFT:
            1. fetch_emails(account=..., folder='[Gmail]/Drafts')
            2. send_email(account=..., to=..., subject=..., body=...) using the draft fields
            """
            f = EmailFilter(
                folder=folder,
                unread_only=unread_only,
                from_address=from_address,
                subject_contains=subject_contains,
                since_date=since_date,
                has_attachment=has_attachment,
                limit=limit,
            )
            return service.clients[account].fetch_emails(f)

        @tool
        def fetch_all_accounts(unread_only: bool = True) -> dict:
            """Check all accounts for new emails at once."""
            return service.fetch_all(unread_only=unread_only)

        @tool
        def send_email(
            account: str, to: str, subject: str, body: str, cc: str = None
        ) -> bool:
            """
            Send email from a specific account to a specific mail id. 
            
            Account: The Existing accound from which the email is sent. (Should be provided by the user, if not provided, the 'Personal' account will be used)
            To: The Email Address of the recipient
            Subject: The Subject of the email, A short sentence about the content of the email
            Body: The Body of the email, The Actual content of the email (Source of Truth)
            CC: The Email Address of the CC recipient (Optional)

            Returns:
                True if the email was sent successfully, False if the email was not sent (sent operation unsuccessful)
            """
            return service.clients[account].send_email(to, subject, body, cc=cc)

        @tool
        def save_draft(account: str, to: str, subject: str, body: str) -> dict:
            """
            Save a draft to the Drafts folder. Draft is a temporary copy of an email that is not yet sent. 
            Any rough work of the email can be saved as a draft.
            
            Account: The Existing accound from which the email is sent. (Should be provided by the user, if not provided, the 'Personal' account will be used)
            To: The Email Address of the recipient
            Subject: The Subject of the email, A short sentence about the content of the email
            Body: The Body of the email, The Actual content of the email (Source of Truth)
            
            Returns:
                The saved draft email object
            """
            return service.clients[account].save_draft(to, subject, body)

        @tool
        def search_emails(account: str, query: str) -> List[dict]:
            """
            Search emails. e.g. 'unread from john' or 'subject invoice'

            Examples:
            - "unread from john" -> Search for unread emails from john
            - "subject invoice" -> Search for emails with subject containing "invoice"
            - "from boss" -> Search for emails from boss
            - "attachment" -> Search for emails with attachments
            
            Account: The Existing accound from which the email is sent. (Should be provided by the user, if not provided, the 'Personal' account will be used)
            Query: The search query (e.g. 'unread from john' or 'subject invoice')
            
            Returns:
                A list of dictionaries containing the email details
            """
            return service.clients[account].search(query)

        @tool
        def add_email_account(
            name: str,
            address: str,
            app_password: str,
            imap_host: str = "imap.gmail.com",
            smtp_host: str = "smtp.gmail.com",
        ) -> bool:
            """
            Add a new email account to the registry. 
            
            Name: The name of the email account (e.g. 'Personal', 'Work')
            Address: The Email Address of the email account
            App Password: The App Password of the email account
            IMAP Host: The IMAP Host of the email account (Default: 'imap.gmail.com')
            SMTP Host: The SMTP Host of the email account (Default: 'smtp.gmail.com')
            
            Returns:
                True if the account addition was successful, False if the account already exists
            """
            acc = EmailAccount(
                name=name,
                address=address,
                app_password=app_password,
                imap_host=imap_host,
                smtp_host=smtp_host,
            )
            return service.add_account(acc)

        @tool
        def remove_email_account(name: str) -> bool:
            """
            Remove an email account from the context. Protected accounts (Root User's accounts) cannot be removed.
            
            Name: The name of the email account to remove

            Returns:
                True if the account removal was successful, False if the account was not found or is protected
            """
            return service.remove_account(name)

        @tool
        def list_email_accounts() -> List[dict]:
            """
            List all registered email accounts, that are currently in the context.

            Example:
            {
                "Personal": {
                    "name":      "Personal",
                    "address":   "example@gmail.com",
                    "protected": False,
                    "imap_host": "imap.gmail.com",
                },
                "Work": {
                    "name":      "Work",
                    "address":   "example@work.com",
                    "protected": False,
                    "imap_host": "imap.work.com",
                },
                "Alice Personal": {
                    "name":      "Alice Personal",
                    "address":   "alice@gmail.com",
                    "protected": False,
                    "imap_host": "imap.gmail.com",
                },
                "Bob Work": {
                    "name":      "Bob Work",
                    "address":   "bob@work.com"
                    "protected": False,
                    "imap_host": "imap.work.com",
                }
            }

            Note these are just examples not the actual data. The Format of the JSON will be the same for the actual one.

            Returns:
                A list of dictionaries containing the email account details. (name: key -> accound: EmailAccount)
            """
            return service.list_accounts()

        return [
            fetch_emails,
            fetch_all_accounts,
            send_email,
            save_draft,
            search_emails,
            add_email_account,
            remove_email_account,
            list_email_accounts,
        ]