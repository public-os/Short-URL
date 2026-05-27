from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Railway uses /data for persistent storage
if os.getenv("RAILWAY_ENVIRONMENT"):
    DATABASE_URL = "sqlite:////data/shortener.db"
else:
    DATABASE_URL = "sqlite:///./shortener.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()