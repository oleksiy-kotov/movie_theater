import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from jinja2 import Environment, FileSystemLoader
from exceptions import BaseEmailError
from app.notifications.interfaces import EmailSenderInterface

logger = logging.getLogger(__name__)

class EmailSender(EmailSenderInterface):
    def __init__(
        self,
        hostname: str,
        port: int,
        email: str,
        password: str,
        use_tls: bool,
        template_dir: str,
        activation_email_template_name: str,
        activation_complete_email_template_name: str,
        password_email_template_name: str,
        password_complete_email_template_name: str,
    ):
        self._hostname = hostname
        self._port = port
        self._email = email
        self._password = password
        self._use_tls = use_tls

        self._activation_email_template_name = activation_email_template_name
        self._activation_complete_email_template_name = activation_complete_email_template_name
        self._password_email_template_name = password_email_template_name
        self._password_complete_email_template_name = password_complete_email_template_name

        self._env = Environment(loader=FileSystemLoader(template_dir))
        self._smtp = None

    async def _ensure_connection(self):
        if self._smtp is None or not self._smtp.is_connected():
            self._smtp = aiosmtplib.SMTP(hostname=self._hostname, port=self._port, start_tls=self._use_tls)
            await self._smtp.connect()
            if self._use_tls:
                await self._smtp.starttls()
            await self._smtp.login(self._email, self._password)

    async def _send_email(self, recipient: str, subject: str, html_content: str) -> None:
        await self._ensure_connection()

        message = MIMEMultipart()
        message["From"] = self._email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(html_content, "html"))

        try:
            await self._smtp.sendmail(self._email, [recipient], message.as_string())
        except aiosmtplib.SMTPException as error:
            logger.error(f"Failed to send email to {recipient}: {error}", exc_info=True)
            raise BaseEmailError(f"Failed to send email to {recipient}: {error}")

    async def _send_templated_email(
        self,
        recipient: str,
        template_name: str,
        subject: str,
        context: dict
    ) -> None:
        template = self._env.get_template(template_name)
        html_content = template.render(**context)
        await self._send_email(recipient, subject, html_content)

    async def send_activation_email(self, email: str, activation_link: str) -> None:
        await self._send_templated_email(
            recipient=email,
            template_name=self._activation_email_template_name,
            subject="Account Activation",
            context={"email": email, "activation_link": activation_link}
        )

    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        await self._send_templated_email(
            recipient=email,
            template_name=self._activation_complete_email_template_name,
            subject="Account Activated Successfully",
            context={"email": email, "login_link": login_link}
        )

    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        await self._send_templated_email(
            recipient=email,
            template_name=self._password_email_template_name,
            subject="Password Reset Request",
            context={"email": email, "reset_link": reset_link}
        )

    async def send_password_reset_complete_email(self, email: str, login_link: str) -> None:
        await self._send_templated_email(
            recipient=email,
            template_name=self._password_complete_email_template_name,
            subject="Your Password Has Been Successfully Reset",
            context={"email": email, "login_link": login_link}
        )