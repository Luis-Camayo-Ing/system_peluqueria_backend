"""create appointment schedules and blocks

Revision ID: c1d41645fa90
Revises: 2e30d64dd388
Create Date: 2026-08-04 16:29:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c1d41645fa90"
down_revision: Union[str, Sequence[str], None] = "2e30d64dd388"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


schedule_block_type = postgresql.ENUM(
    "break",
    "day_off",
    "vacation",
    "permission",
    "other",
    name="schedule_block_type",
    create_type=False,
)


def upgrade() -> None:
    """Create professional schedule and availability tables."""
    bind = op.get_bind()

    schedule_block_type.create(
        bind,
        checkfirst=True,
    )

    op.create_table(
        "employee_schedule_blocks",
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
            "employee_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "block_type",
            schedule_block_type,
            server_default=sa.text(
                "'other'::schedule_block_type"
            ),
            nullable=False,
        ),
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
            "reason",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
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
            "end_at > start_at",
            name="ck_employee_schedule_blocks_time_range",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_employee_schedule_blocks_block_type"),
        "employee_schedule_blocks",
        ["block_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_schedule_blocks_company_id"),
        "employee_schedule_blocks",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_schedule_blocks_employee_id"),
        "employee_schedule_blocks",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_schedule_blocks_end_at"),
        "employee_schedule_blocks",
        ["end_at"],
        unique=False,
    )
    op.create_index(
        "ix_employee_schedule_blocks_lookup",
        "employee_schedule_blocks",
        [
            "company_id",
            "employee_id",
            "start_at",
            "end_at",
            "is_active",
        ],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_schedule_blocks_start_at"),
        "employee_schedule_blocks",
        ["start_at"],
        unique=False,
    )

    op.create_table(
        "employee_work_schedules",
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
            "employee_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "weekday",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "start_time",
            sa.Time(timezone=False),
            nullable=False,
        ),
        sa.Column(
            "end_time",
            sa.Time(timezone=False),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
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
            "end_time > start_time",
            name="ck_employee_work_schedules_time_range",
        ),
        sa.CheckConstraint(
            "weekday >= 0 AND weekday <= 6",
            name="ck_employee_work_schedules_weekday",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "employee_id",
            "weekday",
            "start_time",
            "end_time",
            name="uq_employee_work_schedules_period",
        ),
    )

    op.create_index(
        op.f("ix_employee_work_schedules_company_id"),
        "employee_work_schedules",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_work_schedules_employee_id"),
        "employee_work_schedules",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        "ix_employee_work_schedules_lookup",
        "employee_work_schedules",
        [
            "company_id",
            "employee_id",
            "weekday",
            "is_active",
        ],
        unique=False,
    )


def downgrade() -> None:
    """Remove professional schedule and availability tables."""
    bind = op.get_bind()

    op.drop_index(
        "ix_employee_work_schedules_lookup",
        table_name="employee_work_schedules",
    )
    op.drop_index(
        op.f("ix_employee_work_schedules_employee_id"),
        table_name="employee_work_schedules",
    )
    op.drop_index(
        op.f("ix_employee_work_schedules_company_id"),
        table_name="employee_work_schedules",
    )
    op.drop_table("employee_work_schedules")

    op.drop_index(
        op.f("ix_employee_schedule_blocks_start_at"),
        table_name="employee_schedule_blocks",
    )
    op.drop_index(
        "ix_employee_schedule_blocks_lookup",
        table_name="employee_schedule_blocks",
    )
    op.drop_index(
        op.f("ix_employee_schedule_blocks_end_at"),
        table_name="employee_schedule_blocks",
    )
    op.drop_index(
        op.f("ix_employee_schedule_blocks_employee_id"),
        table_name="employee_schedule_blocks",
    )
    op.drop_index(
        op.f("ix_employee_schedule_blocks_company_id"),
        table_name="employee_schedule_blocks",
    )
    op.drop_index(
        op.f("ix_employee_schedule_blocks_block_type"),
        table_name="employee_schedule_blocks",
    )
    op.drop_table("employee_schedule_blocks")

    schedule_block_type.drop(
        bind,
        checkfirst=True,
    )