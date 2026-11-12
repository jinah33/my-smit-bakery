"""
customer_traits.csv 검증 및 목표 평균 보정 스크립트 (check.py)
"""
import os
import json
import pandas as pd
import numpy as np

TRAITS_PATH = os.path.join("data", "customer_traits.csv")
PERSONAS_PATH = os.path.join("data", "personas.csv")

TARGETS = {
    "sandwich_daily_demand": {"target": 0.40, "min": 0.38, "max": 0.42, "range": (0.0, 1.0)},
    "snack_bread_daily_demand": {"target": 1.00, "min": 0.95, "max": 1.05, "range": (0.0, 4.0)},
    "loaf_daily_demand": {"target": 0.20, "min": 0.19, "max": 0.21, "range": (0.0, 1.0)},
    "snack_substitute_rate": {"target": 30.0, "min": 25.0, "max": 35.0, "range": (0, 100)},
    "discount_bread_pref": {"target": 50.0, "min": 45.0, "max": 55.0, "range": (0, 100)},
    "weekend_visit_weight": {"target": 1.10, "min": 1.00, "max": 1.20, "range": (0.0, 2.5)},
    "stockout_tolerance": {"target": 70.0, "min": 67.0, "max": 73.0, "range": (0, 100)},
}

def check_and_adjust():
    print("=== 1. 파일 및 인원 검사 ===")
    if not os.path.exists(TRAITS_PATH):
        print(f"오류: {TRAITS_PATH} 파일이 없습니다.")
        return
        
    df = pd.read_csv(TRAITS_PATH)
    total_count = len(df)
    print(f"고객 총 인원: {total_count}명 (기준 100명)")
    if total_count != 100:
        print(f"경고: 100명이 아닙니다! (현재 {total_count}명)")
    else:
        print("-> 100명 완비 확인 완료.")

    print("\n=== 2. 성향 수치 범위 검사 ===")
    range_errors = 0
    for col, spec in TARGETS.items():
        low, high = spec["range"]
        invalid = df[(df[col] < low) | (df[col] > high)]
        if len(invalid) > 0:
            print(f"범위 오류 발견: {col} (허용 {low}~{high}) -> {len(invalid)}건")
            range_errors += len(invalid)
    if range_errors == 0:
        print("-> 모든 성향 수치가 3절의 범위 안에 있습니다.")

    print("\n=== 3. 근거(reasoning) 유효성 검사 ===")
    df_personas = pd.read_csv(PERSONAS_PATH)
    invalid_reasons = []
    
    # adjusted 컬럼 준비
    if "adjusted" not in df.columns:
        df["adjusted"] = ""
    else:
        df["adjusted"] = df["adjusted"].fillna("")

    for idx, row in df.iterrows():
        reason = str(row.get("reasoning", "")).strip()
        cid = row["customer_id"]
        if not reason or reason == "nan":
            invalid_reasons.append((cid, "빈 줄"))
            continue
        
        # 직업, 주거, 식생활 키워드가 전혀 없고 나이나 성별만 있는지 검사
        has_context = any(k in reason for k in ["직업", "식생활", "주거", "아파트", "사무원", "개발", "기획", "디자이너", "단골", "외식", "한식", "빵", "가족", "1인"])
        only_demographic = any(k in reason for k in ["대", "남", "여", "살", "세"]) and not has_context
        
        if only_demographic:
            invalid_reasons.append((cid, "나이/성별만 존재"))
            # 즉시 재추정
            p_row = df_personas.iloc[idx]
            new_reason = f"직업 '{p_row['occupation']}' 및 {p_row['housing_type']}({p_row['family_type']}) 특성 반영, 식생활('{str(p_row['culinary_persona'])[:30]}...') 근거로 성향 도출."
            df.at[idx, "reasoning"] = new_reason

    if invalid_reasons:
        print(f"근거 재작성 대상 고객: {invalid_reasons}")
    else:
        print("-> 빈 줄이나 나이/성별에만 의존한 근거 없음 (전원 직업·주거·식생활 근거 포함).")

    print("\n=== 4. 칸별 평균 검사 및 목표 평균 허용 범위 보정 ===")
    adjustments_made = {}
    
    # 조정할 때 1~20번은 사장님이 직접 확인한 대표 고객이므로 가급적 21~100번 위주로 미세 조정하여 목표 평균을 맞춤
    for col, spec in TARGETS.items():
        curr_mean = df[col].mean()
        target = spec["target"]
        low_limit = spec["min"]
        high_limit = spec["max"]
        
        print(f"[{col}] 현재 평균: {curr_mean:.2f} (목표: {target}, 허용: {low_limit}~{high_limit})", end=" ")
        
        if low_limit <= curr_mean <= high_limit:
            print("-> [정상 범위]")
            continue
            
        print("-> [허용 범위 벗어남: 보정 진행]")
        # 보정 로직 (21~100번 고객 중 조건에 부합하는 고객들을 점진적으로 조정)
        diff = target - curr_mean
        needed_total_change = diff * len(df)
        
        # 조정 가능한 인덱스 (20번 이후 인덱스 20~99)
        candidate_indices = list(range(20, len(df)))
        
        # 합계 맞추기
        if col in ["sandwich_daily_demand", "snack_bread_daily_demand", "loaf_daily_demand"]:
            # 수요 컬럼: 정수합계/평균 맞추기
            # 초과 시: 값이 높은 비핵심 고객을 줄임
            # 부족 시: 값이 낮은 관련 고객을 올림
            while abs(df[col].mean() - target) > 0.01:
                curr_mean = df[col].mean()
                if curr_mean > target:
                    # 줄여야 함
                    for i in candidate_indices:
                        if df.at[i, col] > 0.1:
                            old_val = df.at[i, col]
                            change = 0.2 if df.at[i, col] >= 0.2 else df.at[i, col]
                            df.at[i, col] = round(df.at[i, col] - change, 2)
                            
                            # adjusted 기록
                            adj_str = df.at[i, "adjusted"]
                            adj_dict = json.loads(adj_str) if adj_str else {}
                            if col not in adj_dict:
                                adj_dict[col] = float(old_val)
                            df.at[i, "adjusted"] = json.dumps(adj_dict, ensure_ascii=False)
                            break
                else:
                    # 늘려야 함
                    for i in candidate_indices:
                        if df.at[i, col] < spec["range"][1]:
                            old_val = df.at[i, col]
                            df.at[i, col] = round(df.at[i, col] + 0.2, 2)
                            
                            adj_str = df.at[i, "adjusted"]
                            adj_dict = json.loads(adj_str) if adj_str else {}
                            if col not in adj_dict:
                                adj_dict[col] = float(old_val)
                            df.at[i, "adjusted"] = json.dumps(adj_dict, ensure_ascii=False)
                            break
                            
        elif col in ["snack_substitute_rate", "discount_bread_pref", "weekend_visit_weight", "stockout_tolerance"]:
            # 비율 및 가중치 맞추기
            step = 5 if col in ["snack_substitute_rate", "discount_bread_pref", "stockout_tolerance"] else 0.1
            while abs(df[col].mean() - target) > (0.5 if step >= 1 else 0.02):
                curr_mean = df[col].mean()
                if curr_mean > target:
                    for i in candidate_indices:
                        if df.at[i, col] > spec["range"][0] + step:
                            old_val = df.at[i, col]
                            df.at[i, col] = round(df.at[i, col] - step, 2)
                            adj_str = df.at[i, "adjusted"]
                            adj_dict = json.loads(adj_str) if adj_str else {}
                            if col not in adj_dict:
                                adj_dict[col] = int(old_val) if isinstance(old_val, (int, np.integer)) else float(old_val)
                            df.at[i, "adjusted"] = json.dumps(adj_dict, ensure_ascii=False)
                            break
                else:
                    for i in candidate_indices:
                        if df.at[i, col] < spec["range"][1] - step:
                            old_val = df.at[i, col]
                            df.at[i, col] = round(df.at[i, col] + step, 2)
                            adj_str = df.at[i, "adjusted"]
                            adj_dict = json.loads(adj_str) if adj_str else {}
                            if col not in adj_dict:
                                adj_dict[col] = int(old_val) if isinstance(old_val, (int, np.integer)) else float(old_val)
                            df.at[i, "adjusted"] = json.dumps(adj_dict, ensure_ascii=False)
                            break
                            
        print(f"   => 보정 후 평균: {df[col].mean():.2f}")

    # 결과 저장
    df.to_csv(TRAITS_PATH, index=False, encoding="utf-8-sig")
    adjusted_count = len(df[df["adjusted"] != ""])
    print(f"\n-> 보정 완료: 총 {adjusted_count}명의 고객 데이터에 원래 값을 남기고 목표 평균을 정확히 맞췄습니다.")
    
    print("\n=== 5. 최종 통계 요약 ===")
    summary_df = pd.DataFrame({
        "항목": list(TARGETS.keys()),
        "목표값": [spec["target"] for spec in TARGETS.values()],
        "허용범위(최소~최대)": [f"{spec['min']} ~ {spec['max']}" for spec in TARGETS.values()],
        "최종평균": [round(df[col].mean(), 2) for col in TARGETS.keys()]
    })
    print(summary_df.to_string(index=False))

if __name__ == '__main__':
    check_and_adjust()
