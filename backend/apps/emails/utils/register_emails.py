from schema import EmailAccount
from config import Settings
from emails.registry import EmailRegistry
from emails.service import Email


def register_emails() -> Email:

    settings = Settings()
    root_accounts = [
        EmailAccount(
            name=settings.EMAIL_NAME_I,
            address=settings.EMAIL_ADDRESS_I,
            app_password=settings.EMAIL_APP_PASSWORD_I,
        ),
        EmailAccount(
            name=settings.EMAIL_NAME_II,
            address=settings.EMAIL_ADDRESS_II,
            app_password=settings.EMAIL_APP_PASSWORD_II,
        ),
    ]

    registry = EmailRegistry(
        settings=settings,
        root_accounts=root_accounts,   # seeded once, protected forever
    )

    email_service = Email(registry)
    return email_service