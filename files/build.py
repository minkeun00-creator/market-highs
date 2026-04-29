#!/usr/bin/env python3
"""build.py – dashboard_data.json → index.html"""
import argparse, json
from pathlib import Path
from datetime import datetime

def theme_color(t):
    P = {"반도체/전자부품":"#7c6af7","전력/에너지인프라":"#f9a94b","소재/화학":"#52c4b0",
         "철강/금속":"#e07b54","소비/유통":"#5b9cf6","방산/조선":"#c65d7b",
         "지주/기타":"#a0a0a0","헬스케어/바이오":"#a3d977","IT/기타":"#f06292",
         "SPAC":"#b0bec5","AI 인프라":"#7c6af7","전력/유틸리티":"#f9a94b",
         "리츠/부동산":"#52c4b0","에너지":"#e07b54","금융":"#5b9cf6","기타":"#555"}
    return P.get(t,"#888")

def build_html(data):
    d      = data.get("target_date","")
    today  = data.get("today",{})
    kr52   = today.get("kr_52w",[])
    krhist = today.get("kr_hist",[])
    us52   = today.get("us_52w",[])
    ts     = data.get("theme_series",{})
    sync   = data.get("sync_series",[])
    chg    = data.get("change_events",[])

    def cnt_themes(recs):
        out={}
        for r in recs: out[r.get("theme","기타")]=out.get(r.get("theme","기타"),0)+1
        return sorted(out.items(),key=lambda x:-x[1])

    def bars(themes,tot):
        h=""
        for t,c in themes[:8]:
            p=round(c/max(tot,1)*100)
            h+=f'<div class="br"><span class="bl">{t}</span><div class="bt"><div class="bf" style="width:{p}%;background:{theme_color(t)}"></div></div><span class="bv">{c}</span></div>'
        return h

    def kr_rows(recs):
        h=""
        for r in recs:
            c=r.get("change"); cs="pos" if c and c>0 else("neg" if c and c<0 else"")
            cs2=(f"+{c:.2f}%" if c and c>0 else f"{c:.2f}%") if c else"-"
            etf='<span class="etag">ETF</span>' if r.get("is_etf") else""
            h+=f'<tr><td><span class="dot" style="background:{theme_color(r.get("theme",""))}"></span>{r.get("name","")}{etf}</td><td class="mono gray">{r.get("ticker","")}</td><td>{r.get("theme","")}</td><td class="right mono {cs}">{cs2}</td><td class="right mono gray small">{r.get("price",0):,.0f}</td></tr>'
        return h

    def us_rows(recs):
        h=""
        for r in recs:
            c=r.get("change"); cs="pos" if c and c>0 else "neg"
            cs2=f"+{c:.2f}%" if c and c>0 else f"{c:.2f}%"
            sp='<span class="etag">S&P</span>' if r.get("sp500") else""
            h+=f'<tr><td class="mono">{r.get("ticker","")}{sp}</td><td>{r.get("name","")}</td><td>{r.get("theme","")}</td><td class="right mono {cs}">{cs2}</td><td class="right mono gray small">{r.get("rationale","")}</td></tr>'
        return h

    # chart data
    def top_t(mkt,n=5):
        all_t={}
        for t,pts in ts.get(mkt,{}).items():
            all_t[t]=sum(p["count"] for p in pts)
        return sorted(all_t,key=lambda x:-all_t[x])[:n]

    def series_j(mkt,tlist):
        dates=sorted({p["date"] for t in tlist for p in ts.get(mkt,{}).get(t,[])})[-30:]
        ds=[{"label":t,"data":[next((p["count"] for p in ts.get(mkt,{}).get(t,[]) if p["date"]==d),0) for d in dates],
             "borderColor":theme_color(t),"backgroundColor":theme_color(t)+"33","tension":.4,"fill":False,"pointRadius":3}
            for t in tlist]
        return json.dumps(dates),json.dumps(ds)

    kr5=top_t("KR"); us5=top_t("US")
    kd,kds=series_j("KR",kr5); ud,uds=series_j("US",us5)
    sd=json.dumps([s["date"] for s in sync[-30:]])
    sv=json.dumps([s["sync"] for s in sync[-30:]])

    kr_themes=cnt_themes(kr52+krhist); us_themes=cnt_themes(us52)
    common=set(t for t,_ in kr_themes)&set(t for t,_ in us_themes)
    common_html="".join(f'<span class="pill" style="background:{theme_color(t)}22;border:1px solid {theme_color(t)};color:{theme_color(t)}">{t}</span>' for t in sorted(common))
    lsync=sync[-1]["sync"] if sync else "N/A"

    chg_rows=""
    for e in [x for x in chg if x.get("type")=="교체"][-3:]:
        chg_rows+=f'<tr><td class="mono">{e.get("date","")}</td><td>{e.get("market","")}</td><td>{e.get("from","")}</td><td>→ {e.get("to","")}</td></tr>'
    if not chg_rows: chg_rows='<tr><td colspan="4" class="gray center">누적 데이터 증가 시 표시</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market Highs Brief — {d}</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@300;400;600&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
:root{{--bg:#0c0c0c;--bg2:#131313;--bg3:#1a1a1a;--border:#242424;--ink:#e8e3d8;--muted:#585450;--gold:#c9a84c;--gold2:#e8c96d;--accent:#7c6af7;--pos:#4caf86;--neg:#e05a5a;--mono:'IBM Plex Mono',monospace;--kr:'Noto Sans KR',sans-serif;--disp:'Bebas Neue',sans-serif;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--ink);font-family:var(--kr);font-size:13px;}}
body::before{{content:"";position:fixed;inset:0;pointer-events:none;z-index:999;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.05) 2px,rgba(0,0,0,.05) 4px);}}
.header{{background:var(--bg2);border-bottom:1px solid var(--border);padding:0 28px;height:52px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}}
.hlogo{{font-family:var(--disp);font-size:20px;letter-spacing:.1em;color:var(--gold);}}
.hdate{{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.12em;}}
.hero{{background:linear-gradient(135deg,#0f0f0f,#141014,#0c0c10);border-bottom:1px solid var(--border);padding:28px 28px 24px;display:grid;grid-template-columns:auto 1fr auto;gap:32px;align-items:center;}}
.hero-bg{{font-family:var(--disp);font-size:64px;line-height:1;color:var(--gold);opacity:.1;letter-spacing:.02em;}}
.hero-scores{{display:flex;}}
.hs{{padding:0 24px;border-right:1px solid var(--border);text-align:center;}}
.hs:first-child{{padding-left:0;}} .hs:last-child{{border-right:none;}}
.hs-n{{font-family:var(--disp);font-size:46px;line-height:1;color:var(--gold2);display:block;}}
.hs-l{{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.12em;display:block;margin-top:3px;}}
.signal{{text-align:right;}}
.stag{{display:inline-block;padding:5px 12px;border:1px solid var(--accent);color:var(--accent);font-family:var(--mono);font-size:10px;letter-spacing:.14em;margin-bottom:6px;}}
.sdesc{{font-size:11px;color:var(--ink);max-width:160px;text-align:right;line-height:1.6;}}
.wrap{{padding:0 28px;}}
.sec-title{{font-family:var(--disp);font-size:26px;letter-spacing:.06em;margin:28px 0 14px;display:flex;align-items:baseline;gap:10px;}}
.sec-title .sub{{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.12em;}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:28px;}}
.panel{{background:var(--bg2);border:1px solid var(--border);padding:18px 20px;}}
.panel.full{{grid-column:1/-1;}}
.ptitle{{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.12em;text-transform:uppercase;margin-bottom:12px;border-bottom:1px solid var(--border);padding-bottom:7px;}}
.chart-wrap{{position:relative;height:170px;}}
.br{{display:flex;align-items:center;margin-bottom:7px;}}
.bl{{width:120px;font-size:11px;color:var(--ink);flex-shrink:0;}}
.bt{{flex:1;height:9px;background:var(--bg3);border-radius:2px;overflow:hidden;margin:0 8px;}}
.bf{{height:100%;border-radius:2px;}}
.bv{{width:24px;text-align:right;font-family:var(--mono);font-size:11px;color:var(--muted);}}
table{{width:100%;border-collapse:collapse;}}
th{{font-family:var(--mono);font-size:10px;color:var(--muted);text-align:left;padding:6px 10px;border-bottom:1px solid var(--border);letter-spacing:.08em;text-transform:uppercase;}}
td{{padding:7px 10px;border-bottom:1px solid #1a1a1a;vertical-align:middle;}}
tr:hover td{{background:#171717;}}
.mono{{font-family:var(--mono);}} .small{{font-size:11px;}} .right{{text-align:right;}} .gray{{color:var(--muted);}} .center{{text-align:center;}}
.pos{{color:var(--pos);}} .neg{{color:var(--neg);}}
.dot{{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;vertical-align:middle;}}
.etag{{background:#2a2a3a;color:#9a9af7;font-size:9px;padding:1px 5px;margin-left:4px;font-family:var(--mono);}}
.pills{{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;}}
.pill{{font-size:11px;padding:3px 10px;border-radius:20px;font-weight:500;}}
.footer{{padding:16px 28px;border-top:1px solid var(--border);display:flex;justify-content:space-between;margin-top:40px;}}
.footer-note{{font-family:var(--mono);font-size:10px;color:var(--muted);}}
@media(max-width:768px){{.grid2,.grid3{{grid-template-columns:1fr;}}.hero{{grid-template-columns:1fr;}}.hero-bg{{display:none;}}}}
</style></head><body>
<div class="header"><div class="hlogo">MARKET HIGHS</div><div class="hdate">KRX + US · {d}</div></div>
<div class="hero">
  <div class="hero-bg">{d[5:]}</div>
  <div class="hero-scores">
    <div class="hs"><span class="hs-n">{len(kr52)}</span><span class="hs-l">KR 52주</span></div>
    <div class="hs"><span class="hs-n">{len(krhist)}</span><span class="hs-l">KR 역사적</span></div>
    <div class="hs"><span class="hs-n">{len(us52)}</span><span class="hs-l">US 52주</span></div>
    <div class="hs"><span class="hs-n" style="color:{'var(--pos)' if isinstance(lsync,float) and lsync>=50 else 'var(--neg)'}">{lsync}%</span><span class="hs-l">동조화</span></div>
  </div>
  <div class="signal"><div class="stag">{"SYNC ON" if common else "DIVERGE"}</div><div class="sdesc">{"한미 공통 테마:<br>"+"·".join(list(common)[:3]) if common else "한미 테마 분리 중"}</div></div>
</div>
<div class="wrap">
  <div class="sec-title">Distribution <span class="sub">THEME × MARKET</span></div>
  <div class="grid3">
    <div class="panel"><div class="ptitle">🇰🇷 KR 52주 테마</div>{bars(cnt_themes(kr52),len(kr52))}</div>
    <div class="panel"><div class="ptitle">🇰🇷 KR 역사적 테마</div>{bars(cnt_themes(krhist),len(krhist))}</div>
    <div class="panel">
      <div class="ptitle">🔗 한미 공통 테마</div>
      <div class="pills">{common_html or '<span class="gray">US 데이터 추가 시 표시</span>'}</div>
      <div style="margin-top:20px"><div class="ptitle">⚡ 주도주 교체</div>
      <table><tr><th>날짜</th><th>시장</th><th>이전</th><th>신규</th></tr>{chg_rows}</table></div>
    </div>
  </div>
  <div class="sec-title">Trend <span class="sub">THEME SERIES · 30 DAYS</span></div>
  <div class="grid2">
    <div class="panel"><div class="ptitle">📈 KR 테마 추이</div><div class="chart-wrap"><canvas id="ckr"></canvas></div></div>
    <div class="panel"><div class="ptitle">📈 US 테마 추이</div><div class="chart-wrap"><canvas id="cus"></canvas></div></div>
  </div>
  <div class="panel full" style="margin-bottom:14px"><div class="ptitle">🌐 한미 동조화 지수</div><div class="chart-wrap"><canvas id="csync"></canvas></div></div>
  <div class="sec-title">Stocks <span class="sub">TODAY'S HIGHS</span></div>
  <div class="grid2">
    <div class="panel"><div class="ptitle">🇰🇷 KR 52주 신고가 ({len(kr52)})</div><div style="max-height:400px;overflow-y:auto"><table><tr><th>종목명</th><th>코드</th><th>테마</th><th class="right">등락</th><th class="right">현재가</th></tr>{kr_rows(sorted(kr52,key=lambda r:-(r.get('change') or 0)))}</table></div></div>
    <div class="panel"><div class="ptitle">🇰🇷 KR 역사적 신고가 ({len(krhist)})</div><div style="max-height:400px;overflow-y:auto"><table><tr><th>종목명</th><th>코드</th><th>테마</th><th class="right">등락</th><th class="right">현재가</th></tr>{kr_rows(sorted(krhist,key=lambda r:-(r.get('change') or 0)))}</table></div></div>
  </div>
  {"" if not us52 else f'<div class="panel full" style="margin-bottom:28px"><div class="ptitle">🇺🇸 US 52주 신고가 ({len(us52)})</div><table><tr><th>티커</th><th>종목명</th><th>테마</th><th class="right">등락</th><th>논리</th></tr>{us_rows(us52)}</table></div>'}
</div>
<div class="footer">
  <div class="footer-note">KRX 전종목 · S&P500+NASDAQ100 · {d} 기준 · Internal Use Only</div>
  <div class="footer-note">Market Highs Dashboard · Druckenmiller Project</div>
</div>
<script>
const CO={{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#888',font:{{size:10}}}}}}}},scales:{{x:{{ticks:{{color:'#555',maxTicksLimit:8,font:{{size:9}}}},grid:{{color:'#1e1e1e'}}}},y:{{ticks:{{color:'#555',font:{{size:9}}}},grid:{{color:'#1e1e1e'}}}}}}}};
new Chart(document.getElementById('ckr'),{{type:'line',data:{{labels:{kd},datasets:{kds}}},options:CO}});
new Chart(document.getElementById('cus'),{{type:'line',data:{{labels:{ud},datasets:{uds}}},options:CO}});
new Chart(document.getElementById('csync'),{{type:'line',data:{{labels:{sd},datasets:[{{label:'동조화%',data:{sv},borderColor:'#7c6af7',backgroundColor:'#7c6af733',tension:.4,fill:true,pointRadius:3}}]}},options:{{...CO,scales:{{...CO.scales,y:{{...CO.scales.y,min:0,max:100,ticks:{{color:'#555',callback:v=>v+'%',font:{{size:9}}}},grid:{{color:'#1e1e1e'}}}}}}}}}});
</script></body></html>"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default="data/dashboard_data.json")
    ap.add_argument("--out", default="index.html")
    args=ap.parse_args()
    data=json.loads(Path(args.data).read_text("utf-8"))
    Path(args.out).write_text(build_html(data),"utf-8")
    print(f"[build] → {args.out}")

if __name__=="__main__": main()
