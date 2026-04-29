#!/usr/bin/env python3
"""
parse_kr.py  –  한국 신고가 엑셀 파서 (실제 KRX 포맷 기준)
컬럼 구조: 단축코드 | (CA) | 종목명 | 갱신가격 | 갱신전가격 | 갱신전일자 | 현재가 | 대비 | 전일대비 | 등락률 | 거래량
Usage:
  python parse_kr.py --file 0429_52주.xlsx   --type 52w  --date 2026-04-29 --out kr_52w.json
  python parse_kr.py --file 0429역사적.xlsx  --type hist --date 2026-04-29 --out kr_hist.json
"""
import argparse, json, re
from datetime import datetime
from pathlib import Path
import pandas as pd

THEME_MAP = [
    (["삼성전자","SK하이닉스","삼성SDI","엘앤에프","LG이노텍","두산테스나","퀄리타스","싸이맥스",
      "하나머티리얼즈","대덕전자","심텍","서진시스템","샘씨엔에스","기가비스","이오테크닉스",
      "프로텍","코세스","티씨머티리얼즈","솔루엠","에스씨디","이엘피","자화전자","삼성전기",
      "엑시콘","와이씨켐","비씨엔씨","티엘비","아비코","더블유씨피","GST","엔비알모션",
      "삼화콘덴서","솔브레인","코리아써키트","씨아이에스","케이엔더블유","비나텍","제너셈",
      "피엠티","코스텍시스","덕우전자","오로스테크놀로지","앤로보틱스","영화테크","퓨릿",
      "피앤씨테크","메가터치","이엘씨","브이엠","도이치"], "반도체/전자부품"),
    (["LS ELECTRIC","LS에코에너지","LS머트리얼즈","일진전기","일진파워","HD현대에너지솔루션",
      "효성중공업","제룡전기","제룡산업","세보엠이씨","타이거일렉","그리드위즈","제일일렉트릭",
      "한선엔지니어링","지투파워","에스에너지","선도전기","두산퓨얼셀","세명전기",
      "에너토크","금화피에스시","지앤비에스","TP"], "전력/에너지인프라"),
    (["HD현대중공업","HD현대","현대로템","STX엔진","수산인더스트리","두산에너빌리티",
      "한진중공업","SIMPAC"], "방산/조선"),
    (["POSCO","동국제강","동국씨엠","휴스틸","넥스틸","DSR제강","KG스틸","대원전선",
      "대한전선","알멕","KBI메탈","동원금속","삼아알미늄","원풍","삼영","대창","DSR"], "철강/금속"),
    (["롯데케미칼","코오롱인더","PI첨단소재","롯데에너지머티리얼즈","SK이노베이션","송원산업",
      "성일하이텍","국도화학","KG케미칼","HS효성첨단소재","LX하우시스","KPX홀딩스",
      "유니드","한국알콜","테이팩스","두올","롯데정밀화학","씨에스베어링",
      "진성티이씨","유성티엔에스"], "소재/화학"),
    (["코오롱","한섬","오리온","롯데쇼핑","신세계","BGF","에이블씨엔씨","LX인터내셔널",
      "GS글로벌","현대코퍼레이션","LS네트웍스","KG모빌리티","인지컨트롤스","서연탑메탈",
      "한국단자","누리플렉스","와이지-원","서원","삼일기업공사"], "소비/유통"),
    (["SK스퀘어","SK","GS","일진홀딩스","솔브레인홀딩스","케이씨텍","자이에스앤디","진흥기업",
      "피노","메쥬","THE E&M","DL","NC","코리아써우","BYC우","CJ4우","두산우"], "지주/기타"),
    (["메디포스트","큐로셀","네오팜","에스티큐브"], "헬스케어/바이오"),
    (["알티캐스트","코텍","와이엠텍","신도기연","아이티센"], "IT/기타"),
]

def guess_theme(name: str) -> str:
    if "스팩" in name: return "SPAC"
    for names, theme in THEME_MAP:
        for n in names:
            if n in name: return theme
    return "기타"

def parse_excel(filepath: str, file_type: str, trade_date: str) -> list[dict]:
    df = pd.read_excel(filepath, dtype=str)
    df.columns = ["ticker","ca","name","update_price","prev_price",
                  "update_date","current","sign","change_abs","change_pct","volume"]
    df = df.dropna(subset=["ticker"])
    df = df[~df["ticker"].str.startswith("단축")]
    records = []
    for _, r in df.iterrows():
        name = str(r["name"]).strip()
        ticker = re.split(r'\*', str(r["ticker"]))[0]
        def n(v):
            try: return float(str(v).replace(",","").strip())
            except: return None
        records.append({
            "date": trade_date, "market": "KR", "type": file_type,
            "ticker": ticker, "name": name, "is_etf": False,
            "theme": guess_theme(name), "sector": "",
            "price": n(r["current"]), "change": n(r["change_pct"]),
            "volume": n(r["volume"]),
            "update_date": str(r["update_date"])[:10],
            "prev_price": n(r["prev_price"]),
        })
    return records

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--type", required=True, choices=["52w","hist"])
    ap.add_argument("--date", default=datetime.today().strftime("%Y-%m-%d"))
    ap.add_argument("--out",  default=None)
    args = ap.parse_args()
    records = parse_excel(args.file, args.type, args.date)
    out = json.dumps(records, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"[parse_kr] {len(records)} records → {args.out}")
    else:
        print(out)

if __name__ == "__main__":
    main()
