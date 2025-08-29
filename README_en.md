🌐 Languages: [한국어](README.md) | **English**


# ⚾ KBO Saber App

A web application to calculate and visualize sabermetrics for the KBO League.  
Built with Flask.

🌐 Languages: [한국어](README.md) | **English**

---

## 🚀 Features

### 🥎 Hitter Calculator
- OPS, OPS+
- wRC, wRC+
- League constants & park factor inputs
- Presets (league averages)
- Reference scale (Excellent, Great, Average…)

**Example:**  
![OPS+, wRC+ Calculator](docs/screenshots/calc_hitter.png)

---

### ⚾ Pitcher Calculator
- ERA-, FIP-, xFIP-
- League ERA/FIP/xFIP presets
- Park factor adjustments
- Colored badges by performance tier

**Example:**  
![Pitcher Calculator](docs/screenshots/calc_pitcher.png)

---

### 📊 Game Score
- Bill James Game Score
- Game Score v2.0
- Auto-compute from pitching stats

**Example:**  
![Game Score](docs/screenshots/calc_gamescore.png)

---

### 📈 Real-time Pythagorean
- Google Sheets CSV (cached every 30 mins)
- Actual vs Pythagorean win%
- Difference (±), Games Behind (GB)
- Projected season standings (Wins–Draws–Losses, win%)
- Selectable exponent (default 2.00, literature 1.83, etc.)

**Example:**  
![Pythagorean](docs/screenshots/pythagorean.png)

---

## 📂 Structure
kbo-saber-app/
├─ run.py
├─ requirements.txt
├─ app/
│ ├─ init.py
│ ├─ routes/
│ │ ├─ calc.py
│ │ ├─ pitch.py
│ │ ├─ gamescore.py
│ │ └─ pythag.py
│ └─ templates/
│ ├─ base.html
│ ├─ calc.html
│ ├─ pitch.html
│ ├─ gamescore.html
│ └─ pythag.html
└─ .gitignore


## ⚙️ Setup
```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python run.py


🌍 Deploy (Render)

Build: pip install -r requirements.txt

Start: gunicorn run:app

Env: PYTHAG_CSV_URL (Google Sheets published CSV)

## C. 커밋/푸시
```bash
git add README_en.md README.md
git commit -m "docs: add English README + language switcher"
git push origin main