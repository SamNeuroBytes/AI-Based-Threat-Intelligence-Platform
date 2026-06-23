from pydantic import BaseModel
from typing import Optional
import datetime


class IndicatorOut(BaseModel):
    id: int
    ioc_type: str
    value: str
    source: str
    threat_type: Optional[str] = None
    confidence: float
    severity: str
    ml_score: Optional[float] = None
    ml_label: Optional[str] = None
    first_seen: datetime.datetime
    last_seen: datetime.datetime

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    indicator_id: int
    title: str
    summary: str
    severity: str
    created_at: datetime.datetime
    acknowledged: int

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_indicators: int
    total_alerts: int
    by_severity: dict
    by_source: dict
    by_type: dict
    recent_trend: list
