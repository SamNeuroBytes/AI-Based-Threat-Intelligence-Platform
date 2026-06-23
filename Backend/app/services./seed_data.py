"""
Seed the database with realistic sample threat indicators.

Useful for:
  - Local demos without relying on live feed availability
  - Giving the ML model enough data to train on immediately
  - Screenshot/portfolio purposes

Run with: python -m app.services.seed_data
"""

import random
import json
import datetime
from app.models.db import SessionLocal, Indicator, init_db

random.seed(42)

MALICIOUS_DOMAINS = [
    "secure-login-update.xyz", "account-verify-bank.top", "free-bonus-click.tk",
    "paypa1-confirm.ml", "appleid-verify-secure.ga", "urgent-payment-alert.cf",
    "wallet-recovery-support.work", "microsoft-update-portal.loan",
    "amaz0n-account-check.xyz", "netflix-billing-update.top",
]

NORMAL_DOMAINS = [
    "github.com", "google.com", "wikipedia.org", "cloudflare.com",
    "stackoverflow.com", "python.org", "openai.com", "microsoft.com",
]

MALWARE_FAMILIES = ["Emotet", "AgentTesla", "RedLineStealer", "Qakbot", "Cobalt Strike", "Lokibot"]
THREAT_TYPES_URL = ["malware_download", "phishing", "c2"]

SOURCES = ["URLhaus", "ThreatFox", "AbuseIPDB"]


def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def random_hash():
    return "".join(random.choices("abcdef0123456789", k=64))


def build_sample_indicators(n=180):
    samples = []
    now = datetime.datetime.utcnow()

    for i in range(n):
        days_ago = random.randint(0, 6)
        seen = now - datetime.timedelta(days=days_ago, hours=random.randint(0, 23))

        roll = random.random()
        if roll < 0.35:
            ioc_type = "url"
            domain = random.choice(MALICIOUS_DOMAINS)
            value = f"http://{domain}/{random.choice(['login', 'verify', 'update', 'secure'])}.php?id={random.randint(1000,9999)}"
            source = "URLhaus"
            threat_type = random.choice(THREAT_TYPES_URL)
            confidence = random.uniform(60, 100)
        elif roll < 0.55:
            ioc_type = "domain"
            value = random.choice(MALICIOUS_DOMAINS + NORMAL_DOMAINS)
            source = "ThreatFox"
            threat_type = random.choice(MALWARE_FAMILIES)
            confidence = random.uniform(40, 95)
        elif roll < 0.85:
            ioc_type = "ip"
            value = random_ip()
            source = "AbuseIPDB"
            threat_type = random.choice(["botnet", "brute_force", "spam", "scanning"])
            confidence = random.uniform(30, 100)
        else:
            ioc_type = "hash"
            value = random_hash()
            source = "ThreatFox"
            threat_type = random.choice(MALWARE_FAMILIES)
            confidence = random.uniform(70, 100)

        if confidence >= 90:
            severity = "critical"
        elif confidence >= 70:
            severity = "high"
        elif confidence >= 40:
            severity = "medium"
        else:
            severity = "low"

        samples.append({
            "ioc_type": ioc_type,
            "value": value,
            "source": source,
            "threat_type": threat_type,
            "confidence": round(confidence, 2),
            "severity": severity,
            "raw_data": json.dumps({"sample": True}),
            "first_seen": seen,
            "last_seen": seen,
        })
    return samples


def seed():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Indicator).count()
        if existing > 0:
            print(f"DB already has {existing} indicators, skipping seed (delete threatintel.db to reseed).")
            return
        for item in build_sample_indicators():
            db.add(Indicator(**item))
        db.commit()
        print(f"Seeded {db.query(Indicator).count()} sample indicators.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
