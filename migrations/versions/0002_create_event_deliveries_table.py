"""Create the event deliveries table."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_deliveries",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("destination", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="pending", nullable=False),
        sa.Column(
            "attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("event_id", "destination", name="pk_event_deliveries"),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.event_id"],
            name="fk_event_deliveries_event_id",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'delivered', 'failed')",
            name="ck_event_deliveries_status",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0", name="ck_event_deliveries_attempt_count"
        ),
        sa.CheckConstraint(
            "(status = 'pending') = (next_attempt_at IS NOT NULL)",
            name="ck_event_deliveries_next_attempt_at",
        ),
    )
    op.create_index(
        "ix_event_deliveries_pending_next_attempt_at",
        "event_deliveries",
        ["next_attempt_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_table("event_deliveries")
