from __future__ import annotations

from typing import Any


def calculate_seo_score(data: dict[str, Any]) -> int:
    """
    Calculate a score out of 100 using four SEO checks.

    Scoring (25 points each):
    - Title length between 50 and 60 characters
    - Meta description exists
    - Exactly one H1 tag
    - No images missing alt text
    """
    score = 0

    meta = data.get("meta_tags", {})
    headers = data.get("headers", {})
    images = data.get("images", {})

    title_length = meta.get("title_length", 0)
    if 50 <= title_length <= 60:
        score += 25

    if meta.get("meta_description", "").strip():
        score += 25

    if headers.get("h1_count", 0) == 1:
        score += 25

    if images.get("images_missing_alt", 0) == 0:
        score += 25

    return int(score)


def generate_recommendations(data: dict[str, Any]) -> list[str]:
    """Generate actionable SEO recommendations based on analysis data."""
    recommendations: list[str] = []

    meta = data.get("meta_tags", {})
    headers = data.get("headers", {})
    images = data.get("images", {})

    title_length = meta.get("title_length", 0)
    if not 50 <= title_length <= 60:
        recommendations.append("Improve title length to 50-60 characters.")

    if not meta.get("meta_description", "").strip():
        recommendations.append("Add a meta description for better search snippets.")

    if headers.get("h1_count", 0) != 1:
        recommendations.append("Fix H1 count so the page has exactly one H1 tag.")

    if images.get("images_missing_alt", 0) > 0:
        recommendations.append("Add alt text to all images missing it.")

    return recommendations


def get_score_color(score: int) -> str:
    """Return a display color based on score thresholds."""
    if score > 80:
        return "green"
    if 50 <= score <= 80:
        return "orange"
    return "red"
