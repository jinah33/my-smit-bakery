"""
1~20번 페르소나 고객 성향 수치 추정 및 data/customer_traits.csv 저장 스크립트
"""
import os
import pandas as pd

traits_data = [
    {
        "customer_id": 1,
        "uuid": "97bc5ac1083c4e569c60e6a5ab8424ee",
        "sandwich_daily_demand": 0.8,
        "snack_bread_daily_demand": 1.5,
        "loaf_daily_demand": 0.1,
        "snack_substitute_rate": 60,
        "discount_bread_pref": 20,
        "weekend_visit_weight": 0.8,
        "stockout_tolerance": 70,
        "confidence": "보통",
        "reasoning": "영업 관리 사무원으로 '주 5~6회 외식과 팀 회식'이 잦아 점심 샌드위치(0.8)와 간식빵(1.5) 수요 높음. 고소득 청년이자 부모 동거로 식빵(0.1) 및 할인 식빵(20%) 수요는 낮음."
    },
    {
        "customer_id": 2,
        "uuid": "bb9e5d23079d4fca812e11916e6b4dfc",
        "sandwich_daily_demand": 0.3,
        "snack_bread_daily_demand": 1.0,
        "loaf_daily_demand": 0.6,
        "snack_substitute_rate": 15,
        "discount_bread_pref": 5,
        "weekend_visit_weight": 1.5,
        "stockout_tolerance": 40,
        "confidence": "높음",
        "reasoning": "제품 디자이너로 '1mm 오차도 허용 않는 완벽주의'에 '신선함이 느껴지는 정갈한 상차림' 고집. 할인 빵 극도 기피(5%), 품절 시 높은 실망(40점). 자녀 있어 주말 가족 식빵·간식빵(1.5) 구매."
    },
    {
        "customer_id": 3,
        "uuid": "43deaabf404d4f26a5a7d9385f93ce34",
        "sandwich_daily_demand": 0.4,
        "snack_bread_daily_demand": 2.0,
        "loaf_daily_demand": 0.8,
        "snack_substitute_rate": 55,
        "discount_bread_pref": 65,
        "weekend_visit_weight": 1.8,
        "stockout_tolerance": 75,
        "confidence": "높음",
        "reasoning": "아파트 거주 '전업주부'로 가족 식사 및 자녀 간식용 식빵(0.8)·간식빵(2.0) 소비 큼. 조리용 실속 할인 식빵 선호(65%)하며 주말 가족 중심 방문(1.8)."
    },
    {
        "customer_id": 4,
        "uuid": "221e99e2310e4bde82af0725d7e474c4",
        "sandwich_daily_demand": 0.1,
        "snack_bread_daily_demand": 1.2,
        "loaf_daily_demand": 0.5,
        "snack_substitute_rate": 30,
        "discount_bread_pref": 50,
        "weekend_visit_weight": 1.4,
        "stockout_tolerance": 80,
        "confidence": "보통",
        "reasoning": "배관공으로 '퇴근길 단골 분식집 선호'하는 소박한 가장. 서구식 주식 빵(샌드위치 0.1)보다는 퇴근길 가족용 간식빵(1.2) 위주 소비, 단골 관계 중시(인내도 80점)."
    },
    {
        "customer_id": 5,
        "uuid": "d0753c0b64024b468f1c9f7153f86310",
        "sandwich_daily_demand": 0.6,
        "snack_bread_daily_demand": 0.8,
        "loaf_daily_demand": 0.1,
        "snack_substitute_rate": 40,
        "discount_bread_pref": 30,
        "weekend_visit_weight": 0.7,
        "stockout_tolerance": 60,
        "confidence": "보통",
        "reasoning": "지방행정 사무원 1인 가구로 '정갈한 식사' 선호. 출근 점심용 샌드위치(0.6) 중심 소비하며 대용량 식빵(0.1)은 기피, 꼼꼼하고 규칙적 성향(인내도 60점)."
    },
    {
        "customer_id": 6,
        "uuid": "03dcb1522c344438b6cf4762028002d7",
        "sandwich_daily_demand": 0.7,
        "snack_bread_daily_demand": 1.0,
        "loaf_daily_demand": 0.2,
        "snack_substitute_rate": 60,
        "discount_bread_pref": 45,
        "weekend_visit_weight": 1.2,
        "stockout_tolerance": 70,
        "confidence": "높음",
        "reasoning": "상품 기획자로 '새벽 수영과 서점 탐방' 즐기는 트렌디 1인 가구. 수영 후 샌드위치(0.7) 선호, 수제버거 등 양식 선호로 대체 구매 유연(60%)하며 주말 동네 활동(1.2)."
    },
    {
        "customer_id": 7,
        "uuid": "6b02719bab6645ba83f077320695cf7d",
        "sandwich_daily_demand": 0.5,
        "snack_bread_daily_demand": 2.5,
        "loaf_daily_demand": 0.9,
        "snack_substitute_rate": 45,
        "discount_bread_pref": 70,
        "weekend_visit_weight": 1.7,
        "stockout_tolerance": 65,
        "confidence": "높음",
        "reasoning": "마케팅 전문가이자 '배우자·자녀·아버지 동거' 3세대 대가족 워킹맘. 가족용 식빵(0.9)·간식빵(2.5) 대량 소비하며, 식구가 많아 조리용 할인 식빵 선호(70%) 높음."
    },
    {
        "customer_id": 8,
        "uuid": "99bcf9b3559d49f98c23dc3a10c8edc4",
        "sandwich_daily_demand": 0.6,
        "snack_bread_daily_demand": 1.5,
        "loaf_daily_demand": 0.6,
        "snack_substitute_rate": 70,
        "discount_bread_pref": 60,
        "weekend_visit_weight": 1.5,
        "stockout_tolerance": 75,
        "confidence": "보통",
        "reasoning": "산업 안전원으로 '점심에 햄버거·피자로 빠르게 한 끼 해결하는 실용적 식습관'. 간편식 샌드위치(0.6) 및 상황에 따른 높은 간식빵 대체율(70%)과 실속 할인 빵 선호(60%)."
    },
    {
        "customer_id": 9,
        "uuid": "42daf462572c47d0beebb350541320fa",
        "sandwich_daily_demand": 0.4,
        "snack_bread_daily_demand": 3.0,
        "loaf_daily_demand": 0.7,
        "snack_substitute_rate": 90,
        "discount_bread_pref": 10,
        "weekend_visit_weight": 2.0,
        "stockout_tolerance": 85,
        "confidence": "높음",
        "reasoning": "변리사로 '주말마다 갓 구운 소금빵과 치아바타 빵집 투어 즐김' 빵 매니아. 간식빵 다량 구매(3.0), 품절 시 대체 적극적(90%)이며 갓 구운 빵 고집으로 할인 선호 낮음(10%). 주말 집중(2.0)."
    },
    {
        "customer_id": 10,
        "uuid": "343ccf0c1bc645e085cb3700887d741a",
        "sandwich_daily_demand": 0.8,
        "snack_bread_daily_demand": 1.2,
        "loaf_daily_demand": 0.1,
        "snack_substitute_rate": 50,
        "discount_bread_pref": 35,
        "weekend_visit_weight": 0.5,
        "stockout_tolerance": 65,
        "confidence": "보통",
        "reasoning": "20대 후반 경리 사무원(부모 동거)으로 출근 점심용 샌드위치(0.8) 위주 소비. 주말에는 외부 모임 선호로 동네 빵집 방문 적음(0.5)."
    },
    {
        "customer_id": 11,
        "uuid": "63577b5e09f44349a10ac35d12a9a0d6",
        "sandwich_daily_demand": 0.2,
        "snack_bread_daily_demand": 1.8,
        "loaf_daily_demand": 0.8,
        "snack_substitute_rate": 20,
        "discount_bread_pref": 25,
        "weekend_visit_weight": 1.6,
        "stockout_tolerance": 55,
        "confidence": "높음",
        "reasoning": "보육교사로 '정성껏 차린 집밥 선호, 검증된 식당만 선택'. 자녀 간식용 빵(1.8)과 식빵(0.8) 중심이며, 신중하고 보수적 성향이라 대체율(20%) 낮고 신선 빵 선호(할인 25%)."
    },
    {
        "customer_id": 12,
        "uuid": "54f9ea81c43141dca25d8536972e9d12",
        "sandwich_daily_demand": 0.6,
        "snack_bread_daily_demand": 1.5,
        "loaf_daily_demand": 0.7,
        "snack_substitute_rate": 60,
        "discount_bread_pref": 50,
        "weekend_visit_weight": 1.4,
        "stockout_tolerance": 70,
        "confidence": "보통",
        "reasoning": "통계 사무원 워킹맘으로 직장 점심 샌드위치(0.6) 및 '주말 아이가 좋아하는 간식'용 식빵(0.7)·간식빵(1.5) 균형 소비. 합리적 데이터 분석가로 평균적 성향."
    },
    {
        "customer_id": 13,
        "uuid": "b1b139dc3068496aa74b6cf236faac06",
        "sandwich_daily_demand": 0.3,
        "snack_bread_daily_demand": 2.5,
        "loaf_daily_demand": 0.8,
        "snack_substitute_rate": 40,
        "discount_bread_pref": 15,
        "weekend_visit_weight": 1.8,
        "stockout_tolerance": 75,
        "confidence": "높음",
        "reasoning": "네트워크 엔지니어로 '천연발효종 빵집에서 갓 구운 치아바타 사 들고 귀가해 가족과 나눔' 중시. 갓 구운 신선 빵 애호가(할인 선호 15%), 가족용 식빵(0.8)·간식빵(2.5) 다량 구매."
    },
    {
        "customer_id": 14,
        "uuid": "994f33680a584f4f83ba3cff0fc070f6",
        "sandwich_daily_demand": 0.7,
        "snack_bread_daily_demand": 0.5,
        "loaf_daily_demand": 0.1,
        "snack_substitute_rate": 30,
        "discount_bread_pref": 30,
        "weekend_visit_weight": 0.4,
        "stockout_tolerance": 50,
        "confidence": "보통",
        "reasoning": "금융 사무원으로 '당뇨·비만 고민으로 채소/간편식 압박' 느낌. 점심 샌드위치(0.7) 외에 간식빵·식빵은 절제(0.1), 주말 낚시 외출로 매장 방문 적음(0.4)."
    },
    {
        "customer_id": 15,
        "uuid": "f23e4bd8e8f94572aa806fd915d77c97",
        "sandwich_daily_demand": 0.5,
        "snack_bread_daily_demand": 3.5,
        "loaf_daily_demand": 0.8,
        "snack_substitute_rate": 85,
        "discount_bread_pref": 10,
        "weekend_visit_weight": 1.9,
        "stockout_tolerance": 85,
        "confidence": "높음",
        "reasoning": "내과 전문의이자 워킹맘으로 '작은 빵집에서 갓 구워 나온 소금빵 집는 순간에 가장 큰 행복 느낌'. 간식빵 최다 소비(3.5), 갓 구운 새 빵 선호(할인 10%), 빵집 애착 큼(85점)."
    },
    {
        "customer_id": 16,
        "uuid": "329d17f4878e4447b2de3178fc750a55",
        "sandwich_daily_demand": 0.7,
        "snack_bread_daily_demand": 1.0,
        "loaf_daily_demand": 0.4,
        "snack_substitute_rate": 60,
        "discount_bread_pref": 50,
        "weekend_visit_weight": 0.9,
        "stockout_tolerance": 70,
        "confidence": "보통",
        "reasoning": "네트워크 시스템 개발자로 '아내를 위해 직접 요리 대접'하는 2인 가구. 평일 점심 샌드위치(0.7) 및 주말 브런치 조리용 식빵(0.4) 실속 구매."
    },
    {
        "customer_id": 17,
        "uuid": "633c48e05f6d45619a26a1ef5d1811b5",
        "sandwich_daily_demand": 0.6,
        "snack_bread_daily_demand": 0.7,
        "loaf_daily_demand": 0.1,
        "snack_substitute_rate": 20,
        "discount_bread_pref": 15,
        "weekend_visit_weight": 0.5,
        "stockout_tolerance": 45,
        "confidence": "높음",
        "reasoning": "회계 사무원으로 '정교한 숫자와 정적인 일상, 재료 품질 확실한 곳 신중히 선택'하는 1인 가구. 까다로운 미식 기준(할인 15%, 대체율 20%), 품절 시 높은 실망(45점)."
    },
    {
        "customer_id": 18,
        "uuid": "7fe908311f11412a8ed1e08be6fd9d0f",
        "sandwich_daily_demand": 0.6,
        "snack_bread_daily_demand": 1.5,
        "loaf_daily_demand": 0.3,
        "snack_substitute_rate": 70,
        "discount_bread_pref": 40,
        "weekend_visit_weight": 0.8,
        "stockout_tolerance": 75,
        "confidence": "보통",
        "reasoning": "ICT 기획 관리자로 '위생 상태와 서빙 속도 살피는 효율 중시형 직장인'. 빠른 점심 샌드위치(0.6) 및 간식빵 대체율(70%) 유연함."
    },
    {
        "customer_id": 19,
        "uuid": "d133d55773954549ba320f3209d88039",
        "sandwich_daily_demand": 0.3,
        "snack_bread_daily_demand": 1.5,
        "loaf_daily_demand": 0.7,
        "snack_substitute_rate": 35,
        "discount_bread_pref": 20,
        "weekend_visit_weight": 1.7,
        "stockout_tolerance": 60,
        "confidence": "보통",
        "reasoning": "마케팅 관리자로 '이탈리아 코스 천천히 음미'하는 미식 성향 아파트 거주 가구. 주말 가족용 식빵(0.7)·간식빵(1.5) 위주 소비하며 새 빵 선호(할인 20%)."
    },
    {
        "customer_id": 20,
        "uuid": "10ebd25c834a442dbea4b9e6c16ee103",
        "sandwich_daily_demand": 0.7,
        "snack_bread_daily_demand": 2.8,
        "loaf_daily_demand": 0.2,
        "snack_substitute_rate": 80,
        "discount_bread_pref": 20,
        "weekend_visit_weight": 1.3,
        "stockout_tolerance": 80,
        "confidence": "높음",
        "reasoning": "기획·마케팅 사무원으로 '불안을 소금빵과 산책으로 달래며 주말 유명 베이커리 찾아 갓 구운 소금빵 구매'. 소금빵 매니아(간식빵 2.8, 대체 80%), 갓 구운 빵 선호(할인 20%)."
    }
]

df = pd.DataFrame(traits_data)
os.makedirs("data", exist_ok=True)
csv_path = os.path.join("data", "customer_traits.csv")
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"성공적으로 {len(df)}명의 성향 데이터를 {csv_path}에 저장했습니다.")
