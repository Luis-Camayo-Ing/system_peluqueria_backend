"""External delivery helpers for internal sale receipts."""

from email.message import EmailMessage
from email.utils import formataddr
import smtplib
import ssl
from urllib.parse import quote

from app.core.config import Settings
from app.modules.sale.exceptions import (
    SaleEmailConfigurationException,
    SaleEmailSendingException,
)
from app.modules.sale.model import Sale, SaleStatus


STATUS_LABELS = {
    SaleStatus.COMPLETED: "Completada",
    SaleStatus.CANCELLED: "Cancelada",
}


class SmtpReceiptSender:
    """Send internal sale receipts using an SMTP server."""

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self.settings = settings

    def send(
        self,
        *,
        recipient_email: str,
        subject: str,
        body: str,
        pdf_content: bytes,
        filename: str,
    ) -> None:
        """Send one PDF receipt as an email attachment."""

        self._validate_configuration()

        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = formataddr(
            (
                self.settings.smtp_from_name,
                str(self.settings.smtp_from_email),
            )
        )
        message["To"] = recipient_email

        message.set_content(body)

        message.add_attachment(
            pdf_content,
            maintype="application",
            subtype="pdf",
            filename=filename,
        )

        context = ssl.create_default_context()

        try:
            if self.settings.smtp_use_ssl:
                with smtplib.SMTP_SSL(
                    host=str(self.settings.smtp_host),
                    port=self.settings.smtp_port,
                    timeout=self.settings.smtp_timeout_seconds,
                    context=context,
                ) as smtp_client:
                    self._authenticate_and_send(
                        smtp_client=smtp_client,
                        message=message,
                    )

            else:
                with smtplib.SMTP(
                    host=str(self.settings.smtp_host),
                    port=self.settings.smtp_port,
                    timeout=self.settings.smtp_timeout_seconds,
                ) as smtp_client:
                    smtp_client.ehlo()

                    if self.settings.smtp_use_tls:
                        smtp_client.starttls(
                            context=context
                        )
                        smtp_client.ehlo()

                    self._authenticate_and_send(
                        smtp_client=smtp_client,
                        message=message,
                    )

        except SaleEmailConfigurationException:
            raise

        except (
            OSError,
            smtplib.SMTPException,
            ValueError,
        ) as exception:
            raise SaleEmailSendingException() from exception

    def _authenticate_and_send(
        self,
        *,
        smtp_client,
        message: EmailMessage,
    ) -> None:
        if self.settings.smtp_username:
            smtp_client.login(
                self.settings.smtp_username,
                str(self.settings.smtp_password),
            )

        smtp_client.send_message(
            message
        )

    def _validate_configuration(
        self,
    ) -> None:
        if not self.settings.smtp_host:
            raise SaleEmailConfigurationException()

        if not self.settings.smtp_from_email:
            raise SaleEmailConfigurationException()

        if (
            self.settings.smtp_use_tls
            and self.settings.smtp_use_ssl
        ):
            raise SaleEmailConfigurationException()

        username_present = bool(
            self.settings.smtp_username
        )

        password_present = bool(
            self.settings.smtp_password
        )

        if username_present != password_present:
            raise SaleEmailConfigurationException()


def build_default_receipt_subject(
    sale: Sale,
) -> str:
    """Build the default receipt email subject."""

    return (
        f"Comprobante interno {sale.sale_number} "
        f"- {sale.company_name}"
    )


def build_default_receipt_message(
    sale: Sale,
) -> str:
    """Build the default plain-text receipt email."""

    status = STATUS_LABELS.get(
        sale.status,
        sale.status.value,
    )

    return "\n".join(
        [
            "Hola,",
            "",
            (
                "Adjuntamos el comprobante interno "
                f"de la venta {sale.sale_number}."
            ),
            "",
            f"Empresa: {sale.company_name}",
            f"Estado: {status}",
            f"Total: {_format_amount(sale.total_amount)}",
            "",
            (
                "Este comprobante es de uso interno "
                "y no corresponde a una factura electrónica."
            ),
        ]
    )


def build_default_whatsapp_message(
    sale: Sale,
) -> str:
    """Build the default WhatsApp receipt message."""

    status = STATUS_LABELS.get(
        sale.status,
        sale.status.value,
    )

    return "\n".join(
        [
            f"Comprobante interno {sale.sale_number}",
            f"Empresa: {sale.company_name}",
            f"Estado: {status}",
            f"Total: {_format_amount(sale.total_amount)}",
            "",
            (
                "Este mensaje no incluye el archivo PDF. "
                "El comprobante puede enviarse por correo "
                "o descargarse desde ERP Beauty Pro."
            ),
        ]
    )


def build_whatsapp_url(
    *,
    phone_number: str,
    message: str,
) -> str:
    """Return a wa.me URL without calling the Meta API."""

    encoded_message = quote(
        message,
        safe="",
    )

    return (
        f"https://wa.me/{phone_number}"
        f"?text={encoded_message}"
    )


def _format_amount(
    value,
) -> str:
    amount = f"{value:,.2f}"

    integer_part, decimal_part = amount.split(
        "."
    )

    integer_part = integer_part.replace(
        ",",
        ".",
    )

    return (
        "$ "
        f"{integer_part},{decimal_part}"
    )
