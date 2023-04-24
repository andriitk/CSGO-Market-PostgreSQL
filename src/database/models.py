from sqlalchemy.sql.schema import ForeignKey, Table, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import MetaData, Column, Integer, String, TIMESTAMP, cast, func
from datetime import datetime, timedelta

metadata = MetaData()

on_sale = Table(
    "csgo_market_on_sale",
    metadata,
    Column("market_id", String, index=True, nullable=False),
    Column("market_hash_name", String, nullable=False),
    Column("asset", String, nullable=True),
    Column("class_id", String, nullable=False),
    Column("instance_id", String, nullable=False),
    Column("price", String, nullable=False),
    Column("status", String, default="on_sale"),
    Column("created_at", TIMESTAMP, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
)

history = Table(
    "csgo_market_history",
    metadata,
    Column("market_hash_name", String, index=True, nullable=False),
    Column("time", JSONB, nullable=False),
    Column("price", JSONB, nullable=False),
    Column("status", String, default="need_check"),
    Column("created_at", TIMESTAMP, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
)

fourth_stage = Table(
    "csgo_market_fourth_stage",
    metadata,
    Column("market_id", String, index=True, nullable=False),
    Column("market_hash_name", String, nullable=False),
    Column("price", String, nullable=False),
    Column("status", String, default="found"),
    Column("asset", String, nullable=True),
    Column("class_id", String, nullable=True),
    Column("instance_id", String, nullable=True),
    Column("created_at", TIMESTAMP, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
)

Index('market_id_hash_idx', func.hash(cast(on_sale.c.market_id, String)), postgresql_using='hash')
Index('market_hash_name_idx', func.hash(cast(history.c.market_hash_name, String)), postgresql_using='hash')
Index('market_id_fourth_idx', func.hash(cast(fourth_stage.c.market_id, String)), postgresql_using='hash')
