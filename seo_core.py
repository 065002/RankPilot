from __future__ import annotations

import re
from collections import Counter
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# ---------------- STOPWORDS ---------------- #
STOPWORDS = {
    "the", "is", "in", "and", "to", "of", "for", "on", "with", "as",
    "by", "at", "from", "that", "this", "it", "an", "be", "are",
    "was", "were", "or", "if", "but", "not", "we", "you", "they",
    "he", "she", "his", "her", "their", "our", "can", "will", "just",
    "about", "into", "than", "then", "them", "so", "no", "yes"
}


class SEOTool:
    """Perform SEO analysis on a single webpage URL."""

    def __init__(self, url: str, timeout: int = 10) -> None:
        self.url = self._normalize_url(url)
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.response = None
        self.html_content = ""
        self.soup = BeautifulSoup("", "html.parser")
        self._fetch_and_parse()

    @staticmethod
    def _normalize_url(url: str) -> str:
        clean_url = url.strip()
        if not clean_url:
            raise ValueError("URL cannot be empty.")
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"
        elif clean_url.startswith("http://"):
            clean_url = clean_url.replace("http://", "https://", 1)
        return clean_url

    def _fetch_and_parse(self) -> None:
        try:
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            self.response = response
            self.html_content = response.text
            self.soup = BeautifulSoup(self.html_content, "html.parser")
        except requests.RequestException:
            self.response = None
            self.html_content = ""
            self.soup = BeautifulSoup("", "html.parser")

    # ---------------- META TAGS ---------------- #
    def check_meta_tags(self) -> dict[str, Any]:
        title_tag = self.soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        desc_tag = self.soup.find("meta", attrs={"name": "description"})
        if not desc_tag:
            desc_tag = self.soup.find("meta", attrs={"property": "og:description"})

        meta_description = (
            desc_tag.get("content", "").strip()
            if desc_tag and desc_tag.get("content")
            else ""
        )

        return {
            "title": title,
            "title_length": len(title),
            "meta_description": meta_description,
        }

    # ---------------- HEADERS ---------------- #
    def check_headers(self) -> dict[str, int]:
        return {
            "h1_count": len(self.soup.find_all("h1")),
            "h2_count": len(self.soup.find_all("h2")),
            "h3_count": len(self.soup.find_all("h3")),
        }

    # ---------------- IMAGES ---------------- #
    def check_images(self) -> dict[str, int]:
        images = self.soup.find_all("img")
        missing_alt = sum(1 for image in images if not image.get("alt", "").strip())
        return {
            "total_images": len(images),
            "images_missing_alt": missing_alt,
        }

    # ---------------- LINKS ---------------- #
    def check_links(self) -> dict[str, int]:
        internal_links = 0
        external_links = 0
        base_domain = urlparse(self.url).netloc.lower()

        for link in self.soup.find_all("a", href=True):
            href = link["href"].strip()

            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            parsed = urlparse(href)

            if not parsed.netloc:
                internal_links += 1
                continue

            if parsed.netloc.lower() == base_domain:
                internal_links += 1
            else:
                external_links += 1

        return {
            "internal_links": internal_links,
            "external_links": external_links,
        }

    # ---------------- KEYWORD DENSITY (UPDATED) ---------------- #
    def keyword_density(self) -> dict[str, Any]:
        for script_or_style in self.soup(["script", "style", "noscript"]):
            script_or_style.extract()

        text = self.soup.get_text(separator=" ", strip=True).lower()

        words = re.findall(r"\b[a-z0-9]{3,}\b", text)

        # Remove stopwords + numbers + noise
        filtered_words = [
            word for word in words
            if word not in STOPWORDS
            and not word.isdigit()
            and len(word) > 3
        ]

        top_keywords = Counter(filtered_words).most_common(10)

        return {
            "top_keywords": [
                {"keyword": keyword, "frequency": frequency}
                for keyword, frequency in top_keywords
            ]
        }

    # ---------------- PAGE SPEED ---------------- #
    def check_page_speed(self) -> dict[str, float | int]:
        page_size_kb = round(len(self.html_content.encode("utf-8")) / 1024, 2)

        number_of_scripts = len(self.soup.find_all("script"))

        number_of_css = len(
            self.soup.find_all(
                "link",
                attrs={
                    "rel": lambda rel: rel
                    and "stylesheet" in [item.lower() for item in rel]
                },
            )
        )

        return {
            "page_size_kb": page_size_kb,
            "number_of_scripts": number_of_scripts,
            "number_of_css": number_of_css,
        }

    # ---------------- FINAL OUTPUT ---------------- #
    def run_full_analysis(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "meta_tags": self.check_meta_tags(),
            "headers": self.check_headers(),
            "images": self.check_images(),
            "links": self.check_links(),
            "keyword_density": self.keyword_density(),
            "page_speed": self.check_page_speed(),
        }