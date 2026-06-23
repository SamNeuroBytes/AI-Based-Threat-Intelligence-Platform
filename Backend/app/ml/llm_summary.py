"""
LLM-powered summarization for high-severity indicators.

Uses the Anthropic API (set ANTHROPIC_API_KEY env var) to turn a raw
indicator + ML score into a short, human-readable alert summary that
a security analyst could read directly. Falls back to a template-based
summary if no API key is configured, so the platform still works
out-of-the-box.
"""

import os
import requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _template_summary(indicator) -> str:
    return (
        f"A {indicator.severity}-severity {indicator.ioc_type} indicator "
        f"({indicator.value}) was reported by {indicator.source} with "
        f"{indicator.confidence:.0f}% confidence"
        + (f" and flagged as anomalous by the ML model (score "
           f"{indicator.ml_score:.1f})." if indicator.ml_score else ".")
        + f" Associated threat type: {indicator.threat_type or 'unknown'}. "
        "Recommended action: review and consider blocking if confirmed malicious."
    )


def generate_summary(indicator) -> str:
    if not ANTHROPIC_API_KEY:
        return _template_summary(indicator)

    prompt = (
        "You are a security analyst assistant. Write a 2-3 sentence plain "
        "English summary of this threat indicator for a SOC dashboard alert. "
        "Be concise, factual, and suggest a next action.\n\n"
        f"IOC type: {indicator.ioc_type}\n"
        f"Value: {indicator.value}\n"
        f"Source: {indicator.source}\n"
        f"Threat type: {indicator.threat_type}\n"
        f"Confidence: {indicator.confidence}\n"
        f"Severity: {indicator.severity}\n"
        f"ML anomaly score: {indicator.ml_score}\n"
    )

    try:
        resp = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return " ".join(text_blocks).strip() or _template_summary(indicator)
    except Exception as e:
        print(f"[LLM] summary generation failed: {e}")
        return _template_summary(indicator)
