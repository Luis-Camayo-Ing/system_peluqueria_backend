"""Internal PDF receipt generation for sales."""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_RIGHT,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.modules.sale.exceptions import (
    SaleReceiptGenerationException,
)
from app.modules.sale.model import (
    Sale,
    SalePaymentMethod,
    SaleStatus,
)


PAGE_WIDTH, PAGE_HEIGHT = A4

DARK_COLOR = colors.HexColor("#1F2937")
BORDER_COLOR = colors.HexColor("#D1D5DB")
LIGHT_COLOR = colors.HexColor("#F3F4F6")
MUTED_COLOR = colors.HexColor("#6B7280")
SUCCESS_COLOR = colors.HexColor("#166534")
CANCELLED_COLOR = colors.HexColor("#B91C1C")


PAYMENT_LABELS = {
    SalePaymentMethod.CASH: "Efectivo",
    SalePaymentMethod.CARD: "Tarjeta",
    SalePaymentMethod.TRANSFER: "Transferencia",
    SalePaymentMethod.OTHER: "Otro",
}


def build_sale_receipt_filename(
    sale: Sale,
) -> str:
    """Return a filesystem-safe PDF filename."""

    safe_number = re.sub(
        r"[^A-Za-z0-9._-]+",
        "-",
        sale.sale_number,
    ).strip("-")

    if not safe_number:
        safe_number = str(sale.id)

    return (
        f"comprobante-{safe_number}.pdf"
    )


def build_sale_receipt_pdf(
    sale: Sale,
) -> bytes:
    """Generate an internal A4 receipt as PDF bytes."""

    try:
        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=14 * mm,
            bottomMargin=18 * mm,
            title=(
                "Comprobante interno "
                f"{sale.sale_number}"
            ),
            author=sale.company_name,
            subject="Comprobante interno de venta",
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReceiptTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            alignment=TA_CENTER,
            textColor=DARK_COLOR,
            spaceAfter=3 * mm,
        )

        subtitle_style = ParagraphStyle(
            "ReceiptSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=MUTED_COLOR,
        )

        normal_style = ParagraphStyle(
            "ReceiptNormal",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=DARK_COLOR,
        )

        right_style = ParagraphStyle(
            "ReceiptRight",
            parent=normal_style,
            alignment=TA_RIGHT,
        )

        section_style = ParagraphStyle(
            "ReceiptSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=DARK_COLOR,
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
        )

        story = []

        story.append(
            Paragraph(
                _safe_text(
                    sale.company_name
                ),
                title_style,
            )
        )

        company_information = [
            (
                "NIT: "
                + _safe_text(
                    sale.company_tax_id
                )
            ),
        ]

        if sale.company_phone:
            company_information.append(
                "Tel: "
                + _safe_text(
                    sale.company_phone
                )
            )

        if sale.company_email:
            company_information.append(
                _safe_text(
                    sale.company_email
                )
            )

        story.append(
            Paragraph(
                " | ".join(
                    company_information
                ),
                subtitle_style,
            )
        )

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        status_label = (
            "CANCELADO"
            if sale.status
            == SaleStatus.CANCELLED
            else "COMPLETADO"
        )

        status_color = (
            CANCELLED_COLOR
            if sale.status
            == SaleStatus.CANCELLED
            else SUCCESS_COLOR
        )

        status_table = Table(
            [
                [
                    Paragraph(
                        (
                            "<b>COMPROBANTE INTERNO</b>"
                            "<br/>"
                            "NO ES FACTURA "
                            "ELECTR\u00d3NICA"
                        ),
                        normal_style,
                    ),
                    Paragraph(
                        f"<b>{status_label}</b>",
                        right_style,
                    ),
                ]
            ],
            colWidths=[
                120 * mm,
                60 * mm,
            ],
        )

        status_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        LIGHT_COLOR,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.8,
                        status_color,
                    ),
                    (
                        "TEXTCOLOR",
                        (1, 0),
                        (1, 0),
                        status_color,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        story.append(status_table)
        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        information_table = Table(
            [
                [
                    "N\u00famero:",
                    _safe_text(
                        sale.sale_number
                    ),
                    "Fecha:",
                    _format_datetime(
                        sale.sold_at
                    ),
                ],
                [
                    "Estado:",
                    status_label,
                    "ID:",
                    _safe_text(
                        sale.id
                    ),
                ],
            ],
            colWidths=[
                25 * mm,
                65 * mm,
                25 * mm,
                65 * mm,
            ],
        )

        information_table.setStyle(
            _information_table_style()
        )

        story.append(information_table)

        story.append(
            Paragraph(
                "Cliente",
                section_style,
            )
        )

        customer_table = Table(
            [
                [
                    "Nombre:",
                    _safe_text(
                        sale.customer_name,
                        "Consumidor final",
                    ),
                ],
                [
                    "Documento:",
                    _safe_text(
                        sale.customer_document
                    ),
                ],
                [
                    "Tel\u00e9fono:",
                    _safe_text(
                        sale.customer_phone
                    ),
                ],
                [
                    "Correo:",
                    _safe_text(
                        sale.customer_email
                    ),
                ],
            ],
            colWidths=[
                35 * mm,
                145 * mm,
            ],
        )

        customer_table.setStyle(
            _information_table_style()
        )

        story.append(customer_table)

        story.append(
            Paragraph(
                "Detalle de la venta",
                section_style,
            )
        )

        detail_rows = [
            [
                "Descripci\u00f3n",
                "Cantidad",
                "Precio unit.",
                "Descuento",
                "Impuesto",
                "Total",
            ]
        ]

        for detail in sale.details:
            description_parts = [
                f"<b>{_safe_text(detail.item_name)}</b>"
            ]

            if detail.item_code:
                description_parts.append(
                    "C\u00f3digo: "
                    + _safe_text(
                        detail.item_code
                    )
                )

            if detail.item_description:
                description_parts.append(
                    _safe_text(
                        detail.item_description
                    )
                )

            detail_rows.append(
                [
                    Paragraph(
                        "<br/>".join(
                            description_parts
                        ),
                        normal_style,
                    ),
                    _format_quantity(
                        detail.quantity
                    ),
                    _format_money(
                        detail.unit_price
                    ),
                    _format_money(
                        detail.discount_amount
                    ),
                    _format_money(
                        detail.tax_amount
                    ),
                    _format_money(
                        detail.line_total
                    ),
                ]
            )

        detail_table = Table(
            detail_rows,
            colWidths=[
                72 * mm,
                18 * mm,
                28 * mm,
                22 * mm,
                18 * mm,
                22 * mm,
            ],
            repeatRows=1,
        )

        detail_table.setStyle(
            _data_table_style()
        )

        story.append(detail_table)

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        totals_table = Table(
            [
                [
                    "Subtotal",
                    _format_money(
                        sale.subtotal
                    ),
                ],
                [
                    "Descuentos",
                    _format_money(
                        sale.discount_amount
                    ),
                ],
                [
                    "Impuestos",
                    _format_money(
                        sale.tax_amount
                    ),
                ],
                [
                    Paragraph(
                        "<b>TOTAL</b>",
                        right_style,
                    ),
                    Paragraph(
                        "<b>"
                        + _format_money(
                            sale.total_amount
                        )
                        + "</b>",
                        right_style,
                    ),
                ],
                [
                    "Pagado",
                    _format_money(
                        sale.paid_amount
                    ),
                ],
                [
                    "Cambio",
                    _format_money(
                        sale.change_amount
                    ),
                ],
            ],
            colWidths=[
                130 * mm,
                50 * mm,
            ],
        )

        totals_table.setStyle(
            TableStyle(
                [
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "RIGHT",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        BORDER_COLOR,
                    ),
                    (
                        "BACKGROUND",
                        (0, 3),
                        (-1, 3),
                        LIGHT_COLOR,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, -1),
                        "Helvetica",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8.5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(totals_table)

        story.append(
            Paragraph(
                "Formas de pago",
                section_style,
            )
        )

        payment_rows = [
            [
                "M\u00e9todo",
                "Valor aplicado",
                "Entregado",
                "Referencia",
            ]
        ]

        for payment in sale.payments:
            payment_rows.append(
                [
                    PAYMENT_LABELS.get(
                        payment.payment_method,
                        payment.payment_method.value,
                    ),
                    _format_money(
                        payment.amount
                    ),
                    (
                        _format_money(
                            payment.tendered_amount
                        )
                        if (
                            payment.tendered_amount
                            is not None
                        )
                        else "-"
                    ),
                    _safe_text(
                        payment.reference
                    ),
                ]
            )

        payment_table = Table(
            payment_rows,
            colWidths=[
                45 * mm,
                45 * mm,
                45 * mm,
                45 * mm,
            ],
            repeatRows=1,
        )

        payment_table.setStyle(
            _data_table_style()
        )

        story.append(payment_table)

        if sale.notes:
            story.append(
                Paragraph(
                    "Observaciones",
                    section_style,
                )
            )

            story.append(
                Paragraph(
                    _safe_text(
                        sale.notes
                    ),
                    normal_style,
                )
            )

        if sale.status == SaleStatus.CANCELLED:
            story.append(
                Paragraph(
                    "Informaci\u00f3n de cancelaci\u00f3n",
                    section_style,
                )
            )

            cancellation_rows = [
                [
                    "Fecha:",
                    _format_datetime(
                        sale.cancelled_at
                    ),
                ],
                [
                    "Motivo:",
                    Paragraph(
                        _safe_text(
                            sale.cancellation_reason
                        ),
                        normal_style,
                    ),
                ],
            ]

            cancellation_table = Table(
                cancellation_rows,
                colWidths=[
                    35 * mm,
                    145 * mm,
                ],
            )

            cancellation_table.setStyle(
                TableStyle(
                    [
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.8,
                            CANCELLED_COLOR,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            BORDER_COLOR,
                        ),
                        (
                            "BACKGROUND",
                            (0, 0),
                            (0, -1),
                            LIGHT_COLOR,
                        ),
                        (
                            "FONTNAME",
                            (0, 0),
                            (0, -1),
                            "Helvetica-Bold",
                        ),
                        (
                            "FONTSIZE",
                            (0, 0),
                            (-1, -1),
                            8.5,
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                    ]
                )
            )

            story.append(
                cancellation_table
            )

        def draw_footer(
            canvas: Canvas,
            current_document: SimpleDocTemplate,
        ) -> None:
            canvas.saveState()

            canvas.setFillColor(
                MUTED_COLOR
            )

            canvas.setFont(
                "Helvetica",
                5.8,
            )

            canvas.drawCentredString(
                PAGE_WIDTH / 2,
                15.5 * mm,
                (
                    "Documento generado por ERP Beauty Pro. "
                    "Este comprobante es de uso interno."
                ),
            )

            canvas.drawCentredString(
                PAGE_WIDTH / 2,
                12.7 * mm,
                (
                    "No reemplaza la facturaci\u00f3n "
                    "electr\u00f3nica exigida por la "
                    "autoridad tributaria."
                ),
            )

            canvas.setStrokeColor(
                BORDER_COLOR
            )

            canvas.line(
                15 * mm,
                10 * mm,
                PAGE_WIDTH - 15 * mm,
                10 * mm,
            )

            canvas.setFont(
                "Helvetica",
                7,
            )

            canvas.drawString(
                15 * mm,
                6.5 * mm,
                "ERP Beauty Pro - comprobante interno",
            )

            canvas.drawRightString(
                PAGE_WIDTH - 15 * mm,
                6.5 * mm,
                (
                    "P\u00e1gina "
                    f"{current_document.page}"
                ),
            )

            canvas.restoreState()


        document.build(
            story,
            onFirstPage=draw_footer,
            onLaterPages=draw_footer,
        )

        pdf_content = buffer.getvalue()

        if not pdf_content.startswith(
            b"%PDF-"
        ):
            raise SaleReceiptGenerationException()

        if not pdf_content.rstrip().endswith(
            b"%%EOF"
        ):
            raise SaleReceiptGenerationException()

        return pdf_content

    except SaleReceiptGenerationException:
        raise

    except Exception as exception:
        raise SaleReceiptGenerationException() from exception


def _safe_text(
    value: object | None,
    fallback: str = "-",
) -> str:
    if value is None:
        return fallback

    normalized = str(value).strip()

    if not normalized:
        return fallback

    return escape(normalized)


def _format_money(
    value: Decimal | None,
) -> str:
    amount = Decimal(
        value or Decimal("0.00")
    ).quantize(
        Decimal("0.01")
    )

    formatted = f"{amount:,.2f}"

    integer_part, decimal_part = formatted.split(
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


def _format_quantity(
    value: Decimal,
) -> str:
    normalized = Decimal(value).normalize()

    return format(
        normalized,
        "f",
    )


def _format_datetime(
    value: datetime | None,
) -> str:
    if value is None:
        return "-"

    timezone_name = (
        value.tzname()
        if value.tzinfo is not None
        else None
    )

    result = value.strftime(
        "%d/%m/%Y %H:%M"
    )

    if timezone_name:
        result = (
            f"{result} {timezone_name}"
        )

    return result


def _information_table_style() -> TableStyle:
    return TableStyle(
        [
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                BORDER_COLOR,
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                LIGHT_COLOR,
            ),
            (
                "BACKGROUND",
                (2, 0),
                (2, -1),
                LIGHT_COLOR,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica",
            ),
            (
                "FONTNAME",
                (0, 0),
                (0, -1),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (2, 0),
                (2, -1),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8.5,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ]
    )


def _data_table_style() -> TableStyle:
    return TableStyle(
        [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                DARK_COLOR,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7.5,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                BORDER_COLOR,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "RIGHT",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ]
    )
