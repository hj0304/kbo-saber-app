⚾ KBO Saber App

KBO 리그 데이터를 기반으로 다양한 세이버메트릭스 지표를 계산하고 시각화할 수 있는 웹 애플리케이션입니다.
Flask 기반으로 구현하였습니다.

🚀 주요 기능
🥎 타자 계산기

- OPS, OPS+ 계산

- wRC, wRC+ 계산

- 리그 상수, 파크팩터 입력 지원

- 프리셋(리그 평균 값) 지원

- 결과 스케일(Excellent, Great, Average…) 안내 표 제공

⚾ 투수 계산기

- ERA-, FIP-, xFIP- 계산

- 리그 ERA/FIP/xFIP 프리셋 지원

- 파크팩터 보정 적용

- 성적 수준에 따른 색상 배지

📊 게임스코어 계산기

- Bill James의 Game Score

- Tom Tango의 Game Score v2.0

- 투구 기록 입력 시 자동 계산

📈 실시간 피타고리안 승률

- 구글 시트 CSV 연동 (매 30분 캐싱)

- 현재 승률, 피타고리안 승률 비교

- 차이(±), 승차(GB) 표시

- 시즌 종료 시 예상 순위/승·무·패/승률 계산

- 지수 선택 가능 (기본 2.00, Baseball-reference 1.83 등)

📂 프로젝트 구조
kbo-saber-app/
├─ run.py                # 앱 실행 진입점
├─ requirements.txt      # 패키지 의존성
├─ app/
│  ├─ __init__.py        # Flask 앱 팩토리
│  ├─ routes/
│  │  ├─ calc.py         # 타자 지표 계산
│  │  ├─ pitch.py        # 투수 지표 계산
│  │  ├─ gamescore.py    # 게임스코어 계산
│  │  └─ pythag.py       # 피타고리안 승률 계산
│  └─ templates/         # Jinja2 템플릿
│     ├─ base.html
│     ├─ calc.html
│     ├─ pitch.html
│     ├─ gamescore.html
│     └─ pythag.html
└─ .gitignore

⚙️ 설치 & 실행
1. 가상환경 생성
python -m venv .venv
.\.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Mac/Linux

2. 패키지 설치
pip install -r requirements.txt

3. 실행
python run.py


브라우저에서 http://127.0.0.1:5000 접속

🌍 배포(Render)

GitHub에 Push

Render에서 Web Service 생성

Build Command:

pip install -r requirements.txt


Start Command:

gunicorn run:app


Environment Variables에 아래 항목 추가:

PYTHAG_CSV_URL : 구글 시트 CSV 공개 URL

기타 .env 변수들

📊 사용 기술

Python 3.12+

Flask 3.x

Gunicorn

Pandas

TailwindCSS

Render (Deployment)

Google Sheets (CSV 연동)


📌 TODO / 향후 계획

WAR 계산기 추가

타자/투수 프리셋 자동 불러오기

팀별/선수별 데이터 시각화 대시보드

사용자 입력 결과 저장/비교 기능
