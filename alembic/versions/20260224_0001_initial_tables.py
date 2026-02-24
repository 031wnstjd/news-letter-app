"""initial tables

Revision ID: 20260224_0001
Revises:
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260224_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("trust_tier", sa.String(length=8), nullable=False),
        sa.Column("fetch_type", sa.String(length=64), nullable=False),
        sa.Column("rss_url", sa.String(length=1024), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("lang", sa.String(length=16), nullable=True),
    )

    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=False, unique=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=1024), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_content_ref", sa.String(length=2048), nullable=True),
        sa.Column("lang", sa.String(length=16), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("hash", sa.String(length=128), nullable=True),
        sa.Column("dedup_group_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )

    op.create_table(
        "ranked_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("score_breakdown_json", sa.JSON(), nullable=True),
        sa.Column("day", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
    )

    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("tldr", sa.Text(), nullable=False),
        sa.Column("bullets_json", sa.JSON(), nullable=True),
        sa.Column("caveats", sa.Text(), nullable=True),
        sa.Column("model_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
    )

    op.create_table(
        "subscribers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("preferences_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unsub_token", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("day", sa.String(length=16), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("html_body_ref", sa.String(length=2048), nullable=True),
        sa.Column("text_body_ref", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("subscriber_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bounce_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("complaint_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("open_count", sa.Integer(), nullable=False),
        sa.Column("click_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["subscriber_id"], ["subscribers.id"]),
    )


def downgrade() -> None:
    op.drop_table("deliveries")
    op.drop_table("campaigns")
    op.drop_table("subscribers")
    op.drop_table("summaries")
    op.drop_table("ranked_items")
    op.drop_table("items")
    op.drop_table("sources")
