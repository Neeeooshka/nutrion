import sqlalchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from backend.db import database

metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("telegram_id", String, unique=True, nullable=False),
    Column("username", String),
    Column("gender", String),
    Column("age", Integer),
    Column("weight", Float),
    Column("height", Float),
    Column("goal", String),
    Column("created_at", DateTime, server_default=func.now())
)
