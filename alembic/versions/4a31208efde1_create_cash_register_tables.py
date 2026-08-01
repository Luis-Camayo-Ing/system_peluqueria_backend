"""create cash register tables

Revision ID: 4a31208efde1
Revises: 501c39f48e00
Create Date: 2026-08-01 22:50:03.144185

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "4a31208efde1"
down_revision: Union[str, Sequence[str], None] = "501c39f48e00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


cash_session_status_enum = postgresql.ENUM(
    "open",
    "closed",
    name="cash_session_status",
    create_type=False,
)

cash_transaction_type_enum = postgresql.ENUM(
    "income",
    "expense",
    name="cash_transaction_type",
    create_type=False,
)

cash_transaction_source_enum = postgresql.ENUM(
    "manual",
    "sale",
    "purchase",
    "refund",
    "adjustment",
    "other",
    name="cash_transaction_source",
    create_type=False,
)


def upgrade() -> None:
    """Create cash register tables and PostgreSQL enum types."""
    bind = op.get_bind()

    cash_session_status_enum.create(
        bind,
        checkfirst=True,
    )
    cash_transaction_type_enum.create(
        bind,
        checkfirst=True,
    )
    cash_transaction_source_enum.create(
        bind,
        checkfirst=True,
    )

    op.create_table(
        "cash_registers",
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
            "code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
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
            "char_length(trim(code)) > 0",
            name="ck_cash_registers_code_not_blank",
        ),
        sa.CheckConstraint(
            "char_length(trim(name)) > 0",
            name="ck_cash_registers_name_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "code",
            name="uq_cash_registers_company_code",
        ),
        sa.UniqueConstraint(
            "company_id",
            "name",
            name="uq_cash_registers_company_name",
        ),
    )

    op.create_index(
        op.f("ix_cash_registers_code"),
        "cash_registers",
        ["code"],
        unique=False,
    )
    op.create_index(
        "ix_cash_registers_company_active",
        "cash_registers",
        ["company_id", "is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_registers_company_id"),
        "cash_registers",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_registers_is_active"),
        "cash_registers",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_registers_name"),
        "cash_registers",
        ["name"],
        unique=False,
    )

    op.create_table(
        "cash_sessions",
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
            "cash_register_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "opened_by_user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "closed_by_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "status",
            cash_session_status_enum,
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "opening_amount",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "expected_amount",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            nullable=True,
        ),
        sa.Column(
            "counted_amount",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            nullable=True,
        ),
        sa.Column(
            "difference_amount",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            nullable=True,
        ),
        sa.Column(
            "opening_notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "closing_notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "closed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            """
            (
                status = 'open'
                AND closed_at IS NULL
                AND closed_by_user_id IS NULL
                AND expected_amount IS NULL
                AND counted_amount IS NULL
                AND difference_amount IS NULL
            )
            OR
            (
                status = 'closed'
                AND closed_at IS NOT NULL
                AND closed_by_user_id IS NOT NULL
                AND expected_amount IS NOT NULL
                AND counted_amount IS NOT NULL
                AND difference_amount IS NOT NULL
            )
            """,
            name="ck_cash_sessions_status_closing_data",
        ),
        sa.CheckConstraint(
            "counted_amount IS NULL OR counted_amount >= 0",
            name="ck_cash_sessions_counted_amount_non_negative",
        ),
        sa.CheckConstraint(
            "expected_amount IS NULL OR expected_amount >= 0",
            name="ck_cash_sessions_expected_amount_non_negative",
        ),
        sa.CheckConstraint(
            "opening_amount >= 0",
            name="ck_cash_sessions_opening_amount_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["cash_register_id"],
            ["cash_registers.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["closed_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["opened_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_cash_sessions_cash_register_id"),
        "cash_sessions",
        ["cash_register_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_sessions_closed_at"),
        "cash_sessions",
        ["closed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_sessions_closed_by_user_id"),
        "cash_sessions",
        ["closed_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_sessions_company_id"),
        "cash_sessions",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_cash_sessions_company_status_opened",
        "cash_sessions",
        ["company_id", "status", "opened_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_sessions_opened_at"),
        "cash_sessions",
        ["opened_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_sessions_opened_by_user_id"),
        "cash_sessions",
        ["opened_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_cash_sessions_register_status",
        "cash_sessions",
        ["cash_register_id", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_sessions_status"),
        "cash_sessions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "uq_cash_sessions_one_open_per_register",
        "cash_sessions",
        ["cash_register_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )

    op.create_table(
        "cash_transactions",
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
            "cash_session_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "transaction_type",
            cash_transaction_type_enum,
            nullable=False,
        ),
        sa.Column(
            "source",
            cash_transaction_source_enum,
            server_default="manual",
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            nullable=False,
        ),
        sa.Column(
            "reference",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="ck_cash_transactions_amount_positive",
        ),
        sa.CheckConstraint(
            "char_length(trim(description)) > 0",
            name="ck_cash_transactions_description_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["cash_session_id"],
            ["cash_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_cash_transactions_cash_session_id"),
        "cash_transactions",
        ["cash_session_id"],
        unique=False,
    )
    op.create_index(
        "ix_cash_transactions_company_created",
        "cash_transactions",
        ["company_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_transactions_company_id"),
        "cash_transactions",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_cash_transactions_company_type",
        "cash_transactions",
        ["company_id", "transaction_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_transactions_created_at"),
        "cash_transactions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_transactions_reference"),
        "cash_transactions",
        ["reference"],
        unique=False,
    )
    op.create_index(
        "ix_cash_transactions_session_created",
        "cash_transactions",
        ["cash_session_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_transactions_source"),
        "cash_transactions",
        ["source"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_transactions_transaction_type"),
        "cash_transactions",
        ["transaction_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cash_transactions_user_id"),
        "cash_transactions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop cash register tables and PostgreSQL enum types."""
    op.drop_index(
        op.f("ix_cash_transactions_user_id"),
        table_name="cash_transactions",
    )
    op.drop_index(
        op.f("ix_cash_transactions_transaction_type"),
        table_name="cash_transactions",
    )
    op.drop_index(
        op.f("ix_cash_transactions_source"),
        table_name="cash_transactions",
    )
    op.drop_index(
        "ix_cash_transactions_session_created",
        table_name="cash_transactions",
    )
    op.drop_index(
        op.f("ix_cash_transactions_reference"),
        table_name="cash_transactions",
    )
    op.drop_index(
        op.f("ix_cash_transactions_created_at"),
        table_name="cash_transactions",
    )
    op.drop_index(
        "ix_cash_transactions_company_type",
        table_name="cash_transactions",
    )
    op.drop_index(
        op.f("ix_cash_transactions_company_id"),
        table_name="cash_transactions",
    )
    op.drop_index(
        "ix_cash_transactions_company_created",
        table_name="cash_transactions",
    )
    op.drop_index(
        op.f("ix_cash_transactions_cash_session_id"),
        table_name="cash_transactions",
    )
    op.drop_table("cash_transactions")

    op.drop_index(
        "uq_cash_sessions_one_open_per_register",
        table_name="cash_sessions",
    )
    op.drop_index(
        op.f("ix_cash_sessions_status"),
        table_name="cash_sessions",
    )
    op.drop_index(
        "ix_cash_sessions_register_status",
        table_name="cash_sessions",
    )
    op.drop_index(
        op.f("ix_cash_sessions_opened_by_user_id"),
        table_name="cash_sessions",
    )
    op.drop_index(
        op.f("ix_cash_sessions_opened_at"),
        table_name="cash_sessions",
    )
    op.drop_index(
        "ix_cash_sessions_company_status_opened",
        table_name="cash_sessions",
    )
    op.drop_index(
        op.f("ix_cash_sessions_company_id"),
        table_name="cash_sessions",
    )
    op.drop_index(
        op.f("ix_cash_sessions_closed_by_user_id"),
        table_name="cash_sessions",
    )
    op.drop_index(
        op.f("ix_cash_sessions_closed_at"),
        table_name="cash_sessions",
    )
    op.drop_index(
        op.f("ix_cash_sessions_cash_register_id"),
        table_name="cash_sessions",
    )
    op.drop_table("cash_sessions")

    op.drop_index(
        op.f("ix_cash_registers_name"),
        table_name="cash_registers",
    )
    op.drop_index(
        op.f("ix_cash_registers_is_active"),
        table_name="cash_registers",
    )
    op.drop_index(
        op.f("ix_cash_registers_company_id"),
        table_name="cash_registers",
    )
    op.drop_index(
        "ix_cash_registers_company_active",
        table_name="cash_registers",
    )
    op.drop_index(
        op.f("ix_cash_registers_code"),
        table_name="cash_registers",
    )
    op.drop_table("cash_registers")

    bind = op.get_bind()

    cash_transaction_source_enum.drop(
        bind,
        checkfirst=True,
    )
    cash_transaction_type_enum.drop(
        bind,
        checkfirst=True,
    )
    cash_session_status_enum.drop(
        bind,
        checkfirst=True,
    )