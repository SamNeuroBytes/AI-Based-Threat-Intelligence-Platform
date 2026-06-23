from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

DATABASE_URL = "sqlite:///./threatintel.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Indicator(Base):
    """A single threat indicator (IP, domain, URL, hash) collected from a feed."""
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    ioc_type = Column(String, index=True)        # ip, domain, url, hash
    value = Column(String, index=True)           # the actual indicator value
    source = Column(String, index=True)          # which feed it came from
    threat_type = Column(String, nullable=True)  # malware, phishing, botnet, etc.
    confidence = Column(Float, default=0.0)      # 0-100 score from source
    severity = Column(String, default="unknown") # low, medium, high, critical
    ml_score = Column(Float, nullable=True)      # anomaly score from ML model
    ml_label = Column(String, nullable=True)     # ML predicted label
    raw_data = Column(Text, nullable=True)       # original JSON payload
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)


class Alert(Base):
    """Generated when a high-severity indicator is detected."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, index=True)
    title = Column(String)
    summary = Column(Text)          # human-readable / LLM-generated summary
    severity = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    acknowledged = Column(Integer, default=0)  # 0/1 boolean


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
