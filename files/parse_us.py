#!/usr/bin/env python3
"""
parse_us.py
-----------
미국 52주 신고가 파서
입력: JSON (수동 입력) 또는 CSV
Usage:
  python parse_us.py --file us_0429.json --date 2026-04-29
  python parse_us.py --file us_0429.csv  --date 2026-04-29

JSON 스키마 (스크린샷에서 수동 입력):
[
  {
    "ticker": "MRVL",
    "name": "Marvell Technology",
    "sector": "Technology",
    "price": 106.71,
    "change": 7.73,
    "high52": 106.71,
    "volume": 1210000,
    "rationale": "AI 데이터센터 성장",
    "sp500": true
  }
]
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

THEME_MAP = {
    "Technology":            "AI 인프라",
    "Communication":         "AI 인프라",
    "Semiconductors":        "AI 인프라",
    "Real Estate":           "리츠/부동산",
    "Utilities":             "전력/유틸리티",
    "Energy":                "에너지",
    "Financials":            "금융",
    "Health Care":           "헬스케어",
    "Consumer Discretionary":"소비재(성장)",
    "Consumer Staples":      "소비재(방어)",
    "Industrials":           "산업재",
    "Materials":             "소재",
}

TICKER_THEME_OVERRIDE = {
    "EQIX": "리츠/부동산",
    "AMT":  "리츠/부동산",
    "ETR":  "전력/유틸리티",
    "NEE":  "전력/유틸리티",
    "NI":   "전력/유틸리티",
    "MRVL": "AI 인프라",
    "NVDA": "AI 인프라",
    "AMD":  "AI 인프라",
    "ROST": "소비재(방어)",
    "TJX":  "소비재(방어)",
    "WMT":  "소비재(방어)",
    "COST": "소비재(방어)",
}


def _guess_theme(ticker: str, sector: str) -> str:
    if ticker in TICKER_THEME_OVERRIDE:
        return TICKER_THEME_OVERRIDE[ticker]
    for key, theme in THEME_MAP.items():
        if key.lower() in str(sector).lower():
            return theme
    return "기타"


def parse_json(filepath: str, trade_date: str) -> list[dict]:
    data = json.loads(Path(filepath).read_text(encoding="utf-8"))
    records = []
    for item in data:
        ticker = str(item.get("ticker", "")).upper().strip()
        sector = str(item.get("sector", "")).strip()
        records.append({
            "date":      trade_date,
            "market":    "US",
            "type":      "52w",
            "ticker":    ticker,
            "name":      str(item.get("name", ticker)),
            "is_etf":    False,
            "theme":     _guess_theme(ticker, sector),
            "sector":    sector,
            "price":     item.get("price"),
            "change":    item.get("change"),
            "high52":    item.get("high52"),
            "volume":    item.get("volume"),
            "rationale": item.get("rationale", ""),
            "sp500":     item.get("sp500", False),
        })
    return records


def parse_csv(filepath: str, trade_date: str) -> list[dict]:
    df = pd.read_csv(filepath, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]
    records = []
    for _, row in df.iterrows():
        ticker = str(row.get("ticker", "")).upper().strip()
        sector = str(row.get("sector", "")).strip()
        def n(v):
            try: return float(re.sub(r"[^0-9.\-]", "", str(v)))
            except: return None
        records.append({
            "date":      trade_date,
            "market":    "US",
            "type":      "52w",
            "ticker":    ticker,
            "name":      str(row.get("name", ticker)).strip(),
            "is_etf":    False,
            "theme":     _guess_theme(ticker, sector),
            "sector":    sector,
            "price":     n(row.get("price")),
            "change":    n(row.get("change")),
            "high52":    n(row.get("high52")),
            "volume":    n(row.get("volume")),
            "rationale": str(row.get("rationale", "")).strip(),
            "sp500":     str(row.get("sp500", "")).lower() in ("true", "1", "yes"),
        })
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file",  required=True)
    ap.add_argument("--date",  default=datetime.today().strftime("%Y-%m-%d"))
    ap.add_argument("--out",   default=None)
    args = ap.parse_args()

    ext = Path(args.file).suffix.lower()
    if ext == ".json":
        records = parse_json(args.file, args.date)
    elif ext == ".csv":
        records = parse_csv(args.file, args.date)
    else:
        sys.exit(f"Unsupported file type: {ext}")

    out = json.dumps(records, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"[parse_us] {len(records)} records → {args.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
