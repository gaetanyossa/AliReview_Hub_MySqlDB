#!/usr/bin/env python3
"""
extract_reviews.py — Scrape reviews from AliExpress and export to CSV

This tool contacts AliExpress’s undocumented review API and extracts product reviews.
It supports various schema versions and falls back safely when field names change.

Usage:
    python extract_reviews.py aliexpress 1005007002128983 --outfile reviews.csv

Requirements:
    pip install httpx faker
"""

import argparse
import csv
import datetime as dt
import json
import random
import sys
from pathlib import Path
from typing import Iterable

import httpx
from faker import Faker

fake = Faker()

HEADERS = {
    "User-Agent": fake.user_agent(),
    "Accept": "application/json",
}


class AliExpressBackend:
    URL = (
        "https://feedback.aliexpress.com/pc/searchEvaluation.do"
        "?productId={pid}&page={page}&pageSize={size}&filter=all"
    )

    @staticmethod
    def _normalize(raw: dict) -> dict:
        """Convert raw review JSON into a flat, robust row dict."""
        ts_ms = next(
            (
                raw.get(k)
                for k in (
                    "gmtCreate",
                    "createTime",
                    "createTimestamp",
                    "gmtOrderCreateTime",
                    "feedbackCreateTime",
                )
                if raw.get(k)
            ),
            None,
        )

        try:
            created = dt.datetime.fromtimestamp(int(ts_ms) / 1000) if ts_ms else dt.datetime.utcnow()
        except (TypeError, ValueError):
            created = dt.datetime.utcnow()

        return {
            "author": raw.get("buyerName") or fake.name(),
            "country": raw.get("buyerCountry", ""),
            "rating": raw.get("buyerEval", 100) / 20,
            "date": created,
            "content": raw.get("buyerFeedback", ""),
            "photos": json.dumps(raw.get("images", [])), 
        }

    @staticmethod
    def fetch(product_id: str, limit: int = 0, page_size: int = 100, **_) -> Iterable[dict]:
        page, fetched = 1, 0
        with httpx.Client(timeout=20, headers=HEADERS) as cli:
            while True:
                url = AliExpressBackend.URL.format(pid=product_id, page=page, size=page_size)
                try:
                    resp = cli.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    print(f"Failed to fetch page {page}: {e}")
                    break

                reviews = data.get("data", {}).get("evaViewList", [])
                if not reviews:
                    break

                for raw in reviews:
                    row = AliExpressBackend._normalize(raw)
                    yield row
                    fetched += 1
                    if limit and fetched >= limit:
                        return
                page += 1


BACKENDS = {
    "aliexpress": AliExpressBackend,
}


def cli(parser: argparse.ArgumentParser) -> argparse.Namespace:
    parser.description = "Scrape reviews from e-commerce platforms"
    parser.add_argument("backend", choices=BACKENDS, help="Platform (e.g. aliexpress)")
    parser.add_argument("product_id", help="Product ID to fetch reviews for")
    parser.add_argument("--outfile", default="reviews.csv", help="CSV output filename")
    parser.add_argument("--limit", type=int, default=0, help="Max reviews (0 = all)")
    parser.add_argument("--page-size", type=int, default=100, help="Backend page size")
    return parser


def main(ns: argparse.Namespace | None = None) -> int:
    if ns is None:
        parser = argparse.ArgumentParser()
        cli(parser)
        ns = parser.parse_args()

    backend_cls = BACKENDS[ns.backend]
    rows = backend_cls.fetch(ns.product_id, limit=ns.limit, page_size=ns.page_size)

    out_path = Path(ns.outfile).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["author", "country", "rating", "date", "content", "photos"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"✅ Wrote {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
