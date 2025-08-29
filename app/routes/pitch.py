from flask import Blueprint, render_template, request

bp = Blueprint("pitch", __name__)

# ▼▼▼ 리그 프리셋 (예시 값) ▼▼▼
PRESETS_PITCH = {
    "kbo_2025_example": {
        "label": "KBO 2025 (진행중)",
        "lgERA": 4.22,
        "lgFIP": 4.18,
        "lgxFIP": 3.20
    },
    "kbo_2024_example": {
        "label": "KBO 2024 (반영완료)",
        "lgERA": 4.91,
        "lgFIP": 4.79,
        "lgxFIP": 3.58
    },
}
# ▲▲▲ 프리셋 끝 ▲▲▲

def _to_float(v):
    try:
        if v in (None, ""): return None
        return float(v)
    except ValueError:
        return None

def _pf_percent(v):
    """입력 PF를 100 스케일로 환산.
    - 0.888, 1.000, 1.045 같은 소수 → 88.8, 100.0, 104.5 로 변환
    - 95, 100, 105 같은 정수/백분값 → 그대로 사용
    """
    f = _to_float(v)
    if f is None: return 100.0
    return f*100.0 if f <= 2.5 else f

# ERA-/FIP-/xFIP- 등급 (값이 낮을수록 좋음)
_MINUS_GRADE_BINS = [
    (70,  ("Excellent",     "bg-emerald-600 text-white")),
    (80,  ("Great",         "bg-green-600 text-white")),
    (90,  ("Above Average", "bg-sky-600 text-white")),
    (100, ("Average",       "bg-slate-500 text-white")),
    (110, ("Below Average", "bg-amber-600 text-white")),
    (115, ("Poor",          "bg-orange-700 text-white")),
    (10**9, ("Awful",       "bg-red-700 text-white")),
]

def _minus_grade(v):
    if v is None:
        return None, "bg-slate-300 text-slate-700"
    try:
        x = float(v)
    except Exception:
        return None, "bg-slate-300 text-slate-700"
    for th, label in _MINUS_GRADE_BINS:
        if x <= th:
            return label
    return _MINUS_GRADE_BINS[-1][1]

@bp.route("/", methods=["GET", "POST"])
@bp.route("/calc", methods=["GET", "POST"])
def calc():
    # 입력: 지표 자체(ERA, FIP, xFIP)와 리그 평균, PF
    keys = ["ERA", "lgERA", "FIP", "lgFIP", "xFIP", "lgxFIP", "PF"]
    vals = {k: request.form.get(k, "") for k in keys}
    results = None

    if request.method == "POST":
        ERA   = _to_float(vals["ERA"])
        lgERA = _to_float(vals["lgERA"])
        FIP   = _to_float(vals["FIP"])
        lgFIP = _to_float(vals["lgFIP"])
        xFIP  = _to_float(vals["xFIP"])
        lgxFIP= _to_float(vals["lgxFIP"])
        PFpct = _pf_percent(vals["PF"])  # 100 스케일 (소수 입력 허용)

        def minus_metric(metric, lg_metric):
            # 100 * ((M + (M - M*(PF/100))) / lgM) = 100 * (M*(2 - PF/100)) / lgM
            if metric is None or lg_metric is None or lg_metric <= 0:
                return None
            return 100.0 * (metric + (metric - metric * (PFpct/100.0))) / lg_metric         # == return 100.0 * (metric * (2.0 - (PFpct/100.0))) / lg_metric 

        ERA_minus  = minus_metric(ERA,  lgERA)
        FIP_minus  = minus_metric(FIP,  lgFIP)
        xFIP_minus = minus_metric(xFIP, lgxFIP)

        era_grade,  era_class  = _minus_grade(ERA_minus)
        fip_grade,  fip_class  = _minus_grade(FIP_minus)
        xfip_grade, xfip_class = _minus_grade(xFIP_minus)

        results = {
            "ERA_minus": ERA_minus, "FIP_minus": FIP_minus, "xFIP_minus": xFIP_minus,
            "PF_percent": PFpct,
            "era_grade": era_grade, "era_class": era_class,
            "fip_grade": fip_grade, "fip_class": fip_class,
            "xfip_grade": xfip_grade, "xfip_class": xfip_class,
        }

    return render_template("pitch.html", vals=vals, results=results, presets_pitch=PRESETS_PITCH)
