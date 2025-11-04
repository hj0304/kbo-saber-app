import os
import time
import pandas as pd
from flask import Blueprint, render_template, request

bp = Blueprint("pythag", __name__)

# ===== 설정 =====
DATA_XLSX = os.environ.get("PYTHAG_XLSX")      # (선택) 엑셀 파일 경로
SEASON_GAMES = 144                                # KBO 정규시즌 총 경기 수 (기본값)

# ▼▼▼ 시즌별 데이터 프리셋 (URL) ▼▼▼
# .env 파일에서 각 시즌 URL을 불러오도록 수정
PYTHAG_PRESETS = {
    "kbo_2026": {
        "label": "KBO 2026 (준비중)",
        "url": os.environ.get("PYTHAG_CSV_URL_2026"),
        "season_games": 144,
    },
    "kbo_2025": {
        "label": "KBO 2025",
        "url": os.environ.get("PYTHAG_CSV_URL_2025"),
        "season_games": 144,
    },
    "kbo_2024": {
        "label": "KBO 2024",
        "url": os.environ.get("PYTHAG_CSV_URL_2024"),
        "season_games": 144,
    }
}
# ▲▲▲ 프리셋 끝 ▲▲▲

# 간단 캐시(외부 CSV 안정화 + 성능)
_CACHE = {"df": None, "ts": 0.0, "url": ""}
CACHE_SEC = 30 * 60  # 30분


def _pick_col(df: pd.DataFrame, candidates, default=None):
    cols = set(map(str, df.columns))
    for c in candidates:
        if c in cols:
            return c
    return default


def load_dataframe(url: str) -> pd.DataFrame:
    now = time.time()
    # URL이 변경되면 캐시를 초기화
    if _CACHE["df"] is not None and (now - _CACHE["ts"]) < CACHE_SEC and _CACHE["url"] == url:
        return _CACHE["df"]

    if url and "docs.google.com" in url:
        cache_tag = f"t={int(now // 3600)}"
        fetch_url = f"{url}&{cache_tag}" if ("?" in url) else f"{url}?{cache_tag}"
        df = pd.read_csv(fetch_url)
    elif url and url.endswith(".xlsx"):
        df = pd.read_excel(url, sheet_name=0)
    elif DATA_XLSX:  # URL이 없을 경우 기존 .env의 XLSX 경로를 예비로 사용
        df = pd.read_excel(DATA_XLSX, sheet_name=0)
    else:
        raise RuntimeError("데이터 소스가 설정되지 않았습니다. 프리셋을 선택하거나 PYTHAG_CSV_URL 환경변수를 지정하세요.")

    _CACHE["df"] = df
    _CACHE["ts"] = now
    _CACHE["url"] = url
    return df


def to_f(x):
    try:
        return float(x)
    except Exception:
        return float("nan")


def to_i0(x) -> int:
    try:
        if x == x and x is not None and x != "-":
            return int(round(float(x)))
    except Exception:
        pass
    return 0


def pythag_win_pct(rs: float, ra: float, exp: float = 2.0) -> float:
    if rs < 0 or ra < 0:
        return float("nan")
    rs_e = rs ** exp
    ra_e = ra ** exp
    denom = rs_e + ra_e
    return (rs_e / denom) if denom > 0 else float("nan")


@bp.route("/pythag", methods=["GET", "POST"])
def pythag():
    getv = request.values.get
    try:
        exp = float(getv("exp", "2.0"))
    except Exception:
        exp = 2.0

    # --- 프리셋 & 데이터 소스 결정 ---
    preset_key = getv("preset", "live")
    data_url = None
    season_games = SEASON_GAMES  # 기본값

    if preset_key == "live":
        # 'live'는 .env 파일의 기본 URL을 사용
        data_url = os.environ.get("PYTHAG_CSV_URL")
    elif preset_key in PYTHAG_PRESETS:
        preset_data = PYTHAG_PRESETS[preset_key]
        data_url = preset_data.get("url")
        season_games = preset_data.get("season_games", SEASON_GAMES)

    # 보기/정렬 모드: actual | pythag | proj
    sort_by = getv("sort", "actual")
    if sort_by not in ("actual", "pythag", "proj"):
        sort_by = "actual"

    rows = []
    err = None
    has_projection = False

    try:
        if not data_url:
            raise RuntimeError("선택된 프리셋의 데이터 URL이 유효하지 않거나, PYTHAG_CSV_URL이 .env에 설정되지 않았습니다.")
        df = load_dataframe(data_url)

        # ---- 컬럼 자동 매핑 ----
        col_team = _pick_col(df, ["팀명", "팀", "Team", "TEAM"], "팀명")
        col_rs   = _pick_col(df, ["득점", "RS", "Runs Scored"], "득점")
        col_ra   = _pick_col(df, ["실점", "RA", "Runs Allowed"], "실점")
        col_gp   = _pick_col(df, ["경기수", "G", "Games"], "경기수")
        col_w    = _pick_col(df, ["승", "W", "Wins"], "승")
        col_d    = _pick_col(df, ["무", "T", "Draws", "Ties"])
        col_l    = _pick_col(df, ["패", "L", "Losses"], "패")
        col_pct  = _pick_col(df, ["승률", "PCT", "Win%", "WinPct"], "승률")
        col_proj_pct = _pick_col(df, ["시즌 종료 시 예상 승률", "시즌종료시예상승률", "예상승률", "예상 승률"])
        col_proj_rank = _pick_col(df, ["시즌 종료 시 예상 순위", "시즌종료시예상순위", "예상순위", "예상 순위"])
        has_projection = col_proj_pct is not None

        # ---- 행 구성 ----
        rsra_any = False
        for _, row in df.iterrows():
            team = row.get(col_team, "-")
            rs = to_f(row.get(col_rs, float("nan"))); ra = to_f(row.get(col_ra, float("nan")))
            if rs == rs and ra == ra: rsra_any = True

            gp = row.get(col_gp, "-"); w  = row.get(col_w, "-")
            d  = row.get(col_d, 0) if col_d else 0; l  = row.get(col_l, "-")
            actual_pct = to_f(row.get(col_pct, float("nan")))
            calc_pct = pythag_win_pct(rs, ra, exp)
            item = { "team": team, "gp": gp, "w": w, "d": d, "l": l, "rs": rs, "ra": ra,
                     "actual_pct": actual_pct, "calc_pct": calc_pct,
                     "diff": (actual_pct - calc_pct) if (calc_pct == calc_pct and actual_pct == actual_pct) else float("nan"), }

            if has_projection:
                proj_pct = to_f(row.get(col_proj_pct, float("nan")))
                d_now = to_i0(d)
                games = max(season_games - d_now, 0) # 시즌 총 경기수 사용
                if proj_pct == proj_pct:
                    proj_w = int(round(games * proj_pct)); proj_l = int(games - proj_w)
                else:
                    proj_w, proj_l = "-", "-"
                item.update({"proj_pct": proj_pct, "proj_w": proj_w, "proj_d": d_now, "proj_l": proj_l,
                             "proj_rank_src": row.get(col_proj_rank, "-") if col_proj_rank else "-"})
            rows.append(item)

        # ---- 승차(GB) 계산 ----
        leader = None
        valid_actual = [r for r in rows if r["actual_pct"] == r["actual_pct"]]
        if valid_actual: leader = max(valid_actual, key=lambda x: x["actual_pct"])
        elif rsra_any: valid_calc = [r for r in rows if r["calc_pct"] == r["calc_pct"]]; leader = max(valid_calc, key=lambda x: x["calc_pct"]) if valid_calc else None
        leadW = to_f(leader["w"]) if leader else float("nan"); leadL = to_f(leader["l"]) if leader else float("nan")
        for r in rows:
            wv = to_f(r["w"]); lv = to_f(r["l"])
            r["gb"] = ((leadW - wv) + (lv - leadL)) / 2 if (leadW == leadW and leadL == leadL and wv == wv and lv == lv) else float("nan")

        # ---- 정렬 & 순위 부여 ----
        if sort_by == "pythag": rows.sort(key=lambda x: (x["calc_pct"] if x["calc_pct"] == x["calc_pct"] else -1), reverse=True)
        elif sort_by == "proj" and has_projection:
            def to_rank(v):
                try: return int(v)
                except Exception: return 10**9
            if any(r.get("proj_rank_src") not in (None, "-", "") for r in rows): rows.sort(key=lambda x: to_rank(x.get("proj_rank_src")))
            else: rows.sort(key=lambda x: (x.get("proj_pct") if x.get("proj_pct") == x.get("proj_pct") else -1), reverse=True)
        else: rows.sort(key=lambda x: (x["actual_pct"] if x["actual_pct"] == x["actual_pct"] else -1), reverse=True)
        for i, r in enumerate(rows, start=1): r["rank"] = i

    except Exception as e:
        err = str(e)

    return render_template(
        "pythag.html",
        exp=exp,
        rows=rows,
        err=err,
        sort_by=sort_by,
        has_projection=has_projection,
        presets=PYTHAG_PRESETS,
        preset_key=preset_key
    )
