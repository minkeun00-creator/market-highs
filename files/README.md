# 📈 한미 시장 신고가 대시보드

한국(코스피·코스닥)과 미국(S&P500·NASDAQ100)의 52주 신고가 및 역사적 신고가 종목을 날짜별로 추적하는 대시보드입니다.

👉 **[라이브 대시보드 보기](https://minkeun00-creator.github.io/market-highs/)**

---

## 폴더 구조

```
market-highs/
├── index.html          # 메인 대시보드 (GitHub Pages 진입점)
├── parse_kr.py         # 한국 엑셀 파서
├── parse_us.py         # 미국 JSON 파서
├── db.py               # 누적 DB 관리
├── build.py            # index.html 빌드
├── daily_update.sh     # 매일 실행 스크립트
├── us_quick_input.html # US 데이터 빠른 입력기 (로컬용)
└── data/               # 자동 생성
    ├── records.json
    ├── themes.json
    └── dashboard_data.json
```

## 매일 사용법

```bash
./daily_update.sh \
  --kr-52w  0430_52주.xlsx \
  --kr-hist 0430역사적.xlsx \
  --us-json us_0430.json \
  --date    2026-04-30
```

그 후 `index.html`과 `data/` 폴더를 GitHub에 push.
