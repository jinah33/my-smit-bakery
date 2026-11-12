"""
Hugging Face nvidia/Nemotron-Personas-Korea 데이터셋에서
마포구 20~40대 방송·미디어·IT 직장인 및 아파트 주민 100명을 추출하는 스크립트
"""
import os
import random
import pandas as pd
from datasets import load_dataset

RANDOM_SEED = 42
TARGET_COUNT = 100

def extract():
    random.seed(RANDOM_SEED)
    print("원격 데이터셋 스트리밍 연결 중...")
    ds = load_dataset('nvidia/Nemotron-Personas-Korea', split='train', streaming=True)
    
    work_keywords = [
        '방송', '미디어', '기획', 'PD', '기자', '작가', '영화', '영상', '음반',
        '디자이너', '디자인', '광고', '홍보', 'IT', '개발', '소프트웨어', '정보통신',
        '사무원', '연구원', '엔지니어', '프로그래머', '마케팅'
    ]
    
    candidates_primary = []
    candidates_secondary = []
    
    # 필요한 최소 후보군(예: 300명)이 모이거나 충분히 탐색하면 중단
    print("조건에 맞는 페르소나 탐색 중...")
    checked = 0
    for item in ds:
        checked += 1
        district = item.get('district', '')
        if '마포' not in district:
            continue
            
        age = item.get('age', 0)
        # 성인 조건 (20~49세)
        if not (20 <= age <= 49):
            continue
            
        occupation = item.get('occupation', '')
        housing_type = item.get('housing_type', '')
        family_type = item.get('family_type', '')
        
        # 1. 평일 직장인 조건 (25~49세 방송/미디어/IT/사무)
        is_worker = (25 <= age <= 49) and any(kw in occupation for kw in work_keywords)
        # 2. 아파트 거주 가족 조건 (30~49세 아파트 주민)
        is_resident = (30 <= age <= 49) and ('아파트' in housing_type) and any(kw in family_type for kw in ['자녀', '배우자'])
        
        record = {
            'uuid': item.get('uuid'),
            'age': age,
            'sex': item.get('sex'),
            'occupation': occupation,
            'housing_type': housing_type,
            'family_type': family_type,
            'district': district,
            'province': item.get('province'),
            'persona': item.get('persona'),
            'culinary_persona': item.get('culinary_persona'),
            'professional_persona': item.get('professional_persona'),
            'category': '직장인' if is_worker else ('아파트주민' if is_resident else '일반성인')
        }
        
        if is_worker or is_resident:
            candidates_primary.append(record)
        else:
            if occupation != '무직':
                candidates_secondary.append(record)
                
        # 1순위 후보가 200명 이상 모이면 충분하므로 중단
        if len(candidates_primary) >= 200:
            break
            
        # 너무 오래 걸리지 않도록 5만 건 탐색 후 중단
        if checked >= 50000:
            break

    print(f"탐색 완료: 총 {checked}건 중 마포구 1순위 조건 {len(candidates_primary)}명, 2순위 조건 {len(candidates_secondary)}명 확보")
    
    if len(candidates_primary) >= TARGET_COUNT:
        selected = random.sample(candidates_primary, TARGET_COUNT)
    else:
        needed = TARGET_COUNT - len(candidates_primary)
        print(f"1순위 후보가 {len(candidates_primary)}명으로 {TARGET_COUNT}명에 부족하여 2순위 후보에서 {needed}명을 보충합니다.")
        fill = random.sample(candidates_secondary, min(needed, len(candidates_secondary)))
        selected = candidates_primary + fill
        
    os.makedirs('data', exist_ok=True)
    df = pd.DataFrame(selected)
    out_path = os.path.join('data', 'personas.csv')
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {out_path} (총 {len(df)}명)")
    
    # 요약 출력
    print("=== 선별된 100명 요약 ===")
    print(f"평균 나이: {df['age'].mean():.1f}세 (범위 {df['age'].min()}~{df['age'].max()}세)")
    print(f"성별: {dict(df['sex'].value_counts())}")
    print(f"주거 형태: {dict(df['housing_type'].value_counts())}")
    print(f"주요 직업군 상위 5개:\n{df['occupation'].value_counts().head(5)}")

if __name__ == '__main__':
    extract()
