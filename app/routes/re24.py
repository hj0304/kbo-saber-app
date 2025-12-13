from flask import Blueprint, render_template, request

bp = Blueprint("re24", __name__)

# KBO 2021-2025 시즌 평균 기대 득점(Run Expectancy) 매트릭스
# (새로 제공해주신 HTML 테이블 데이터 기준)
# 키: "{아웃}_{주자상태(1루=1, 2루=2, 3루=3)}"
RE_MATRIX = {
    # 0 아웃
    "0_0": 0.5064,  # 주자 없음
    "0_1": 0.9004,  # 1루
    "0_2": 1.1354,  # 2루
    "0_3": 1.4329,  # 3루
    "0_12": 1.5295, # 1, 2루
    "0_13": 1.7628, # 1, 3루
    "0_23": 2.0144, # 2, 3루
    "0_123": 2.4667, # 만루
    # 1 아웃
    "1_0": 0.2707,
    "1_1": 0.5432,
    "1_2": 0.7228,
    "1_3": 1.0095,
    "1_12": 1.0101,
    "1_13": 1.2254,
    "1_23": 1.4812,
    "1_123": 1.7139,
    # 2 아웃
    "2_0": 0.1101,
    "2_1": 0.2473,
    "2_2": 0.3785,
    "2_3": 0.4160,
    "2_12": 0.4940,
    "2_13": 0.5766,
    "2_23": 0.6698,
    "2_123": 0.9217,
}

# RE24 시즌 총합 등급표 (제공해주신 이미지 기반 - 타자)
# Rules of Thumb (Hitters)
RATING_TABLE_HITTERS = [
    ("Excellent", 45),
    ("Great", 30),
    ("Above Average", 15),
    ("Average", 0),
    ("Below Average", -5),
    ("Poor", -10),
    ("Awful", -20),
]

# --- 템플릿 렌더링용 헬퍼 ---
# (RE_MATRIX를 3x8 테이블로 변환)
def get_matrix_for_template():
    table = []
    bases = [
        ("0", "주자 없음"), ("1", "1루"), ("2", "2루"), ("3", "3루"),
        ("12", "1,2루"), ("13", "1,3루"), ("23", "2,3루"), ("123", "만루")
    ]
    for out_count in range(3):
        row = []
        for base_key, base_label in bases:
            key = f"{out_count}_{base_key}"
            row.append({
                "key": key,
                "label": base_label,
                "value": RE_MATRIX.get(key, 0.0)
            })
        table.append({"out": f"{out_count} 아웃", "states": row})
    return table, bases

# --- 폼 선택 옵션 ---
OUT_STATES = [(0, "0 아웃"), (1, "1 아웃"), (2, "2 아웃")]
BASE_STATES = [
    ("0", "주자 없음"), ("1", "1루"), ("2", "2루"), ("3", "3루"),
    ("12", "1,2루"), ("13", "1,3루"), ("23", "2,3루"), ("123", "만루")
]
AFTER_OUT_STATES = OUT_STATES + [(3, "3 아웃 (이닝 종료)")]
RUNS_SCORED = [(i, f"{i}점") for i in range(5)] # 0~4점


@bp.route("/", methods=["GET", "POST"])
def re24_calc():
    re_matrix_table, _ = get_matrix_for_template()
    vals = {
        "before_outs": "0",
        "before_bases": "0",
        "after_outs": "0",
        "after_bases": "0",
        "runs_scored": "0"
    }
    re24_value = None

    if request.method == "POST":
        vals = request.form.to_dict()
        try:
            # 1. 이전 상황 기대 득점 (RE_before)
            before_key = f"{vals.get('before_outs')}_{vals.get('before_bases')}"
            re_before = RE_MATRIX.get(before_key, 0.0)

            # 2. 이후 상황 기대 득점 (RE_after)
            after_outs = int(vals.get('after_outs', 0))
            if after_outs == 3:
                re_after = 0.0  # 이닝 종료 시 기대 득점은 0
            else:
                after_key = f"{vals.get('after_outs')}_{vals.get('after_bases')}"
                re_after = RE_MATRIX.get(after_key, 0.0)
            
            # 3. 해당 플레이로 얻은 득점
            runs = int(vals.get('runs_scored', 0))

            # 4. RE24 = (RE_after + Runs) - RE_before
            re24_value = (re_after + runs) - re_before

        except Exception:
            re24_value = None # 오류 시 None 처리

    return render_template(
        "re24.html",
        vals=vals,
        re24_value=re24_value,
        # --- 폼 옵션 전달 ---
        out_states=OUT_STATES,
        base_states=BASE_STATES,
        after_out_states=AFTER_OUT_STATES,
        runs_scored_options=RUNS_SCORED,
        # --- 하단 표 데이터 전달 ---
        re_matrix_table=re_matrix_table,
        rating_table=RATING_TABLE_HITTERS
    )