# project_spec.md 1절 매장 정의를 옮긴 설정 파일
# "# 가정" 표시는 코딩 AI가 제안해 정한 값으로, 실제 값을 알게 되면 바꿈

# ── 매장 이름과 업종 ──
STORE_NAME = "SMIT 베이커리"
STORE_TYPE = "동네 빵집"

# ── 위치와 상권 ──
LOCATION = "서울시 마포구 상암동, MBC 근처(DMC 단지 안)"
TRADE_AREA = "오피스와 아파트 주거지가 섞인 복합 상권, 평일은 직장인, 저녁·주말은 주민 중심"  # 가정

# ── 주고객 ──
MAIN_CUSTOMERS = {
    "office_workers": "평일 아침·점심, 20대 후반~40대 방송·미디어·IT 직장인, 샌드위치·간식빵",  # 가정
    "residents": "저녁·주말, 30~40대 아파트 주민(맞벌이·자녀 있는 가구), 식빵·간식빵",  # 가정
}

# ── 반복되는 결정과 행동 후보 ──
# 결정 : 오늘 빵 종류별로 몇 개를 구울지
# 행동 : 종류별 개수를 범위 안의 연속값으로 고르고 반올림해 정수 개수로 구움
BREAD_TYPES = ["sandwich", "snack_bread", "loaf_bread"]  # 샌드위치, 간식빵(소금빵·크루아상), 식빵

ACTION_MIN = {"sandwich": 0, "snack_bread": 0, "loaf_bread": 0}      # 가정
ACTION_MAX = {"sandwich": 60, "snack_bread": 200, "loaf_bread": 50}  # 가정 (피크 수요 반영)

# ── 결정 단위 ──
DECISION_UNIT = "store"  # 매장 전체

# ── 영업 시간 ──
BUSINESS_HOURS = {
    "weekday": {"open": "08:00", "close": "21:00"},
    "weekend": {"open": "09:00", "close": "20:00"}
}  # 가정

# ── 가격과 원가율 ──
PRICE = {"sandwich": 6500, "snack_bread": 3800, "loaf_bread": 5500}   # 원, 가정
COST_RATE = {"sandwich": 0.45, "snack_bread": 0.35, "loaf_bread": 0.30}  # 가정
UNIT_COST = {b: PRICE[b] * COST_RATE[b] for b in BREAD_TYPES}  # 개당 원가 = 가격 × 원가율

# ── 남은 빵 처리 ──
# 샌드위치·간식빵은 당일 폐기, 식빵만 다음 날 할인해 한 번 더 판매하고 남으면 폐기
CARRYOVER_BREADS = ["loaf_bread"]  # 가정
CARRYOVER_DISCOUNT = 0.5           # 다음 날 판매 가격 = 원래 가격 × 0.5, 가정

# ── 얻는 것과 잃는 것 ──
# 얻는 것 : 판매 수익(판매 금액 − 원가)
# 잃는 것 : 폐기 손실(버린 빵의 원가), 품절 손실(빵이 떨어져 못 판 만큼의 수익)

# ── 성공 척도 ──
# 주 척도 : 순이익 = 판매 금액 − 그날 구운 빵 전체의 원가 (고정비 제외)
# 보조 지표 : 폐기율, 품절률
MAIN_METRIC = "net_profit"
SUB_METRICS = ["waste_rate", "stockout_rate"]

# ── 결정 주기와 한 판의 길이 ──
DECISIONS_PER_DAY = 1   # 하루 1번, 개점 전
EPISODE_DAYS = 28       # 한 판 = 28일(4주), 28일 동안 쌓인 순이익으로 평가

# ── 학습 및 평가 기간 설정 ──
# 학습 : 2016~2024년 중 28일 시작일을 무작위 샘플링
TRAIN_START_DATE = "2016-01-01"
TRAIN_END_DATE = "2024-12-31"
TRAIN_SEED = 42         # 가정

# 평가 : 2025년 내 서로 겹치지 않는 13개 에피소드 시작일로 평가
EVAL_START_DATE = "2025-01-01"
EVAL_END_DATE = "2025-12-31"
EVAL_EPISODE_START_DATES = [
    "2025-01-01", "2025-01-29", "2025-02-26", "2025-03-26",
    "2025-04-23", "2025-05-21", "2025-06-18", "2025-07-16",
    "2025-08-13", "2025-09-10", "2025-10-08", "2025-11-05",
    "2025-12-03"
]  # 가정 (2025년 28일 기준 비중첩 13개 에피소드)
EVAL_SEEDS = [42, 1004, 2026]  # 가정 (3개 난수 시드로 13개 에피소드 다회차 평가)

# ── 외부 요인 후보 (영향의 크기는 2절에서 정함) ──
EXTERNAL_FACTORS = ["weekday", "holiday", "bad_weather", "local_event"]  # 요일, 공휴일, 궂은 날씨, 근처 행사
