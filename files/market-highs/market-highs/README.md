# 📈 한미 시장 신고가 대시보드

한국(코스피·코스닥)과 미국(S&P500·NASDAQ100)의 52주 신고가 및 역사적 신고가 종목을 날짜별로 추적하는 대시보드입니다.

**👉 [라이브 대시보드 보기](https://YOUR_USERNAME.github.io/market-highs/)**

---

## 폴더 구조

```
market-highs/
├── index.html              # 메인 대시보드 (GitHub Pages 진입점)
├── data/
│   ├── 2026-04-26/
│   │   └── data.json       # 해당 날짜 데이터
│   ├── 2026-04-27/
│   │   └── data.json
│   └── ...
└── README.md
```

## 데이터 구조 (`data.json`)

```json
{
  "date": "2026-04-26",
  "kr": {
    "historical_high": [
      {
        "code": "종목코드",
        "name": "종목명",
        "change_pct": 29.96,
        "prev_high_date": "2026-02-25",
        "current_price": 1541000,
        "prev_high_price": 1442000
      }
    ],
    "week52_only": [ ... ]
  },
  "us": {
    "week52": [
      {
        "ticker": "INTC",
        "sector": "Information Technology",
        "price": 82.54,
        "change_pct": 23.60,
        "rationale": "AI 투자 낙관론 확산"
      }
    ]
  }
}
```

## 새 날짜 데이터 추가 방법

1. `data/YYYY-MM-DD/` 폴더 생성
2. 위 구조에 맞게 `data.json` 작성
3. `index.html` 상단 `DATES` 배열과 `<select>` 옵션에 날짜 추가:

```js
// index.html 내 script
const DATES = ['2026-04-27', '2026-04-26'];  // 최신 날짜 앞에 추가
```

```html
<select id="dateSelect">
  <option value="2026-04-27">2026-04-27</option>
  <option value="2026-04-26">2026-04-26</option>
</select>
```

## GitHub Pages 배포

1. 이 레포를 GitHub에 push
2. Settings → Pages → Source: `Deploy from a branch`
3. Branch: `main`, Folder: `/ (root)` 선택 후 Save
4. 잠시 후 `https://YOUR_USERNAME.github.io/market-highs/` 에서 접근 가능

---

데이터 출처: 한국거래소(KRX), S&P500/NASDAQ100 유니버스 기준
