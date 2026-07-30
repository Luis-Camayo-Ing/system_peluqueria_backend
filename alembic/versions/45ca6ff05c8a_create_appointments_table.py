"""create appointments table

Revision ID: 45ca6ff05c8a
Revises: 68cfe639f792
Create Date: 2026-07-30 22:31:37.562339
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "45ca6ff05c8a"
down_revision: Union[str, Sequence[str], None] = "68cfe639f792"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


appointment_status_enum = sa.Enum(
    "scheduled",
    "confirmed",
    "in_progress",
    "completed",
    "cancelled",
    "no_show",
    name="appointment_status",
)


def upgrade() -> None:
    """Create appointments table."""

    op.create_table(
        "appointments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("service_id", sa.UUID(), nullable=False),
        sa.Column(
            "start_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "end_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            appointment_status_enum,
            server_default="scheduled",
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "cancellation_reason",
            sa.String(length=500),
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
            "end_at > start_at",
            name="ck_appointments_end_after_start",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_appointments_company_id"),
        "appointments",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_customer_id"),
        "appointments",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_employee_id"),
        "appointments",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_end_at"),
        "appointments",
        ["end_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_service_id"),
        "appointments",
        ["service_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_start_at"),
        "appointments",
        ["start_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_status"),
        "appointments",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Remove appointments table and its PostgreSQL enum."""

    op.drop_index(
        op.f("ix_appointments_status"),
        table_name="appointments",
    )
    op.drop_index(
        op.f("ix_appointments_start_at"),
        table_name="appointments",
    )
    op.drop_index(
        op.f("ix_appointments_service_id"),
        table_name="appointments",
    )
    op.drop_index(
        op.f("ix_appointments_end_at"),
        table_name="appointments",
    )
    op.drop_index(
        op.f("ix_appointments_employee_id"),
        table_name="appointments",
    )
    op.drop_index(
        op.f("ix_appointments_customer_id"),
        table_name="appointments",
    )
    op.drop_index(
        op.f("ix_appointments_company_id"),
        table_name="appointments",
    )

    op.drop_table("appointments")

    appointment_status_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )