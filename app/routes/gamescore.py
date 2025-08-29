from flask import Blueprint, render_template, request

bp = Blueprint("gamescore", __name__)

# --- Helpers ---

def _to_float(v, default=0.0):
    try:
        if v in (None, ""): return default
        return float(v)
    except ValueError:
        return default

# IP(이닝) → 아웃 수 계산 (6.2 → 20아웃)
# 소수 첫째 자리는 0,1,2만 유효(0=0아웃, 1=1아웃, 2=2아웃)

def ip_to_outs(ip_raw: float) -> int:
    ip_int = int(ip_raw)
    frac = round((ip_raw - ip_int) + 1e-9, 1)
    # 0.0/0.1/0.2 외 값이 들어오면 반올림 오차를 고려하여 보정
    tenth = int(round(frac * 10))
    add_outs = 0
    if tenth == 1:
        add_outs = 1
    elif tenth == 2:
        add_outs = 2
    elif tenth != 0:
        # 예외 입력은 버림 처리
        add_outs = 0
    return ip_int * 3 + add_outs


def outs_to_completed_innings_after_four(outs: int) -> int:
    # 완투한 이닝 수(정수)만 인정, 4이닝 초과분만 카운트
    full_innings = outs // 3
    return max(full_innings - 4, 0)


@bp.route("/gamescore", methods=["GET", "POST"])
def gamescore():
    vals = {k: request.form.get(k, "") for k in [
        "IP", "H", "BB", "K", "ER", "UER", "HR"
    ]}

    results = None
    if request.method == "POST":
        IP = _to_float(vals["IP"])  # 예: 6.2
        H = _to_float(vals["H"])    
        BB = _to_float(vals["BB"])   
        K = _to_float(vals["K"])    
        ER = _to_float(vals["ER"])  
        UER = _to_float(vals["UER"])  # 비자책 실점
        HR = _to_float(vals["HR"])  

        outs = ip_to_outs(IP)
        after4 = outs_to_completed_innings_after_four(outs)
        R = ER + UER

        # Bill James Game Score (오리지널)
        # 50 + 1*outs + 2*(이후 이닝) + 1*K - 2*H - 4*ER - 2*UER - 1*BB
        GS = (
            50
            + outs
            + 2*after4
            + K
            - 2*H
            - 4*ER
            - 2*UER
            - 1*BB
        )

        # Game Score v2 (Tango)
        # 40 + 2*outs + 1*K - 2*BB - 2*H - 3*R - 6*HR
        GSv2 = (
            40
            + 2*outs
            + 1*K
            - 2*BB
            - 2*H
            - 3*R
            - 6*HR
        )

        results = {
            "outs": outs,
            "after4": after4,
            "R": R,
            "GS": GS,
            "GSv2": GSv2,
        }

    return render_template("gamescore.html", vals=vals, results=results)