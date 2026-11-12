# 🥐 SMIT 베이커리 (SMIT Bakery & Café) - 가상 매장 강화학습 프로젝트

서울 마포구 상암동 디지털미디어시티(DMC) 오피스·주거 복합 상권에 위치한 동네 빵집 **SMIT 베이커리**의 가상 운영 환경 및 AI 매장 매니저 의사결정 시뮬레이션 프로젝트입니다.

---

## 📌 1. 프로젝트 소개

- **의사결정 문제**: 매일 아침 영업 시작 전(08:00) 빵 3종의 당일 생산량(굽는 양) 결정
  - 🥪 **샌드위치**: 0 ~ 60개 (소비기한 당일 1일, 미판매분 전량 폐기)
  - 🥐 **간식빵(소금빵/크루아상/단팥빵)**: 0 ~ 200개 (소비기한 당일 1일, 미판매분 전량 폐기)
  - 🍞 **식빵**: 0 ~ 50개 (소비기한 2일, 당일 미판매분은 익일 '어제 식빵' 30% 할인 판매 후 폐기)
- **목표(성공 척도)**: 28일(4주) 누적 순이익 최대화 (폐기 손실 및 품절 기회비용 최소화, 고객 신뢰도 유지)
- **주요 특징**:
  - 가상 고객 100명의 페르소나 및 구매 성향 모델링 (선호 메뉴, 가격 민감도, 어제 식빵 허용도, 재방문 주기 등)
  - 마포구 10개년 기상 데이터(기온, 강수, 날씨) 및 공휴일 외부 요인 반영
  - 과잉 폐기(생산량의 25% 초과 폐기 시) 고객 신뢰도 하락 페널티 적용
  - 웹 브라우저(Canvas 2D) 기반의 아이소메트릭 실시간 매장 재생 화면 제공 (`public/index.html`)

---

## 📈 1-1. 초기 학습 v1 현황 (휴리스틱 기준선)

- **4대 휴리스틱 벤치마크 결과 (28일 누적)**:
  - 🥇 **내가 정한 규칙 (사장님 노하우)**: **+9,726,050원** (폐기율 0.0%, 품절률 27.6%, 신뢰도 95점 유지)
  - 🥈 **무작위 행동 (Random)**: **+2,548,930원** (폐기율 2.4%, 품절률 15.3%)
  - 🥉 **아무것도 안 함 (Do Nothing)**: **0원** (매출 0원, 폐기 0원, 신뢰도 0점 하락)
  - 🚨 **매일 최대로 행동 (Max Production)**: **-6,750,900원** (과잉 폐기율 47.9%로 인한 대규모 적자 및 신뢰도 0점 파산)
- **v1 매장 재생 화면 (`public/index.html`)**:
  - 360x220 넓은 매장, 정면 유리 출입문, WELCOME 매트 및 스트라이프 어닝
  - 3단 제빵 오븐, 트레이 랙, 식빵 벽면 매대, 중앙 바게트 매대, 냉장 샌드위치 쇼케이스, POS 카운터 완비
  - 고객 출입문 통과 및 반응 말풍선 실시간 시각화 지원

---

## 💻 2. 다른 PC에서 설치하는 방법

이 프로젝트는 초고속 파이썬 패키지 관리자 **[uv](https://github.com/astral-sh/uv)**를 사용합니다.

### 1) uv 설치 (미설치 시)
- **Windows (PowerShell)**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **macOS / Linux**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 2) 프로젝트 의존성 동기화
저장소를 클론한 후 프로젝트 루트 폴더에서 아래 명령어를 실행하면 가상환경(`.venv`)과 필수 패키지가 자동으로 설치됩니다.
```powershell
uv sync
```

> **참고**: PyTorch GPU(CUDA) 가속을 사용할 경우:
> ```powershell
> uv pip install torch --index-url https://download.pytorch.org/whl/cu124
> ```

---

## 🚀 3. 실행 방법

모든 스크립트는 가상환경 활성화 후 실행하거나 `uv run <스크립트>`로 바로 실행할 수 있습니다.

### 1) 시뮬레이션 및 규칙 검증 (simulate)
4가지 운영 규칙(아무것도 안 함, 매일 최대로 행동, 무작위 행동, 사장님 노하우)을 13개 에피소드(28일)에 걸쳐 평가하고 결과를 요약합니다.
```powershell
uv run python simulate.py
```
- 결과 로그: `results/logs/` (규칙별 CSV 로그)
- 검증 보고서: `results/sanity_check.md`
- 전후 비교 히스토리: `run_history.csv`

### 2) 매장 재생 화면 시청 (Web UI)
로컬 웹 서버를 실행하여 브라우저에서 매장 운영 모습을 시각적으로 재생합니다.
```powershell
# 로컬 웹 서버 실행 (public 디렉터리 기준)
uv run python -m http.server 8000 --directory public
```
- 브라우저 접속: `http://localhost:8000`
- 기능: 4가지 규칙별 매장 비교, 날짜 이동(1~28일 슬롯), 배속 조절(1x~60x), 고객 말풍선 및 반응 관찰

### 3) 재생 화면 스크린샷 캡처
헤드리스 브라우저로 재생 화면을 캡처하여 검증 이미지를 저장합니다.
```powershell
uv run python scripts/capture_screenshot.py
```
- 캡처 이미지: `results/screenshots/playback_screen.png`

---

## 📂 4. 폴더 구성

```text
my-store/
├── data/                             # 시뮬레이션 기초 데이터
│   ├── personas.csv                  # 마포구 100명 고객 페르소나 원본
│   ├── customer_traits.csv           # 추정된 고객 100명 행동 성향 파라미터
│   └── external_factors.csv          # 10개년(2016~2025) 일별 기상 및 공휴일 데이터
├── public/                           # 매장 재생 화면 (Web UI)
│   ├── index.html                    # 순수 HTML + Canvas 2D 아이소메트릭 매장 화면
│   └── data/
│       ├── personas.json             # 시각화용 고객 외형 요약 데이터
│       └── playback.json             # 28일간 일별 상세 재생 데이터 (시뮬레이션 산출물)
├── results/                          # 실험 결과물
│   ├── logs/                         # 4가지 정책별 39회 시뮬레이션 상세 CSV 로그
│   ├── screenshots/                  # 재생 화면 캡처 이미지
│   └── sanity_check.md               # 4개 규칙 성능 및 상식 점검 보고서
├── scripts/                          # 유틸리티 및 보조 스크립트
│   └── capture_screenshot.py         # 브라우저 화면 자동 캡처 스크립트
├── .gitignore                        # Git 추적 제외 설정
├── AGENTS.md                         # 프로젝트 행동 규칙 및 원칙
├── CLAUDE.md                         # LLM 지침 연동
├── config.py                         # 매장 가격, 비용, 운영 시간 등 단일 기준 설정
├── env.py                            # Gymnasium 표준 강화학습 가상 매장 환경
├── project_spec.md                   # 프로젝트 전체 설계 명세서 (Single Source of Truth)
├── run_history.csv                   # 하이퍼파라미터 및 반응 규칙 변경 이력
├── simulate.py                       # 4대 휴리스틱 규칙 벤치마크 및 JSON 생성기
└── pyproject.toml                    # 프로젝트 의존성 명세 (uv)
```

---

## 📊 5. 데이터 출처

1. **고객 페르소나 데이터**:
   - 데이터셋: `nvidia/Nemotron-Personas-Korea` (Hugging Face)
   - 추출 기준: 서울시 마포구 상암 DMC 인근 20~40대 직장인 및 거주민 100명 샘플링
2. **과거 기상 데이터 (2016 ~ 2025)**:
   - 출처: Open-Meteo Historical Weather API (`openmeteo-requests`)
   - 위치: 서울시 마포구 상암동 좌표 (위도 37.5796, 경도 126.8898)
   - 항목: 일 최고/최저 기온, 강수량, 강우량, 강설량
3. **대한민국 법정 공휴일**:
   - 패키지: `holidays` (대한민국 대체공휴일 및 선거일 포함)
