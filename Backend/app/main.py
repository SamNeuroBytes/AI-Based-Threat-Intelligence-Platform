from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import datetime

from app.models.db import init_db, get_db, Indicator, Alert
from app.models.schemas import IndicatorOut, AlertOut, StatsOut
from app.services.ingestion import run_ingestion
from app.ml.model import retrain_and_score
from app.ml.llm_summary import generate_summary
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI(title="AI-Based Threat Intelligence Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# ---------------------------------------------------------------------------
# Scheduled background jobs: pull fresh data + retrain ML hourly
# ---------------------------------------------------------------------------
def scheduled_job():
    from app.models.db import SessionLocal
    run_ingestion()
    db = SessionLocal()
    try:
        retrain_and_score(db, Indicator)
        create_alerts_for_high_severity(db)
    finally:
        db.close()


def create_alerts_for_high_severity(db: Session):
    high_sev = (
        db.query(Indicator)
        .filter(Indicator.severity.in_(["high", "critical"]))
        .all()
    )
    for ind in high_sev:
        exists = db.query(Alert).filter(Alert.indicator_id == ind.id).first()
        if exists:
            continue
        summary = generate_summary(ind)
        alert = Alert(
            indicator_id=ind.id,
            title=f"{ind.severity.upper()} threat: {ind.ioc_type} from {ind.source}",
            summary=summary,
            severity=ind.severity,
        )
        db.add(alert)
    db.commit()


scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_job, "interval", hours=1, id="ingest_and_score")


@app.on_event("startup")
def startup_event():
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "service": "AI-Based Threat Intelligence Platform"}


@app.post("/api/ingest")
def trigger_ingestion(background_tasks: BackgroundTasks):
    """Manually trigger a data ingestion + ML scoring + alert generation cycle."""
    background_tasks.add_task(scheduled_job)
    return {"message": "Ingestion started in background"}


@app.get("/api/indicators", response_model=List[IndicatorOut])
def list_indicators(
    severity: Optional[str] = None,
    ioc_type: Optional[str] = None,
    source: Optional[str] = None,
    ml_label: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Indicator)
    if severity:
        query = query.filter(Indicator.severity == severity)
    if ioc_type:
        query = query.filter(Indicator.ioc_type == ioc_type)
    if source:
        query = query.filter(Indicator.source == source)
    if ml_label:
        query = query.filter(Indicator.ml_label == ml_label)
    if search:
        query = query.filter(Indicator.value.contains(search))
    query = query.order_by(Indicator.last_seen.desc())
    return query.offset(offset).limit(limit).all()


@app.get("/api/indicators/{indicator_id}", response_model=IndicatorOut)
def get_indicator(indicator_id: int, db: Session = Depends(get_db)):
    ind = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    if not ind:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return ind


@app.get("/api/alerts", response_model=List[AlertOut])
def list_alerts(
    acknowledged: Optional[int] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Alert)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    if severity:
        query = query.filter(Alert.severity == severity)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = 1
    db.commit()
    return {"message": "Alert acknowledged"}


@app.get("/api/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    total_indicators = db.query(Indicator).count()
    total_alerts = db.query(Alert).count()

    by_severity = dict(
        db.query(Indicator.severity, func.count(Indicator.id))
        .group_by(Indicator.severity)
        .all()
    )
    by_source = dict(
        db.query(Indicator.source, func.count(Indicator.id))
        .group_by(Indicator.source)
        .all()
    )
    by_type = dict(
        db.query(Indicator.ioc_type, func.count(Indicator.id))
        .group_by(Indicator.ioc_type)
        .all()
    )

    # 7-day trend of new indicators
    trend = []
    today = datetime.datetime.utcnow().date()
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        count = (
            db.query(Indicator)
            .filter(func.date(Indicator.first_seen) == day.isoformat())
            .count()
        )
        trend.append({"date": day.isoformat(), "count": count})

    return StatsOut(
        total_indicators=total_indicators,
        total_alerts=total_alerts,
        by_severity=by_severity,
        by_source=by_source,
        by_type=by_type,
        recent_trend=trend,
    )


@app.post("/api/retrain")
def retrain(db: Session = Depends(get_db)):
    """Manually retrain the ML anomaly detection model on current data."""
    count = retrain_and_score(db, Indicator)
    return {"message": f"Model retrained and scored {count} indicators"}
