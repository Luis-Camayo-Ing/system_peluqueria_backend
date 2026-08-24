"""create appointment history and reminders

Revision ID: d9f2a4b6c8e1
Revises: c1d41645fa90
Create Date: 2026-08-04 22:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "d9f2a4b6c8e1"
down_revision: str | Sequence[str] | None = "c1d41645fa90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


appointment_status = postgresql.ENUM(
    "scheduled",
    "confirmed",
    "in_progress",
    "completed",
    "cancelled",
    "no_show",
    name="appointment_status",
    create_type=False,
)

appointment_history_type = postgresql.ENUM(
    "rescheduled",
    "cancelled",
    name="appointment_history_type",
    create_type=False,
)

reminder_channel = postgresql.ENUM(
    "internal",
    "email",
    "whatsapp",
    name="reminder_channel",
    create_type=False,
)

appointment_reminder_status = postgresql.ENUM(
    "pending",
    "sent",
    "failed",
    "cancelled",
    name="appointment_reminder_status",
    create_type=False,
)


def upgrade() -> None:
    """Create appointment history and reminder queue."""
    bind = op.get_bind()

    appointment_history_type.create(
        bind,
        checkfirst=True,
    )
    reminder_channel.create(
        bind,
        checkfirst=True,
    )
    appointment_reminder_status.create(
        bind,
        checkfirst=True,
    )

    op.create_table(
        "appointment_histories",
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
            "appointment_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "changed_by_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "change_type",
            appointment_history_type,
            nullable=False,
        ),
        sa.Column(
            "previous_start_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "previous_end_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "new_start_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "new_end_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "previous_status",
            appointment_status,
            nullable=True,
        ),
        sa.Column(
            "new_status",
            appointment_status,
            nullable=True,
        ),
        sa.Column(
            "reason",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_appointment_histories_appointment_id"),
        "appointment_histories",
        ["appointment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_histories_change_type"),
        "appointment_histories",
        ["change_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_histories_changed_by_user_id"),
        "appointment_histories",
        ["changed_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_histories_company_id"),
        "appointment_histories",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_appointment_histories_lookup",
        "appointment_histories",
        [
            "company_id",
            "appointment_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_table(
        "appointment_reminders",
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
            "appointment_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "channel",
            reminder_channel,
            server_default=sa.text(
                "'internal'::reminder_channel"
            ),
            nullable=False,
        ),
        sa.Column(
            "remind_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            appointment_reminder_status,
            server_default=sa.text(
                "'pending'::appointment_reminder_status"
            ),
            nullable=False,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "failure_message",
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
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "appointment_id",
            "channel",
            "remind_at",
            name="uq_appointment_reminders_schedule",
        ),
    )

    op.create_index(
        op.f("ix_appointment_reminders_appointment_id"),
        "appointment_reminders",
        ["appointment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_reminders_channel"),
        "appointment_reminders",
        ["channel"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_reminders_company_id"),
        "appointment_reminders",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_reminders_created_by_user_id"),
        "appointment_reminders",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_appointment_reminders_due",
        "appointment_reminders",
        [
            "company_id",
            "status",
            "remind_at",
        ],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_reminders_remind_at"),
        "appointment_reminders",
        ["remind_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_reminders_status"),
        "appointment_reminders",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Remove appointment history and reminder queue."""
    bind = op.get_bind()

    op.drop_index(
        op.f("ix_appointment_reminders_status"),
        table_name="appointment_reminders",
    )
    op.drop_index(
        op.f("ix_appointment_reminders_remind_at"),
        table_name="appointment_reminders",
    )
    op.drop_index(
        "ix_appointment_reminders_due",
        table_name="appointment_reminders",
    )
    op.drop_index(
        op.f("ix_appointment_reminders_created_by_user_id"),
        table_name="appointment_reminders",
    )
    op.drop_index(
        op.f("ix_appointment_reminders_company_id"),
        table_name="appointment_reminders",
    )
    op.drop_index(
        op.f("ix_appointment_reminders_channel"),
        table_name="appointment_reminders",
    )
    op.drop_index(
        op.f("ix_appointment_reminders_appointment_id"),
        table_name="appointment_reminders",
    )
    op.drop_table("appointment_reminders")

    op.drop_index(
        "ix_appointment_histories_lookup",
        table_name="appointment_histories",
    )
    op.drop_index(
        op.f("ix_appointment_histories_company_id"),
        table_name="appointment_histories",
    )
    op.drop_index(
        op.f("ix_appointment_histories_changed_by_user_id"),
        table_name="appointment_histories",
    )
    op.drop_index(
        op.f("ix_appointment_histories_change_type"),
        table_name="appointment_histories",
    )
    op.drop_index(
        op.f("ix_appointment_histories_appointment_id"),
        table_name="appointment_histories",
    )
    op.drop_table("appointment_histories")

    appointment_reminder_status.drop(
        bind,
        checkfirst=True,
    )
    reminder_channel.drop(
        bind,
        checkfirst=True,
    )
    appointment_history_type.drop(
        bind,
        checkfirst=True,
    )