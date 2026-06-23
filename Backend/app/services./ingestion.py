"""
Ingestion service: pulls real, live threat intelligence data from free
public sources and normalizes it into the Indicator model.

Sources currently implemented:
  1. URLhaus (abuse.ch)   - free, no API key required, recent malicious URLs
  2. ThreatFox (abuse.ch) - free, no API key required, recent IOCs (IP/domain/hash)
  3. AbuseIPDB            - optional, requires free API key (set ABUSEIPDB_KEY env var)

Each source returns a list of normalized dicts which are upserted into the DB.
"""

import os
import requests
import datetime
import json
from app.models.db import SessionLocal, Indicator

URLHAUS_RECENT_URL = "https://urlhaus-api.abuse.ch/v1/urls/recent/"
THREATFOX_API_URL = "https://threatfox-api.abuse.ch/api/v1/"
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/blacklist"

ABUSEIPDB_KEY = os.getenv("ABUSEIPDB_KEY", "")

# abuse.ch endpoints reject requests without a browser-like User-Agent
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ThreatIntelPlatform/1.0; +https://github.com/)",
    "Accept": "application/json",
}


def _severity_from_confidence(confidence: float) -> str:
    if confidence >= 90:
        return "critical"
    if confidence >= 70:
        return "high"
    if confidence >= 40:
        return "medium"
    return "low"


def fetch_urlhaus():
    """Fetch recently submitted malicious URLs from URLhaus."""
    results = []
    try:
        resp = requests.get(URLHAUS_RECENT_URL, headers=DEFAULT_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("query_status") != "ok":
            return results
        for entry in data.get("urls", [])[:100]:
            confidence = 75.0  # URLhaus entries are confirmed malicious
            results.append({
                "ioc_type": "url",
                "value": entry.get("url", ""),
                "source": "URLhaus",
                "threat_type": entry.get("threat", "malware"),
                "confidence": confidence,
                "severity": _severity_from_confidence(confidence),
                "raw_data": json.dumps(entry),
            })
    except Exception as e:
        print(f"[URLhaus] fetch error: {e}")
    return results


def fetch_threatfox():
    """Fetch recent IOCs (IPs, domains, hashes) from ThreatFox."""
    results = []
    try:
        resp = requests.post(
            THREATFOX_API_URL,
            json={"query": "get_iocs", "days": 1},
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("query_status") != "ok":
            return results
        for entry in data.get("data", [])[:100]:
            ioc_type_raw = entry.get("ioc_type", "").lower()
            type_map = {
                "ip:port": "ip",
                "domain": "domain",
                "url": "url",
                "md5_hash": "hash",
                "sha256_hash": "hash",
            }
            ioc_type = type_map.get(ioc_type_raw, "other")
            confidence = float(entry.get("confidence_level", 50))
            value = entry.get("ioc", "")
            # strip port from ip:port style values
            if ioc_type == "ip" and ":" in value:
                value = value.split(":")[0]
            results.append({
                "ioc_type": ioc_type,
                "value": value,
                "source": "ThreatFox",
                "threat_type": entry.get("malware_printable", entry.get("threat_type", "unknown")),
                "confidence": confidence,
                "severity": _severity_from_confidence(confidence),
                "raw_data": json.dumps(entry),
            })
    except Exception as e:
        print(f"[ThreatFox] fetch error: {e}")
    return results


def fetch_abuseipdb():
    """Fetch blacklisted IPs from AbuseIPDB (requires free API key)."""
    results = []
    if not ABUSEIPDB_KEY:
        return results
    try:
        headers = {"Key": ABUSEIPDB_KEY, "Accept": "application/json"}
        resp = requests.get(
            ABUSEIPDB_URL,
            headers=headers,
            params={"confidenceMinimum": 50, "limit": 100},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for entry in data.get("data", []):
            confidence = float(entry.get("abuseConfidenceScore", 50))
            results.append({
                "ioc_type": "ip",
                "value": entry.get("ipAddress", ""),
                "source": "AbuseIPDB",
                "threat_type": "abuse",
                "confidence": confidence,
                "severity": _severity_from_confidence(confidence),
                "raw_data": json.dumps(entry),
            })
    except Exception as e:
        print(f"[AbuseIPDB] fetch error: {e}")
    return results


def run_ingestion():
    """Run all configured fetchers and upsert results into the database."""
    db = SessionLocal()
    new_count = 0
    updated_count = 0
    try:
        all_results = []
        all_results.extend(fetch_urlhaus())
        all_results.extend(fetch_threatfox())
        all_results.extend(fetch_abuseipdb())

        for item in all_results:
            if not item["value"]:
                continue
            existing = (
                db.query(Indicator)
                .filter(
                    Indicator.value == item["value"],
                    Indicator.source == item["source"],
                )
                .first()
            )
            if existing:
                existing.last_seen = datetime.datetime.utcnow()
                existing.confidence = item["confidence"]
                existing.severity = item["severity"]
                updated_count += 1
            else:
                db.add(Indicator(**item))
                new_count += 1
        db.commit()
    finally:
        db.close()

    print(f"[Ingestion] new={new_count} updated={updated_count}")
    return {"new": new_count, "updated": updated_count}


if __name__ == "__main__":
    run_ingestion()
