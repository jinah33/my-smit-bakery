"""
가상 매장 환경 (Gymnasium 표준 환경)
SMIT 베이커리 일별 생산량 결정 시뮬레이션
"""
import os
import random
import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces

import config
from reward import compute_reward_v1

# ══════════════════════════════════════════════════════════════════════════
# 2절 반응 규칙 가정값 묶음 (config.py와 겹치지 않는 규칙 전용 수치)
# ══════════════════════════════════════════════════════════════════════════
# [규칙 1] 품절 시 대체 구매 비율 (가정)
SUBSTITUTE_RATE_SANDWICH = 0.30  # 샌드위치 품절 손님의 30%가 간식빵으로 전환
SUBSTITUTE_RATE_LOAF = 0.20      # 식빵 품절 손님의 20%가 간식빵으로 전환

# [규칙 3] 고객 신뢰도 누적 효과 (가정)
INITIAL_TRUST = 100              # 첫날 신뢰도
TRUST_MIN = 0                    # 신뢰도 최소값
TRUST_MAX = 100                  # 신뢰도 최대값
TRUST_PENALTY = 5                # 10% 초과 품절 또는 25% 초과 폐기 발생 시 감점 (-5)
TRUST_RECOVERY = 2               # 품절 및 과잉 폐기 없는 정상 운영 날 회복 점수 (+2)
STOCKOUT_THRESHOLD_RATIO = 0.10  # 당일 원래 수요의 10% 초과 미판매 시 품절 판정
EXCESS_WASTE_THRESHOLD_RATIO = 0.25  # 당일 구운 빵 대비 폐기량 25% 초과 시 신선도 저하 감점 (가정)

# [규칙 4] 식빵 재고 누적 효과 (가정)
LEFTOVER_LOAF_MAX = 50           # 식빵 재고 상한
DISCOUNT_LOAF_DEMAND_RATIO = 0.50  # 당일 식빵 수요의 50%가 할인 식빵을 먼저 찾음
DISCOUNT_LOAF_PRICE = 2750       # 할인 식빵 판매 가격 (5,500원 × 0.5)

# [규칙 5] 외부 요인 배수 (가정)
# 주말 및 공휴일 배수 (토/일 또는 공휴일)
WEEKEND_HOLIDAY_MULTIPLIER = {
    "sandwich": 0.4,
    "snack_bread": 1.0,
    "loaf_bread": 1.8
}
# 궂은 날씨 배수
BAD_WEATHER_MULTIPLIER = {
    "sandwich": 0.8,
    "snack_bread": 0.8,
    "loaf_bread": 0.8
}
# 근처 행사 확률 및 배수
EVENT_PROBABILITY = 0.10         # 근처 행사 발생 확률 (하루 10%)
EVENT_MULTIPLIER = {
    "sandwich": 1.2,
    "snack_bread": 1.5,
    "loaf_bread": 1.0
}

# [규칙 6] 매일의 우연 (수요 노이즈, 가정)
RANDOM_NOISE_MIN = 0.8
RANDOM_NOISE_MAX = 1.2


class BakeryEnv(gym.Env):
    """
    SMIT 베이커리 강화학습 가상 매장 환경 (Gymnasium 호환)
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, data_dir="data"):
        super().__init__()
        self.data_dir = data_dir

        # ── 1. 고객 성향 데이터 로드 ──
        traits_path = os.path.join(data_dir, "customer_traits.csv")
        if not os.path.exists(traits_path):
            raise FileNotFoundError(f"고객 성향 파일이 없습니다: {traits_path}")
        self.df_traits = pd.read_csv(traits_path)
        self.n_customers = len(self.df_traits)

        # ── 2. 외부 요인 데이터 로드 ──
        ext_path = os.path.join(data_dir, "external_factors.csv")
        if not os.path.exists(ext_path):
            raise FileNotFoundError(f"외부 요인 파일이 없습니다: {ext_path}")
        self.df_ext = pd.read_csv(ext_path)
        self.df_ext["date"] = pd.to_datetime(self.df_ext["date"])
        self.df_ext = self.df_ext.sort_values("date").reset_index(drop=True)

        # ── 3. 상태(Observation) 및 행동(Action) 공간 정의 (4절 설계 카드) ──
        # 관측 7개 수치: [day_of_episode, customer_trust, leftover_loaf, is_weekend, is_holiday, is_bad_weather, is_event]
        # 모든 수치는 0.0 ~ 1.0 범위로 정규화
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(7,),
            dtype=np.float32
        )

        # 연속 행동 3개 (샌드위치 0~60, 간식빵 0~200, 식빵 0~50)
        self.action_space = spaces.Box(
            low=np.array([
                config.ACTION_MIN["sandwich"],
                config.ACTION_MIN["snack_bread"],
                config.ACTION_MIN["loaf_bread"]
            ], dtype=np.float32),
            high=np.array([
                config.ACTION_MAX["sandwich"],
                config.ACTION_MAX["snack_bread"],
                config.ACTION_MAX["loaf_bread"]
            ], dtype=np.float32),
            dtype=np.float32
        )

        # 상태 변수 초기화
        self.current_step = 0
        self.episode_length = config.EPISODE_DAYS
        self.customer_trust = INITIAL_TRUST
        self.leftover_loaf = 0
        self.current_date_idx = 0
        self.cum_profit = 0.0
        self.cum_waste_cost = 0.0
        self.cum_stockout_loss = 0.0
        self.total_baked_units = 0
        self.total_unmet_units = 0
        self.total_demand_units = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # 난수 생성기 초기화
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        else:
            self.rng = np.random.default_rng()

        self.current_step = 0
        self.customer_trust = INITIAL_TRUST
        self.leftover_loaf = 0
        self.cum_profit = 0.0
        self.cum_waste_cost = 0.0
        self.cum_stockout_loss = 0.0
        self.total_baked_units = 0
        self.total_unmet_units = 0
        self.total_demand_units = 0

        # 시작일 설정 (options에 start_date 지정 가능, 미지정 시 학습 기간 내 무작위)
        start_date_str = None
        if options and "start_date" in options:
            start_date_str = options["start_date"]
            start_dt = pd.to_datetime(start_date_str)
            matching = self.df_ext[self.df_ext["date"] == start_dt].index
            if len(matching) == 0:
                raise ValueError(f"시작일 {start_date_str}이 external_factors.csv에 없습니다.")
            self.current_date_idx = matching[0]
        else:
            # 학습 기간(2016-01-01 ~ 2024-12-31) 내에서 28일 에피소드가 끝나도록 시작일 선택
            train_end_dt = pd.to_datetime(config.TRAIN_END_DATE)
            max_start_dt = train_end_dt - pd.Timedelta(days=self.episode_length)
            valid_indices = self.df_ext[
                (self.df_ext["date"] >= pd.to_datetime(config.TRAIN_START_DATE)) &
                (self.df_ext["date"] <= max_start_dt)
            ].index
            self.current_date_idx = int(self.rng.choice(valid_indices))

        # 오늘 외부 요인 중 행사 여부 결정 (하루 10% 확률)
        self.today_is_event = 1 if (self.rng.random() < EVENT_PROBABILITY) else 0

        obs = self._get_observation()
        info = self._get_info()
        return obs, info

    def _get_observation(self):
        # 1. day_of_episode (0.0 ~ 1.0)
        day_norm = self.current_step / max(1, self.episode_length - 1)
        # 2. customer_trust (0.0 ~ 1.0)
        trust_norm = self.customer_trust / float(TRUST_MAX)
        # 3. leftover_loaf (0.0 ~ 1.0)
        loaf_norm = min(1.0, self.leftover_loaf / float(LEFTOVER_LOAF_MAX))

        # 외부 요인 (오늘 날짜)
        row_ext = self.df_ext.iloc[self.current_date_idx]
        is_weekend = float(row_ext["is_weekend"])
        is_holiday = float(row_ext["is_holiday"])
        is_bad_weather = float(row_ext["is_bad_weather"])
        is_event = float(self.today_is_event)

        return np.array([
            day_norm,
            trust_norm,
            loaf_norm,
            is_weekend,
            is_holiday,
            is_bad_weather,
            is_event
        ], dtype=np.float32)

    def _get_info(self):
        curr_row = self.df_ext.iloc[self.current_date_idx]
        return {
            "date": curr_row["date"].strftime("%Y-%m-%d"),
            "step": self.current_step,
            "customer_trust": self.customer_trust,
            "leftover_loaf": self.leftover_loaf,
            "cum_profit": self.cum_profit,
            "is_weekend": curr_row["is_weekend"],
            "is_holiday": curr_row["is_holiday"],
            "is_bad_weather": curr_row["is_bad_weather"],
            "is_event": self.today_is_event
        }

    def step(self, action):
        # ── 1. 행동 반올림 및 정수 생산량 확정 ──
        bake_sandwich = int(np.clip(round(float(action[0])), 0, config.ACTION_MAX["sandwich"]))
        bake_snack = int(np.clip(round(float(action[1])), 0, config.ACTION_MAX["snack_bread"]))
        bake_loaf = int(np.clip(round(float(action[2])), 0, config.ACTION_MAX["loaf_bread"]))

        # ── 2. 외부 환경 배수 계산 (2절 5번 줄) ──
        row_ext = self.df_ext.iloc[self.current_date_idx]
        is_wknd = row_ext["is_weekend"] == 1
        is_hldy = row_ext["is_holiday"] == 1
        is_bad = row_ext["is_bad_weather"] == 1
        is_evnt = self.today_is_event == 1

        mult_sandwich = 1.0
        mult_snack = 1.0
        mult_loaf = 1.0

        # 주말 또는 공휴일
        if is_wknd or is_hldy:
            mult_sandwich *= WEEKEND_HOLIDAY_MULTIPLIER["sandwich"]
            mult_snack *= WEEKEND_HOLIDAY_MULTIPLIER["snack_bread"]
            mult_loaf *= WEEKEND_HOLIDAY_MULTIPLIER["loaf_bread"]

        # 궂은 날씨
        if is_bad:
            mult_sandwich *= BAD_WEATHER_MULTIPLIER["sandwich"]
            mult_snack *= BAD_WEATHER_MULTIPLIER["snack_bread"]
            mult_loaf *= BAD_WEATHER_MULTIPLIER["loaf_bread"]

        # 행사
        if is_evnt:
            mult_sandwich *= EVENT_MULTIPLIER["sandwich"]
            mult_snack *= EVENT_MULTIPLIER["snack_bread"]
            mult_loaf *= EVENT_MULTIPLIER["loaf_bread"]

        # ── 3. 고객 100명 개별 수요 생성 및 합산 (3절) ──
        demand_sw_raw = 0.0
        demand_snack_raw = 0.0
        demand_loaf_raw = 0.0

        for _, cust in self.df_traits.iterrows():
            # 신뢰도가 고객의 품절 인내도보다 낮으면 당일 방문 포기
            if self.customer_trust < cust["stockout_tolerance"]:
                continue

            # 요일 가중치 반영
            wknd_w = cust["weekend_visit_weight"] if (is_wknd or is_hldy) else 1.0

            demand_sw_raw += cust["sandwich_daily_demand"] * wknd_w * mult_sandwich
            demand_snack_raw += cust["snack_bread_daily_demand"] * wknd_w * mult_snack
            demand_loaf_raw += cust["loaf_daily_demand"] * wknd_w * mult_loaf

        # [규칙 6] 매일의 우연 (수요 노이즈 0.8~1.2)
        noise_sw = self.rng.uniform(RANDOM_NOISE_MIN, RANDOM_NOISE_MAX)
        noise_snack = self.rng.uniform(RANDOM_NOISE_MIN, RANDOM_NOISE_MAX)
        noise_loaf = self.rng.uniform(RANDOM_NOISE_MIN, RANDOM_NOISE_MAX)

        total_demand_sw = int(round(demand_sw_raw * noise_sw))
        total_demand_snack = int(round(demand_snack_raw * noise_snack))
        total_demand_loaf = int(round(demand_loaf_raw * noise_loaf))

        # ── 4. 판매 및 즉시 반응 계산 (2절 1, 2, 4번 줄) ──
        # 4.1. 할인 식빵(전날 재고) 판매 (규칙 4)
        discount_loaf_demand = int(round(total_demand_loaf * DISCOUNT_LOAF_DEMAND_RATIO))
        sales_discount_loaf = min(self.leftover_loaf, discount_loaf_demand)
        
        # 오늘 새 식빵 수요
        fresh_loaf_demand = max(0, total_demand_loaf - sales_discount_loaf)

        # 4.2. 샌드위치 판매
        sales_sandwich = min(bake_sandwich, total_demand_sw)
        unmet_sandwich = max(0, total_demand_sw - sales_sandwich)

        # 4.3. 새 식빵 판매
        sales_fresh_loaf = min(bake_loaf, fresh_loaf_demand)
        unmet_fresh_loaf = max(0, fresh_loaf_demand - sales_fresh_loaf)

        # 오늘 남은 새 식빵 -> 내일 반값 재고로 이월 (최대 50개)
        new_leftover_loaf = min(LEFTOVER_LOAF_MAX, max(0, bake_loaf - sales_fresh_loaf))

        # 4.4. 품절 손님의 간식빵 대체 구매 (규칙 1)
        sub_from_sw = int(round(unmet_sandwich * SUBSTITUTE_RATE_SANDWICH))
        sub_from_loaf = int(round(unmet_fresh_loaf * SUBSTITUTE_RATE_LOAF))
        effective_snack_demand = total_demand_snack + sub_from_sw + sub_from_loaf

        sales_snack = min(bake_snack, effective_snack_demand)
        unmet_snack = max(0, effective_snack_demand - sales_snack)

        # 4.5. 당일 폐기량 (샌드위치, 간식빵) (규칙 2)
        waste_sandwich = max(0, bake_sandwich - sales_sandwich)
        waste_snack = max(0, bake_snack - sales_snack)

        # ── 5. 매출, 원가 및 순이익(보상) 계산 (1절 성공 척도) ──
        revenue = (
            sales_sandwich * config.PRICE["sandwich"] +
            sales_snack * config.PRICE["snack_bread"] +
            sales_fresh_loaf * config.PRICE["loaf_bread"] +
            sales_discount_loaf * DISCOUNT_LOAF_PRICE
        )

        # 구운 빵 전체 원가 (할인 식빵은 전날 이미 원가 처리됨, 추가 원가 0)
        baking_cost = (
            bake_sandwich * config.UNIT_COST["sandwich"] +
            bake_snack * config.UNIT_COST["snack_bread"] +
            bake_loaf * config.UNIT_COST["loaf_bread"]
        )

        daily_profit = revenue - baking_cost
        reward = compute_reward_v1(daily_profit, {"step": self.current_step})  # v1 보상: 10만 원 단위 스케일링 순이익

        # 통계 누적
        self.cum_profit += daily_profit
        waste_cost = (
            waste_sandwich * config.UNIT_COST["sandwich"] +
            waste_snack * config.UNIT_COST["snack_bread"]
        )
        self.cum_waste_cost += waste_cost
        
        # 기회손실 (품절로 놓친 이익)
        stockout_loss = (
            unmet_sandwich * (config.PRICE["sandwich"] - config.UNIT_COST["sandwich"]) +
            unmet_snack * (config.PRICE["snack_bread"] - config.UNIT_COST["snack_bread"]) +
            unmet_fresh_loaf * (config.PRICE["loaf_bread"] - config.UNIT_COST["loaf_bread"])
        )
        self.cum_stockout_loss += stockout_loss

        self.total_baked_units += (bake_sandwich + bake_snack + bake_loaf)
        self.total_unmet_units += (unmet_sandwich + unmet_snack + unmet_fresh_loaf)
        self.total_demand_units += (total_demand_sw + total_demand_snack + fresh_loaf_demand)

        # ── 6. 누적 효과 갱신 (규칙 3: 신뢰도 & 규칙 4: 식빵 재고) ──
        # 품절 판정 (원래 수요의 10% 초과 미판매 여부)
        is_sw_stockout = unmet_sandwich > (total_demand_sw * STOCKOUT_THRESHOLD_RATIO)
        is_loaf_stockout = unmet_fresh_loaf > (fresh_loaf_demand * STOCKOUT_THRESHOLD_RATIO)
        # 간식빵 원래 수요 기준 미판매량
        original_snack_unmet = max(0, total_demand_snack - min(bake_snack, total_demand_snack))
        is_snack_stockout = original_snack_unmet > (total_demand_snack * STOCKOUT_THRESHOLD_RATIO)

        has_stockout_today = (is_sw_stockout or is_loaf_stockout or is_snack_stockout)

        # 과잉 폐기 판정 (당일 구운 빵 전체 대비 폐기량 25% 초과 여부)
        total_baked_today = bake_sandwich + bake_snack + bake_loaf
        total_waste_today = waste_sandwich + waste_snack
        is_excess_waste = False
        if total_baked_today > 0:
            is_excess_waste = (total_waste_today / total_baked_today) > EXCESS_WASTE_THRESHOLD_RATIO

        if has_stockout_today or is_excess_waste:
            self.customer_trust = max(TRUST_MIN, self.customer_trust - TRUST_PENALTY)
        else:
            self.customer_trust = min(TRUST_MAX, self.customer_trust + TRUST_RECOVERY)

        self.leftover_loaf = new_leftover_loaf

        # ── 7. 스텝 진행 및 종료 판정 ──
        self.current_step += 1
        self.current_date_idx += 1

        # 다음 날 행사 여부 추첨
        self.today_is_event = 1 if (self.rng.random() < EVENT_PROBABILITY) else 0

        terminated = bool(self.current_step >= self.episode_length)
        truncated = False

        obs = self._get_observation()
        info = self._get_info()
        info.update({
            "daily_profit": daily_profit,
            "revenue": revenue,
            "baking_cost": baking_cost,
            "waste_sandwich": waste_sandwich,
            "waste_snack": waste_snack,
            "unmet_sandwich": unmet_sandwich,
            "unmet_snack": unmet_snack,
            "unmet_fresh_loaf": unmet_fresh_loaf,
            "sales_discount_loaf": sales_discount_loaf,
            "waste_rate": (self.cum_waste_cost / max(1.0, self.cum_profit + self.cum_waste_cost)),
            "stockout_rate": (self.total_unmet_units / max(1.0, self.total_demand_units))
        })

        return obs, reward, terminated, truncated, info

    def render(self):
        curr_row = self.df_ext.iloc[self.current_date_idx]
        print(f"[{curr_row['date'].strftime('%Y-%m-%d')}] Step: {self.current_step}/{self.episode_length} | Trust: {self.customer_trust} | LeftoverLoaf: {self.leftover_loaf} | CumProfit: {int(self.cum_profit):,}원")
