"""delivery idempotency

Revision ID: 20260224_0002
Revises: 20260224_0001
Create Date: 2026-02-24
"""

from alembic import op


revision = "20260224_0002"
down_revision = "20260224_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_delivery_campaign_subscriber",
        "deliveries",
        ["campaign_id", "subscriber_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_delivery_campaign_subscriber", "deliveries", type_="unique")
