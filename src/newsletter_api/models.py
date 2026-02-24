from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(255), index=True)
    trust_tier: Mapped[str] = mapped_column(String(8), default="T2")
    fetch_type: Mapped[str] = mapped_column(String(64), default="rss")
    rss_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    lang: Mapped[str | None] = mapped_column(String(16), nullable=True)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    canonical_url: Mapped[str] = mapped_column(String(2048), index=True)
    title: Mapped[str] = mapped_column(String(1024))
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_content_ref: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    lang: Mapped[str | None] = mapped_column(String(16), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    keywords: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dedup_group_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class RankedItem(Base):
    __tablename__ = "ranked_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    score_breakdown_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    day: Mapped[str] = mapped_column(String(16), index=True)


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), unique=True)
    tldr: Mapped[str] = mapped_column(Text)
    bullets_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    caveats: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    preferences_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unsub_token: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[str] = mapped_column(String(16), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    html_body_ref: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    text_body_ref: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Delivery(Base):
    __tablename__ = "deliveries"
    __table_args__ = (
        UniqueConstraint("campaign_id", "subscriber_id", name="uq_delivery_campaign_subscriber"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    subscriber_id: Mapped[int] = mapped_column(ForeignKey("subscribers.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bounce_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    complaint_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
