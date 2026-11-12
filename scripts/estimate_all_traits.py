"""
data/personas.csv의 100명 전체에 대해 고객 성향(customer_traits.csv)을 완성하는 스크립트
1~20번은 기존 수치를 유지하고, 21~100번은 소개글, 식생활, 직업, 가족/주거 형태를 반영하여 추정
"""
import os
import re
import pandas as pd

def generate_traits_for_row(idx, row):
    # 인덱스는 0부터 시작하므로 고객 번호는 idx + 1
    cust_id = idx + 1
    uuid = row['uuid']
    occ = str(row['occupation'])
    housing = str(row['housing_type'])
    family = str(row['family_type'])
    persona = str(row['persona'])
    culinary = str(row['culinary_persona'])
    
    # 텍스트 단서 분석
    has_child = any(k in family for k in ['자녀', '자식', '아이', '가족'])
    is_single = any(k in family for k in ['혼자', '1인', '독거']) or '혼자' in persona
    is_apartment = '아파트' in housing
    
    # 빵 및 식생활 단서
    likes_bread = any(k in culinary for k in ['빵', '베이커리', '소금빵', '크루아상', '치아바타', '바게트', '토스트', '디저트'])
    fast_lunch = any(k in culinary for k in ['간편', '배달', '외식', '햄버거', '샌드위치', '분식', '바쁜', '빠르게'])
    strict_health = any(k in culinary for k in ['정갈', '신선', '나물', '한식', '유기농', '완벽', '철저', '집밥'])
    likes_meat_social = any(k in culinary for k in ['삼겹살', '고기', '회식', '술', '소주', '동료', '모임'])
    
    # 1. 샌드위치 수요 (직장인 점심형, 간편식 선호형)
    if is_single or ('사무' in occ or '개발' in occ or '기획' in occ or '연구' in occ or '디자이너' in occ):
        if fast_lunch:
            sw_demand = 0.8
        else:
            sw_demand = 0.6
    else:
        if has_child:
            sw_demand = 0.3
        else:
            sw_demand = 0.4
            
    # 2. 간식빵 수요 (가족형, 빵 애호형)
    if likes_bread:
        snack_demand = 2.8 if has_child else 2.0
    elif has_child:
        snack_demand = 1.8 if is_apartment else 1.5
    elif is_single:
        snack_demand = 0.7
    else:
        snack_demand = 1.0
        
    # 3. 식빵 수요 (가정용 식빵: 가족 및 아파트 거주민 중심)
    if has_child and is_apartment:
        loaf_demand = 0.7
    elif has_child:
        loaf_demand = 0.5
    elif is_single:
        loaf_demand = 0.1
    else:
        loaf_demand = 0.2
        
    # 4. 간식빵 대체율 (%)
    if likes_bread or fast_lunch:
        sub_rate = 65
    elif strict_health:
        sub_rate = 25
    else:
        sub_rate = 45
        
    # 5. 할인 식빵 선호도 (%)
    if strict_health or likes_bread:
        disc_pref = 15  # 갓 구운 새 빵 선호
    elif has_child:
        disc_pref = 60  # 가족 조리용 실속 할인 선호
    elif is_single:
        disc_pref = 35
    else:
        disc_pref = 40
        
    # 6. 주말 방문 가중치 (배수)
    if is_apartment and has_child:
        wknd_weight = 1.8
    elif has_child:
        wknd_weight = 1.5
    elif is_single and ('사무' in occ or '개발' in occ):
        wknd_weight = 0.4
    else:
        wknd_weight = 0.8
        
    # 7. 품절 인내도 (점수)
    if strict_health:
        tolerance = 50  # 까다로움
    elif likes_bread:
        tolerance = 85  # 빵집 애착
    elif likes_meat_social:
        tolerance = 75  # 원만함
    else:
        tolerance = 65  # 보통 단골
        
    # 확신도 및 근거 문장 생성 (직업, 주거, 식생활 인용)
    reasons = []
    reasons.append(f"직업 '{occ}' 및 {housing}({family}) 형태")
    if likes_bread:
        reasons.append("식생활에서 빵·베이커리 선호가 나타남")
    elif strict_health:
        reasons.append("식생활에서 정갈한 한식·신선한 식재료 선호")
    elif fast_lunch:
        reasons.append("식생활에서 간편하고 빠른 식사 습관 반영")
    else:
        reasons.append("식생활에서 소박한 일상 외식 성향 반영")
        
    conf = "높음" if likes_bread or strict_health else "보통"
    reasoning_text = f"{reasons[0]} 반영, {reasons[1]}하여 수치 도출."
    
    return {
        "customer_id": cust_id,
        "uuid": uuid,
        "sandwich_daily_demand": round(sw_demand, 2),
        "snack_bread_daily_demand": round(snack_demand, 2),
        "loaf_daily_demand": round(loaf_demand, 2),
        "snack_substitute_rate": int(sub_rate),
        "discount_bread_pref": int(disc_pref),
        "weekend_visit_weight": round(wknd_weight, 2),
        "stockout_tolerance": int(tolerance),
        "confidence": conf,
        "reasoning": reasoning_text
    }

def main():
    personas_path = os.path.join("data", "personas.csv")
    traits_path = os.path.join("data", "customer_traits.csv")
    
    df_personas = pd.read_csv(personas_path)
    print(f"페르소나 총 {len(df_personas)}명 로드 완료.")
    
    # 기존 1~20번 읽기
    existing_traits = []
    if os.path.exists(traits_path):
        df_old = pd.read_csv(traits_path)
        existing_traits = df_old[df_old['customer_id'] <= 20].to_dict('records')
        print(f"기존 1~20번 고객 데이터 {len(existing_traits)}건 보존.")
        
    all_traits = list(existing_traits)
    
    # 21~100번 추가
    for i in range(len(existing_traits), len(df_personas)):
        row = df_personas.iloc[i]
        trait = generate_traits_for_row(i, row)
        all_traits.append(trait)
        
    df_final = pd.DataFrame(all_traits)
    df_final.to_csv(traits_path, index=False, encoding="utf-8-sig")
    print(f"전체 {len(df_final)}명 성향 데이터를 {traits_path}에 저장 완료.")

if __name__ == '__main__':
    main()
