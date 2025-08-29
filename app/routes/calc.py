from flask import Blueprint, render_template, request

bp = Blueprint("calc", __name__)

# ▼▼▼ 타자 프리셋 정의 (예시 값: 반드시 실제 시즌 상수로 갱신해서 쓰세요) ▼▼▼
PRESETS = {
    "kbo_2025_example": {
        "label": "KBO 2025 (진행중)",
        "lgwOBA": 0.337,
        "wOBAScale": 1.176,
        "lgRperPA": 0.1196,
        "lgwRCperPA_noP": 0.1196,
        "lgOBP": 0.337,          # OPS+ 참고용
        "lgSLG": 0.385           # OPS+ 참고용
    },
    "kbo_2024_example": {
        "label": "KBO 2024 (반영완료)",
        "lgwOBA": 0.352,
        "wOBAScale": 1.093,
        "lgRperPA": 0.1352,
        "lgwRCperPA_noP": 0.1352,
        "lgOBP": 0.352,
        "lgSLG": 0.420
    }
}
# ▲▲▲ 프리셋 정의 끝 ▲▲▲

# 등급 구간(내림차순 검사)
_GRADE_BINS = [
    (160, ("Excellent", "bg-emerald-600 text-white")),
    (140, ("Great", "bg-green-600 text-white")),
    (115, ("Above Average", "bg-sky-600 text-white")),
    (100, ("Average", "bg-slate-500 text-white")),
    (80,  ("Below Average", "bg-amber-600 text-white")),
    (75,  ("Poor", "bg-orange-700 text-white")),
    (-10**9, ("Awful", "bg-red-700 text-white")),
]

def _grade(v):
    if v is None:
        return None, "bg-slate-300 text-slate-700"
    try:
        x = int(round(float(v)))
    except Exception:
        return None, "bg-slate-300 text-slate-700"
    for th, label in _GRADE_BINS:
        if x >= th:
            return label
    return _GRADE_BINS[-1][1]


def _to_int(v, default=0):
    try:
        return int(v) if v not in (None, "") else default
    except ValueError:
        return default


def _to_float(v):
    try:
        if v in (None, ""):
            return None
        return float(v)
    except ValueError:
        return None


def _pf_norm(v):
    """PF 관용 처리:
    - 95/100/105 처럼 100 스케일이면 0.95/1.00/1.05로 변환
    - 0.95~1.05 같은 소수면 그대로 사용
    - 비어 있으면 1.0
    """
    f = _to_float(v)
    if f is None:
        return 1.0
    return f/100.0 if f > 2.5 else f


@bp.route("/", methods=["GET", "POST"])
@bp.route("/calc", methods=["GET", "POST"])
def calc():
    field_keys = [
        # 개인 성적(OPS·PA용)
        "AB","BB","HBP","SF","H","2B","3B","HR","IBB",
        # OPS+ 리그 평균
        "lgOBP","lgSLG",
        # wRC/wRC+ 상수
        "lgwOBA","wOBAScale","lgRperPA","PF",
        # 분모 기준선: 리그 wRC/PA (투수 제외)
        "lgwRCperPA_noP",
        # (선택) 개인 wOBA 직접 입력, (백업) 이벤트 가중치
        "wOBA_input","wBB","wHBP","w1B","w2B","w3B","wHR",
    ]
    vals = {k: request.form.get(k, "") for k in field_keys}

    results = None
    if request.method == "POST":
        # ---------------- 기본 합계 ----------------
        AB = _to_int(vals['AB']); BB = _to_int(vals['BB'])
        HBP = _to_int(vals['HBP']); SF = _to_int(vals['SF'])
        H = _to_int(vals['H']); double = _to_int(vals['2B'])
        triple = _to_int(vals['3B']); HR = _to_int(vals['HR'])
        IBB = _to_int(vals['IBB'])

        PA = AB + BB + HBP + SF
        single = max(H - double - triple - HR, 0)
        TB = single + 2*double + 3*triple + 4*HR
        obp_den = AB + BB + HBP + SF
        OBP = (H + BB + HBP) / obp_den if obp_den > 0 else 0.0
        SLG = TB / AB if AB > 0 else 0.0
        OPS = OBP + SLG

        PF = _pf_norm(vals["PF"])  # 정규화된 PF

        # ---------------- OPS+ (참고) ----------------
        # OPS+ = 100/PF * (OBP/lgOBP + SLG/lgSLG - 1)
        lgOBP = _to_float(vals['lgOBP']); lgSLG = _to_float(vals['lgSLG'])
        OPS_plus = None
        if lgOBP and lgSLG and lgOBP > 0 and lgSLG > 0 and PF > 0:
            OPS_plus = (100.0 / PF) * ((OBP / lgOBP) + (SLG / lgSLG) - 1.0)

        # ---------------- wOBA 결정 ----------------
        wOBA = _to_float(vals.get("wOBA_input"))
        if wOBA is None:
            # 백업: 이벤트 가중치로 wOBA 추정
            wBB = _to_float(vals["wBB"]); wHBP_w = _to_float(vals["wHBP"])
            w1B = _to_float(vals["w1B"]); w2B = _to_float(vals["w2B"])
            w3B = _to_float(vals["w3B"]); wHR_w = _to_float(vals["wHR"])
            UBB = max(BB - IBB, 0)
            PA_woba = AB + UBB + HBP + SF
            if all(x is not None for x in (wBB, wHBP_w, w1B, w2B, w3B, wHR_w)) and PA_woba > 0:
                num = (wBB*UBB) + (wHBP_w*HBP) + (w1B*single) + (w2B*double) + (w3B*triple) + (wHR_w*HR)
                wOBA = num / PA_woba

        # ---------------- wRAA / wRC / wRC+ ----------------
        lgwOBA = _to_float(vals["lgwOBA"])
        wOBAScale = _to_float(vals["wOBAScale"])
        lgRperPA = _to_float(vals["lgRperPA"])
        lgwRCperPA_noP = _to_float(vals["lgwRCperPA_noP"])  # 분모 기준선

        wRAA = None; wRC = None; wRC_plus = None
        if (wOBA is not None and None not in (lgwOBA, wOBAScale, lgRperPA) and PA > 0 and
            (wOBAScale and lgRperPA) and lgwRCperPA_noP and lgwRCperPA_noP > 0):
            # 1) wRAA = ((wOBA - lgwOBA) / wOBAScale) * PA
            wRAA = ((wOBA - lgwOBA) / wOBAScale) * PA
            # 2) wRC = (((wOBA - lgwOBA)/wOBAScale) + lgRperPA) * PA
            wRC  = (((wOBA - lgwOBA) / wOBAScale) + lgRperPA) * PA
            # 3) wRC+ = (((wRAA/PA + lgR/PA) + (lgR/PA − PF*lgR/PA)) / (wRC/PA_exclP)) * 100
            top = (wRAA / PA + lgRperPA) + (lgRperPA - PF * lgRperPA)  # = (wRAA/PA) + lgRperPA*(2 - PF)
            wRC_plus = (top / lgwRCperPA_noP) * 100.0

        # ---- 등급 라벨 계산 ----
        ops_grade, ops_class = _grade(OPS_plus)
        wrc_grade, wrc_class = _grade(wRC_plus)

        results = {
            "PA": PA,
            "OBP": OBP, "SLG": SLG, "OPS": OPS, "OPS_plus": OPS_plus,
            "wOBA": wOBA, "wRAA": wRAA, "wRC": wRC, "wRC_plus": wRC_plus,
            "PF_norm": PF,
            "ops_grade": ops_grade, "ops_class": ops_class,
            "wrc_grade": wrc_grade, "wrc_class": wrc_class,
        }

    # ▼ 프리셋 전달
    return render_template("calc.html", vals=vals, results=results, presets=PRESETS)