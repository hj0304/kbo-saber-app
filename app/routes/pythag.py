import os
import time
import pandas as pd
from flask import Blueprint, render_template, request

bp = Blueprint("pythag", __name__)

# ===== 설정 =====
DATA_CSV_URL = os.environ.get("PYTHAG_CSV_URL")   # Google Sheets CSV 공개 URL
DATA_XLSX    = os.environ.get("PYTHAG_XLSX")      # (선택) 엑셀 파일 경로
SEASON_GAMES = 144                                # KBO 정규시즌 총 경기 수

# 간단 캐시(외부 CSV 안정화 + 성능)
_CACHE = {"df": None, "ts": 0.0}
CACHE_SEC = 30 * 60  # 30분


def _pick_col(df: pd.DataFrame, candidates, default=None):
    cols = set(map(str, df.columns))
    for c in candidates:
        if c in cols:
            return c
    return default


def load_dataframe() -> pd.DataFrame:
    now = time.time()
    if _CACHE["df"] is not None and (now - _CACHE["ts"]) < CACHE_SEC:
        return _CACHE["df"]

    if DATA_CSV_URL:
        cache_tag = f"t={int(now // 3600)}"
        url = f"{DATA_CSV_URL}&{cache_tag}" if ("?" in DATA_CSV_URL) else f"{DATA_CSV_URL}?{cache_tag}"
        df = pd.read_csv(url)
    elif DATA_XLSX:
        df = pd.read_excel(DATA_XLSX, sheet_name=0)
    else:
        raise RuntimeError("데이터 소스가 설정되지 않았습니다. PYTHAG_CSV_URL 또는 PYTHAG_XLSX 환경변수를 지정하세요.")

    _CACHE["df"] = df
    _CACHE["ts"] = now
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

    # 보기/정렬 모드: actual | pythag | proj
    sort_by = getv("sort", "actual")
    if sort_by not in ("actual", "pythag", "proj"):
        sort_by = "actual"

    rows = []
    err = None
    has_projection = False

    try:
        df = load_dataframe()

        # ---- 컬럼 자동 매핑 ----
        col_team = _pick_col(df, ["팀명", "팀", "Team", "TEAM"], "팀명")
        col_rs   = _pick_col(df, ["득점", "RS", "Runs Scored"], "득점")
        col_ra   = _pick_col(df, ["실점", "RA", "Runs Allowed"], "실점")
        col_gp   = _pick_col(df, ["경기수", "G", "Games"], "경기수")
        col_w    = _pick_col(df, ["승", "W", "Wins"], "승")
        col_d    = _pick_col(df, ["무", "T", "Draws", "Ties"])  # 선택
        col_l    = _pick_col(df, ["패", "L", "Losses"], "패")
        col_pct  = _pick_col(df, ["승률", "PCT", "Win%", "WinPct"], "승률")

        # 피타고리안 승률(현재 비교용)은 계속 계산
        # 예상 탭용 "예상 승률"은 반드시 시트의 전용 컬럼을 사용
        col_proj_pct = _pick_col(
            df,
            ["시즌 종료 시 예상 승률", "시즌종료시예상승률", "예상승률", "예상 승률", "Projected Win%", "ProjPct"]
        )
        col_proj_rank = _pick_col(
            df,
            ["시즌 종료 시 예상 순위", "시즌종료시예상순위", "예상순위", "예상 순위", "Projected Rank", "ProjRank"]
        )
        has_projection = col_proj_pct is not None  # 예상 탭 활성화 조건: "시즌 종료 시 예상 승률" 컬럼 존재

        # ---- 행 구성 ----
        rsra_any = False  # 현재 피타고 계산용 체크(표시 목적)
        for _, row in df.iterrows():
            team = row.get(col_team, "-")
            rs = to_f(row.get(col_rs, float("nan")))
            ra = to_f(row.get(col_ra, float("nan")))
            if rs == rs and ra == ra:
                rsra_any = True

            gp = row.get(col_gp, "-")
            w  = row.get(col_w, "-")
            d  = row.get(col_d, 0) if col_d else 0
            l  = row.get(col_l, "-")
            actual_pct = to_f(row.get(col_pct, float("nan")))

            # 현재 비교용 피타고 승률
            calc_pct = pythag_win_pct(rs, ra, exp)

            item = {
                "team": team,
                "gp": gp, "w": w, "d": d, "l": l,
                "rs": rs, "ra": ra,
                "actual_pct": actual_pct,
                "calc_pct": calc_pct,
                "diff": (calc_pct - actual_pct) if (calc_pct == calc_pct and actual_pct == actual_pct) else float("nan"),
            }

            # 시즌 종료 시 예측: 예상 승률 = 시트 컬럼 그대로 사용
            if has_projection:
                proj_pct = to_f(row.get(col_proj_pct, float("nan")))
                d_now = to_i0(d)
                games = max(SEASON_GAMES - d_now, 0)

                if proj_pct == proj_pct:
                    proj_w = int(round(games * proj_pct))
                    proj_l = int(games - proj_w)
                else:
                    proj_w, proj_l = "-", "-"

                item["proj_pct"] = proj_pct
                item["proj_w"]   = proj_w
                item["proj_d"]   = d_now
                item["proj_l"]   = proj_l
                # 시트에 예상 순위가 있으면 표시용으로 보관
                item["proj_rank_src"] = row.get(col_proj_rank, "-") if col_proj_rank else "-"

            rows.append(item)

        # ---- 승차(GB): 선두 현재 승률 기준 ----
        leader = None
        valid_actual = [r for r in rows if r["actual_pct"] == r["actual_pct"]]
        if valid_actual:
            leader = max(valid_actual, key=lambda x: x["actual_pct"])
        elif rsra_any:
            valid_calc = [r for r in rows if r["calc_pct"] == r["calc_pct"]]
            leader = max(valid_calc, key=lambda x: x["calc_pct"]) if valid_calc else None

        leadW = to_f(leader["w"]) if leader else float("nan")
        leadL = to_f(leader["l"]) if leader else float("nan")

        for r in rows:
            wv = to_f(r["w"])
            lv = to_f(r["l"])
            if (leadW == leadW) and (leadL == leadL) and (wv == wv) and (lv == lv):
                r["gb"] = ((leadW - wv) + (lv - leadL)) / 2
            else:
                r["gb"] = float("nan")

        # ---- 정렬 & 순위 부여 ----
        if sort_by == "pythag":
            rows.sort(key=lambda x: (x["calc_pct"] if x["calc_pct"] == x["calc_pct"] else -1), reverse=True)
        elif sort_by == "proj" and has_projection:
            # 예상 순위가 시트에 있으면 그걸로(숫자 오름차순), 없으면 예상 승률 내림차순
            def to_rank(v):
                try:
                    return int(v)
                except Exception:
                    return 10**9
            if any(r.get("proj_rank_src") not in (None, "-", "") for r in rows):
                rows.sort(key=lambda x: to_rank(x.get("proj_rank_src")))
            else:
                rows.sort(key=lambda x: (x.get("proj_pct") if x.get("proj_pct") == x.get("proj_pct") else -1), reverse=True)
        else:
            rows.sort(key=lambda x: (x["actual_pct"] if x["actual_pct"] == x["actual_pct"] else -1), reverse=True)

        for i, r in enumerate(rows, start=1):
            r["rank"] = i

    except Exception as e:
        err = str(e)

    return render_template(
        "pythag.html",
        exp=exp,
        rows=rows,
        err=err,
        sort_by=sort_by,
        has_projection=has_projection
    )
