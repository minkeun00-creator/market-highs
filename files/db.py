#!/usr/bin/env python3
"""
db.py  –  누적 DB 관리자 v2
records.json : 모든 일별 레코드 누적 (append-only)
themes.json  : 날짜 × 시장 × 테마 집계
leaders.json : 주도주 시계열 + 교체 이벤트
Usage:
  python db.py ingest  --file parsed.json
  python db.py rebuild
  python db.py export  --date 2026-04-29 --out data/dash_kr.json
  python db.py status
"""
import argparse, json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DB   = Path(__file__).parent / "data"
DB.mkdir(parents=True, exist_ok=True)
RECORDS = DB / "records.json"
THEMES  = DB / "themes.json"
LEADERS = DB / "leaders.json"


def _load(p: Path):
    return json.loads(p.read_text("utf-8")) if p.exists() else ([] if p.suffix == ".json" and "records" in p.name else {})

def _save(p: Path, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")


# ── ingest ──────────────────────────────────────────────
def ingest(filepath: str):
    new = json.loads(Path(filepath).read_text("utf-8"))
    if not new:
        print("[db] empty file – skip"); return

    all_r: list = _load(RECORDS) if RECORDS.exists() else []
    keys = {(r["date"], r["market"], r["type"], r["ticker"]) for r in all_r}
    added = 0
    for rec in new:
        k = (rec["date"], rec["market"], rec["type"], rec["ticker"])
        if k not in keys:
            all_r.append(rec); keys.add(k); added += 1

    all_r.sort(key=lambda r: (r["date"], r["market"], r["type"]))
    _save(RECORDS, all_r)
    print(f"[db] +{added} records  (total {len(all_r)})")
    _rebuild_themes(all_r)
    _rebuild_leaders(all_r)


# ── rebuild ─────────────────────────────────────────────
def _rebuild_themes(all_r=None):
    if all_r is None: all_r = _load(RECORDS)
    agg = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for r in all_r:
        agg[r["date"]][r["market"]][r.get("theme","기타")] += 1
    _save(THEMES, {d: {m: dict(t) for m, t in mv.items()} for d, mv in sorted(agg.items())})
    print(f"[db] themes rebuilt  ({len(agg)} dates)")

def _rebuild_leaders(all_r=None):
    if all_r is None: all_r = _load(RECORDS)
    themes = _load(THEMES)
    dates  = sorted(themes)
    series = []
    prev   = {}

    for date in dates:
        day = themes[date]
        entry = {"date": date}
        for mkt in ("KR","US"):
            if mkt not in day: continue
            top = max(day[mkt], key=day[mkt].get)
            entry[f"{mkt.lower()}_top"] = top
            entry[f"{mkt.lower()}_dist"] = day[mkt]
            if prev.get(mkt) and prev[mkt] != top:
                entry[f"{mkt.lower()}_change"] = {"from": prev[mkt], "to": top}
            prev[mkt] = top
        series.append(entry)

    _save(LEADERS, series)
    print(f"[db] leaders rebuilt ({len(series)} entries)")

def rebuild():
    _rebuild_themes()
    _rebuild_leaders()


# ── export ──────────────────────────────────────────────
def export_dash(date: str | None, out: str):
    all_r   = _load(RECORDS) if RECORDS.exists() else []
    themes  = _load(THEMES)  if THEMES.exists()  else {}
    leaders = _load(LEADERS) if LEADERS.exists() else []

    dates_avail = sorted(set(r["date"] for r in all_r))
    target = date or (dates_avail[-1] if dates_avail else datetime.today().strftime("%Y-%m-%d"))

    today_r  = [r for r in all_r if r["date"] == target]
    recent30 = dates_avail[-30:]

    # 테마 시계열
    theme_series = {}
    for d in recent30:
        for mkt in ("KR","US"):
            tm = themes.get(d, {}).get(mkt, {})
            if mkt not in theme_series: theme_series[mkt] = {}
            for theme, cnt in tm.items():
                theme_series[mkt].setdefault(theme, []).append({"date": d, "count": cnt})

    # 동조화 지수
    sync = []
    for d in recent30:
        kr = set(themes.get(d,{}).get("KR",{}).keys())
        us = set(themes.get(d,{}).get("US",{}).keys())
        if kr and us:
            sync.append({"date":d, "sync":round(len(kr&us)/len(kr|us)*100,1)})

    payload = {
        "generated_at":   datetime.now().isoformat(),
        "target_date":    target,
        "dates_available":dates_avail,
        "today": {
            "kr_52w":  [r for r in today_r if r["market"]=="KR" and r["type"]=="52w"],
            "kr_hist": [r for r in today_r if r["market"]=="KR" and r["type"]=="hist"],
            "us_52w":  [r for r in today_r if r["market"]=="US"],
        },
        "theme_series":  theme_series,
        "sync_series":   sync,
        "leaders":       leaders[-60:],
        "change_events": [e for e in leaders if "kr_change" in e or "us_change" in e][-20:],
    }
    Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    print(f"[db] exported → {out}  ({len(today_r)} records for {target})")


# ── status ──────────────────────────────────────────────
def status():
    all_r   = _load(RECORDS) if RECORDS.exists() else []
    dates   = sorted(set(r["date"] for r in all_r))
    markets = sorted(set(r["market"] for r in all_r))
    print(f"[db] records: {len(all_r)}")
    print(f"     dates  : {len(dates)}  ({dates[0] if dates else '-'} ~ {dates[-1] if dates else '-'})")
    print(f"     markets: {markets}")
    for d in dates[-5:]:
        day = [r for r in all_r if r["date"]==d]
        kr52  = sum(1 for r in day if r["market"]=="KR" and r["type"]=="52w")
        krhst = sum(1 for r in day if r["market"]=="KR" and r["type"]=="hist")
        us52  = sum(1 for r in day if r["market"]=="US")
        print(f"     {d}  KR52w={kr52:3d}  KRhist={krhst:3d}  US={us52:3d}")


# ── CLI ─────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("ingest");  p.add_argument("--file", required=True)
    sub.add_parser("rebuild")
    p = sub.add_parser("export");  p.add_argument("--date",default=None); p.add_argument("--out",default="data/dashboard_data.json")
    sub.add_parser("status")
    args = ap.parse_args()
    if   args.cmd=="ingest":  ingest(args.file)
    elif args.cmd=="rebuild": rebuild()
    elif args.cmd=="export":  export_dash(args.date, args.out)
    elif args.cmd=="status":  status()
    else: ap.print_help()

if __name__=="__main__": main()
