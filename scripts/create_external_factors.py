"""
2016-01-01 ~ 2025-12-31 외부 요인 데이터 생성 스크립트
위치: 서울시 마포구 상암동 DMC (위도 37.5796, 경도 126.8890)
수집 항목:
- date: 날짜 (YYYY-MM-DD)
- is_weekend: 주말 여부 (토/일 = 1, 평일 = 0)
- is_holiday: 공휴일 여부 (holidays.KR = 1, 평일 = 0)
- temp_max: 최고 기온 (℃)
- temp_min: 최저 기온 (℃)
- precipitation: 일 강수량 (mm)
- snowfall: 일 적설량 (cm)
- is_bad_weather: 궂은 날씨 여부 (강수 5mm 이상, 적설 1cm 이상, 최고 33℃ 이상 또는 최저 -10℃ 이하)
"""
import os
import openmeteo_requests
import requests_cache
import pandas as pd
import numpy as np
from retry_requests import retry
import holidays

def generate_external_factors():
    print("1. Open-Meteo 과거 기상 데이터 요청 중 (2016-01-01 ~ 2025-12-31)...")
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # 서울시 마포구 상암동 DMC 좌표
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 37.5796,
        "longitude": 126.8890,
        "start_date": "2016-01-01",
        "end_date": "2025-12-31",
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "snowfall_sum"
        ],
        "timezone": "Asia/Seoul"
    }
    
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    
    daily = response.Daily()
    temp_max = daily.Variables(0).ValuesAsNumpy()
    temp_min = daily.Variables(1).ValuesAsNumpy()
    precipitation = daily.Variables(2).ValuesAsNumpy()
    snowfall = daily.Variables(3).ValuesAsNumpy()
    
    # 날짜 범위 생성
    date_range = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True).tz_convert("Asia/Seoul"),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True).tz_convert("Asia/Seoul"),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )
    
    # 2. 데이터프레임 구성
    df = pd.DataFrame({
        "date": date_range.strftime("%Y-%m-%d"),
        "temp_max": np.round(temp_max, 1),
        "temp_min": np.round(temp_min, 1),
        "precipitation": np.round(precipitation, 1),
        "snowfall": np.round(snowfall, 1)
    })
    
    print("2. 주말, 공휴일 및 궂은 날씨 판정 진행 중...")
    # 한국 공휴일 (2016 ~ 2025)
    kr_holidays = holidays.KR(years=range(2016, 2026))
    
    # 요일 계산 (5: 토요일, 6: 일요일)
    dt_series = pd.to_datetime(df["date"])
    df["is_weekend"] = dt_series.dt.weekday.apply(lambda w: 1 if w >= 5 else 0)
    
    # 공휴일 계산
    df["is_holiday"] = df["date"].apply(lambda d: 1 if d in kr_holidays else 0)
    
    # 궂은 날씨 판정 기준:
    # 1. 일 강수량 5.0mm 이상
    # 2. 일 적설량 1.0cm 이상
    # 3. 폭염(최고 33℃ 이상) 또는 한파(최저 -10℃ 이하)
    is_bad = (
        (df["precipitation"] >= 5.0) |
        (df["snowfall"] >= 1.0) |
        (df["temp_max"] >= 33.0) |
        (df["temp_min"] <= -10.0)
    )
    df["is_bad_weather"] = is_bad.astype(int)
    
    # 컬럼 순서 정돈
    ordered_cols = [
        "date", "is_weekend", "is_holiday",
        "temp_max", "temp_min", "precipitation", "snowfall",
        "is_bad_weather"
    ]
    df = df[ordered_cols]
    
    # 3. CSV 저장
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "external_factors.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    
    print(f"저장 완료: {out_path} (총 {len(df)}일)")
    print("\n=== 외부 요인 10년(2016~2025) 데이터 통계 ===")
    print(f"총 일수: {len(df)}일")
    print(f"주말 일수: {df['is_weekend'].sum()}일 ({df['is_weekend'].mean()*100:.1f}%)")
    print(f"공휴일 일수(주말 포함/대체공휴일 포함): {df['is_holiday'].sum()}일 ({df['is_holiday'].mean()*100:.1f}%)")
    print(f"궂은 날씨 일수: {df['is_bad_weather'].sum()}일 ({df['is_bad_weather'].mean()*100:.1f}%)")
    print(f"평균 최고/최저 기온: {df['temp_max'].mean():.1f}℃ / {df['temp_min'].mean():.1f}℃")
    print(f"연평균 강수일(5mm 이상): {(df['precipitation'] >= 5.0).sum() / 10:.1f}일")

if __name__ == '__main__':
    generate_external_factors()
