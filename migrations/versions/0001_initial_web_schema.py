"""Create the initial web application schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_web_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_symbols",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(length=32), nullable=False, unique=True),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("instrument_type", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_market_symbols_symbol", "market_symbols", ["symbol"], unique=True)

    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol_id", sa.Integer(), sa.ForeignKey("market_symbols.id"), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(), nullable=False),
        sa.Column("open_price", sa.Float(), nullable=False),
        sa.Column("high_price", sa.Float(), nullable=False),
        sa.Column("low_price", sa.Float(), nullable=False),
        sa.Column("close_price", sa.Float(), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="seed"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_market_snapshots_symbol_id_snapshot_at",
        "market_snapshots",
        ["symbol_id", "snapshot_at"],
        unique=False,
    )
    op.create_index("ix_market_snapshots_snapshot_at", "market_snapshots", ["snapshot_at"], unique=False)

    op.create_table(
        "news_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol_id", sa.Integer(), sa.ForeignKey("market_symbols.id"), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="seed"),
        sa.Column("url", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_news_items_published_at", "news_items", ["published_at"], unique=False)
    op.create_index(
        "ix_news_items_symbol_id_published_at",
        "news_items",
        ["symbol_id", "published_at"],
        unique=False,
    )

    op.create_table(
        "decision_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol_id", sa.Integer(), sa.ForeignKey("market_symbols.id"), nullable=False),
        sa.Column("horizon", sa.String(length=32), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False, server_default="heuristic-v1"),
        sa.Column("close_price", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_decision_runs_created_at", "decision_runs", ["created_at"], unique=False)
    op.create_index(
        "ix_decision_runs_symbol_id_created_at",
        "decision_runs",
        ["symbol_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_decision_runs_symbol_id_created_at", table_name="decision_runs")
    op.drop_index("ix_decision_runs_created_at", table_name="decision_runs")
    op.drop_table("decision_runs")

    op.drop_index("ix_news_items_symbol_id_published_at", table_name="news_items")
    op.drop_index("ix_news_items_published_at", table_name="news_items")
    op.drop_table("news_items")

    op.drop_index("ix_market_snapshots_snapshot_at", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_symbol_id_snapshot_at", table_name="market_snapshots")
    op.drop_table("market_snapshots")

    op.drop_index("ix_market_symbols_symbol", table_name="market_symbols")
    op.drop_table("market_symbols")
