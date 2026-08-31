"""create purchase order and receipt tables

Revision ID: ee7da7cae44d
Revises: 5596c072880d
Create Date: 2026-08-02 16:28:15.007802

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "ee7da7cae44d"
down_revision: Union[str, Sequence[str], None] = "5596c072880d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


purchase_order_status_enum = postgresql.ENUM(
    "draft",
    "approved",
    "partially_received",
    "received",
    "cancelled",
    name="purchase_order_status",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    purchase_order_status_enum.create(
        bind,
        checkfirst=True,
    )

    op.create_table(
        "purchase_orders",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "approved_by_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "cancelled_by_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "order_number",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "status",
            purchase_order_status_enum,
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "expected_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=14, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "tax_amount",
            sa.Numeric(precision=14, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "discount_amount",
            sa.Numeric(precision=14, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(precision=14, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "cancellation_reason",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(trim(order_number)) > 0",
            name="ck_purchase_orders_order_number_not_blank",
        ),
        sa.CheckConstraint(
            "discount_amount >= 0",
            name="ck_purchase_orders_discount_non_negative",
        ),
        sa.CheckConstraint(
            "subtotal >= 0",
            name="ck_purchase_orders_subtotal_non_negative",
        ),
        sa.CheckConstraint(
            "tax_amount >= 0",
            name="ck_purchase_orders_tax_non_negative",
        ),
        sa.CheckConstraint(
            "total_amount >= 0",
            name="ck_purchase_orders_total_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["cancelled_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "order_number",
            name="uq_purchase_orders_company_order_number",
        ),
    )

    op.create_index(
        "ix_purchase_orders_company_status_created",
        "purchase_orders",
        ["company_id", "status", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_purchase_orders_supplier_status",
        "purchase_orders",
        ["supplier_id", "status"],
        unique=False,
    )

    op.create_table(
        "purchase_order_details",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "purchase_order_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "ordered_quantity",
            sa.Numeric(precision=14, scale=3),
            nullable=False,
        ),
        sa.Column(
            "received_quantity",
            sa.Numeric(precision=14, scale=3),
            server_default="0.000",
            nullable=False,
        ),
        sa.Column(
            "unit_cost",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "line_total",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "line_total >= 0",
            name="ck_purchase_order_details_line_total_non_negative",
        ),
        sa.CheckConstraint(
            "ordered_quantity > 0",
            name="ck_purchase_order_details_quantity_positive",
        ),
        sa.CheckConstraint(
            "received_quantity <= ordered_quantity",
            name=(
                "ck_purchase_order_details_received_not_exceed_ordered"
            ),
        ),
        sa.CheckConstraint(
            "received_quantity >= 0",
            name="ck_purchase_order_details_received_non_negative",
        ),
        sa.CheckConstraint(
            "unit_cost >= 0",
            name="ck_purchase_order_details_unit_cost_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["purchase_order_id"],
            ["purchase_orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "purchase_order_id",
            "product_id",
            name="uq_purchase_order_details_order_product",
        ),
    )

    op.create_index(
        "ix_purchase_order_details_product",
        "purchase_order_details",
        ["product_id"],
        unique=False,
    )

    op.create_table(
        "purchase_receipts",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "purchase_order_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "received_by_user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "inventory_movement_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "receipt_number",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "supplier_invoice_number",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=14, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "tax_amount",
            sa.Numeric(precision=14, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "discount_amount",
            sa.Numeric(precision=14, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(precision=14, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(trim(receipt_number)) > 0",
            name="ck_purchase_receipts_receipt_number_not_blank",
        ),
        sa.CheckConstraint(
            "discount_amount >= 0",
            name="ck_purchase_receipts_discount_non_negative",
        ),
        sa.CheckConstraint(
            "subtotal >= 0",
            name="ck_purchase_receipts_subtotal_non_negative",
        ),
        sa.CheckConstraint(
            "tax_amount >= 0",
            name="ck_purchase_receipts_tax_non_negative",
        ),
        sa.CheckConstraint(
            "total_amount >= 0",
            name="ck_purchase_receipts_total_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_movement_id"],
            ["inventory_movements.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["purchase_order_id"],
            ["purchase_orders.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["received_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "receipt_number",
            name="uq_purchase_receipts_company_receipt_number",
        ),
        sa.UniqueConstraint(
            "inventory_movement_id",
            name="uq_purchase_receipts_inventory_movement",
        ),
    )

    op.create_index(
        "ix_purchase_receipts_company_received",
        "purchase_receipts",
        ["company_id", "received_at"],
        unique=False,
    )

    op.create_index(
        "ix_purchase_receipts_order_received",
        "purchase_receipts",
        ["purchase_order_id", "received_at"],
        unique=False,
    )

    op.create_table(
        "purchase_receipt_details",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "purchase_receipt_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "purchase_order_detail_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Numeric(precision=14, scale=3),
            nullable=False,
        ),
        sa.Column(
            "unit_cost",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "line_total",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column(
            "stock_before",
            sa.Numeric(precision=14, scale=3),
            nullable=False,
        ),
        sa.Column(
            "stock_after",
            sa.Numeric(precision=14, scale=3),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "line_total >= 0",
            name="ck_purchase_receipt_details_line_total_non_negative",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_purchase_receipt_details_quantity_positive",
        ),
        sa.CheckConstraint(
            "stock_after >= stock_before",
            name="ck_purchase_receipt_details_stock_after_valid",
        ),
        sa.CheckConstraint(
            "stock_before >= 0",
            name="ck_purchase_receipt_details_stock_before_non_negative",
        ),
        sa.CheckConstraint(
            "unit_cost >= 0",
            name="ck_purchase_receipt_details_unit_cost_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["purchase_order_detail_id"],
            ["purchase_order_details.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["purchase_receipt_id"],
            ["purchase_receipts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "purchase_receipt_id",
            "purchase_order_detail_id",
            name="uq_purchase_receipt_details_receipt_order_detail",
        ),
    )

    op.create_index(
        "ix_purchase_receipt_details_product",
        "purchase_receipt_details",
        ["product_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_purchase_receipt_details_product",
        table_name="purchase_receipt_details",
    )
    op.drop_table("purchase_receipt_details")

    op.drop_index(
        "ix_purchase_receipts_order_received",
        table_name="purchase_receipts",
    )
    op.drop_index(
        "ix_purchase_receipts_company_received",
        table_name="purchase_receipts",
    )
    op.drop_table("purchase_receipts")

    op.drop_index(
        "ix_purchase_order_details_product",
        table_name="purchase_order_details",
    )
    op.drop_table("purchase_order_details")

    op.drop_index(
        "ix_purchase_orders_supplier_status",
        table_name="purchase_orders",
    )
    op.drop_index(
        "ix_purchase_orders_company_status_created",
        table_name="purchase_orders",
    )
    op.drop_table("purchase_orders")

    bind = op.get_bind()

    purchase_order_status_enum.drop(
        bind,
        checkfirst=True,
    )