#!/usr/bin/env bash
# ============================================================
# daily_update.sh  –  매일 실행 스크립트
# 사용법:
#   ./daily_update.sh --kr-52w 0430_52주.xlsx --kr-hist 0430역사적.xlsx --us-json us_0430.json --date 2026-04-30
# ============================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

KR_52W=""; KR_HIST=""; US_JSON=""; DATE="$(date +%Y-%m-%d)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kr-52w)  KR_52W="$2";  shift 2 ;;
    --kr-hist) KR_HIST="$2"; shift 2 ;;
    --us-json) US_JSON="$2"; shift 2 ;;
    --date)    DATE="$2";    shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

echo "===== Market Highs Update · $DATE ====="
mkdir -p "$ROOT/data"
TMP="$ROOT/data/tmp_${DATE}"
mkdir -p "$TMP"

echo "[1/5] Parsing..."
[[ -n "$KR_52W"  ]] && python3 "$ROOT/parse_kr.py" --file "$KR_52W"  --type 52w  --date "$DATE" --out "$TMP/kr_52w.json"
[[ -n "$KR_HIST" ]] && python3 "$ROOT/parse_kr.py" --file "$KR_HIST" --type hist --date "$DATE" --out "$TMP/kr_hist.json"
[[ -n "$US_JSON" ]] && python3 "$ROOT/parse_us.py" --file "$US_JSON" --date "$DATE" --out "$TMP/us_52w.json"

echo "[2/5] Merging..."
python3 - <<PYEOF
import json, glob
files = glob.glob("$TMP/*.json")
merged = []
for f in sorted(files):
    merged.extend(json.loads(open(f).read()))
open("$TMP/merged.json","w").write(json.dumps(merged, ensure_ascii=False, indent=2))
print(f"  {len(merged)} records merged")
PYEOF

echo "[3/5] Ingesting DB..."
python3 "$ROOT/db.py" ingest --file "$TMP/merged.json"

echo "[4/5] Exporting dashboard data..."
python3 "$ROOT/db.py" export --date "$DATE" --out "$ROOT/data/dashboard_data.json"

echo "[5/5] Building index.html..."
python3 "$ROOT/build.py" --data "$ROOT/data/dashboard_data.json" --out "$ROOT/index.html"

rm -rf "$TMP"
echo "✅ Done → $ROOT/index.html"
