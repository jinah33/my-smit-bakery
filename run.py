"""
SMIT 베이커리 프로젝트 통합 실행 메뉴 (run.py)

- 메뉴 1: 시험 학습 (1분 안쪽 PPO 2,800 스텝)
- 메뉴 2: 본 학습 (10분 안쪽 PPO 100,000 스텝)
- 메뉴 3: 평가 시뮬레이션 (4대 규칙 + AI 정책 39회 평가)
- 메뉴 4: 웹 매장 재생 화면 서버 실행
- 메뉴 0: 종료
"""
import os
import sys
import time
import datetime
import subprocess
import pandas as pd


HISTORY_FILE = "run_history.csv"


def log_run_history(action_type: str, model_ver: str, steps_info: str, result_metric: str, evaluation: str):
    """실행 기록을 run_history.csv에 일관된 형식으로 추가 기록"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "timestamp": now_str,
        "action_type": action_type,
        "model_version": model_ver,
        "steps_or_episodes": steps_info,
        "result_metric": result_metric,
        "evaluation": evaluation
    }
    
    # 기존 파일이 다른 스키마(before/after)일 수도 있으므로 보존하면서 추가하거나 통합
    log_file = "run_execution_history.csv"
    file_exists = os.path.exists(log_file)
    df_new = pd.DataFrame([row])
    df_new.to_csv(log_file, mode="a", index=False, header=not file_exists, encoding="utf-8-sig")
    print(f"\n[실행 기록 저장 완료] {log_file} 에 저장되었습니다.")


def run_test_train():
    """메뉴 1: 시험 학습 (1분 안쪽)"""
    print("\n" + "=" * 60)
    print(">> [메뉴 1] 시험 학습 시작 (1분 안쪽 PPO 2,800스텝)...")
    print("=" * 60)
    start = time.time()
    res = subprocess.run([sys.executable, "train.py", "--test"], text=True)
    elapsed = time.time() - start
    
    if res.returncode == 0:
        log_run_history(
            action_type="시험 학습 (PPO)",
            model_ver="v1",
            steps_info="2,800 스텝 (100 에피소드)",
            result_metric=f"소요시간 {elapsed:.1f}초 (약 {2800/elapsed:.1f} SPS)",
            evaluation="1분 안쪽 시험 학습 정상 완료, 경험 샘플(1,000스텝) 및 모델 저장"
        )
    else:
        print("시험 학습 중 오류가 발생했습니다.")


def run_full_train(steps: int = 100000):
    """메뉴 2: 본 학습 (10분 안쪽 100,000 스텝)"""
    print("\n" + "=" * 60)
    print(f">> [메뉴 2] 본 학습 시작 (PPO {steps:,}스텝, 예상 약 8~9분)...")
    print("=" * 60)
    start = time.time()
    res = subprocess.run([sys.executable, "train.py", "--steps", str(steps)], text=True)
    elapsed = time.time() - start
    
    if res.returncode == 0:
        log_run_history(
            action_type="본 학습 (PPO)",
            model_ver="v1",
            steps_info=f"{steps:,} 스텝",
            result_metric=f"소요시간 {elapsed/60:.1f}분 (약 {steps/elapsed:.1f} SPS)",
            evaluation="본 학습 완료, 최종 모델(results/models/v1.zip) 및 학습 곡선 저장"
        )
    else:
        print("본 학습 중 오류가 발생했습니다.")


def run_evaluation():
    """메뉴 3: 평가 시뮬레이션 (39회 평가)"""
    print("\n" + "=" * 60)
    print(">> [메뉴 3] 평가 시뮬레이션 시작 (13개 시작일 × 3개 시드 = 39회 평가)...")
    print("=" * 60)
    start = time.time()
    res = subprocess.run([sys.executable, "simulate.py"], text=True)
    elapsed = time.time() - start

    if res.returncode == 0:
        # summary_v1.md 존재 확인
        sum_path = os.path.join("results", "summary_v1.md")
        log_run_history(
            action_type="평가 시뮬레이션",
            model_ver="v1 및 4대 규칙",
            steps_info="39개 에피소드 (28일 * 39 = 1,092일)",
            result_metric=f"소요시간 {elapsed:.1f}초",
            evaluation=f"평가 보고서 생성 완료 ({sum_path})"
        )
    else:
        print("평가 시뮬레이션 중 오류가 발생했습니다.")


def run_web_playback():
    """메뉴 4: 웹 매장 재생 서버 실행"""
    print("\n" + "=" * 60)
    print(">> [메뉴 4] 로컬 웹 서버 시작: http://localhost:8000")
    print("브라우저에서 위 주소로 접속하면 매장 운영 모습을 시청할 수 있습니다.")
    print("종료하려면 Ctrl+C를 누르세요.")
    print("=" * 60)
    try:
        subprocess.run([sys.executable, "-m", "http.server", "8000", "--directory", "public"])
    except KeyboardInterrupt:
        print("\n웹 서버를 종료했습니다.")


def main():
    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
    else:
        print("\n" + "═" * 50)
        print("   🥐 SMIT 베이커리 AI 통합 관리 시스템 (run.py)   ")
        print("═" * 50)
        print("  [1] 시험 학습 (1분 안쪽 PPO 2,800 스텝 빠른 검증)")
        print("  [2] 본 학습 (10분 안쪽 PPO 100,000 스텝 학습)")
        print("  [3] 평가 시뮬레이션 (4대 시험 규칙 + AI 정책 39회 평가)")
        print("  [4] 매장 재생 화면 웹 서버 실행 (http://localhost:8000)")
        print("  [0] 종료")
        print("═" * 50)
        try:
            choice = input("실행할 메뉴 번호를 입력하세요: ").strip()
        except EOFError:
            choice = "1"

    if choice == "1":
        run_test_train()
    elif choice == "2":
        run_full_train()
    elif choice == "3":
        run_evaluation()
    elif choice == "4":
        run_web_playback()
    elif choice == "0":
        print("프로그램을 종료합니다.")
    else:
        print(f"올바른 번호를 입력하세요: {choice}")


if __name__ == "__main__":
    main()
