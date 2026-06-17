from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
)


class EmailService:
    @staticmethod
    async def send_password_reset_email(
        email: str,
        reset_token: str,
    ) -> None:
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        message = MessageSchema(
            subject="Password Reset",
            recipients=[email],
            body=f"""
            Click the link below to reset your password:

            {reset_link}
            """,
            subtype=MessageType.plain,
        )

        fm = FastMail(conf)
        await fm.send_message(message)
