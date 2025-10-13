# backend/models.py
import sqlalchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
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

user_memory = sqlalchemy.Table(
    "user_memory",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("chat_id", String, nullable=False),
    Column("user_id", String, nullable=False),
    Column("user_message", Text, nullable=False),
    Column("ai_response", Text, nullable=False),
    Column("created_at", DateTime, server_default=func.now())
)
