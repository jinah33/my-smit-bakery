"""
SMIT 베이커리 강화학습 학습 스크립트 (train.py)

- 알고리즘: PPO (Proximal Policy Optimization)
- 장치: GPU (CUDA - NVIDIA GeForce RTX 3090 Ti)
- 보상: reward.py (v1: 당일 순이익 / 100,000)
- 학습 기간: 2016-01-01 ~ 2024-12-31 (무작위 에피소드 시작일)
"""
import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 윈도우 한글 폰트 설정 (그래프 한글 깨짐 방지)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

import config
from env import BakeryEnv


# ==============================================================================
# 1. 처음 1,000스텝 경험(Transition) 저장 콜백
# ==============================================================================
class ExperienceRecorderCallback(BaseCallback):
    """학습 중 처음 max_steps (기본 1,000) 스텝 동안의 경험 데이터를 수집하여 CSV로 저장"""
    def __init__(self, save_path: str, max_steps: int = 1000, verbose: int = 0):
        super().__init__(verbose)
        self.save_path = save_path
        self.max_steps = max_steps
        self.records = []
        self.is_saved = False

    def _on_step(self) -> bool:
        if len(self.records) < self.max_steps:
            # locals에서 직전 step의 transition 데이터 추출
            obs = self.locals.get("obs_tensor")
            if obs is not None:
                obs_np = obs.cpu().numpy()[0]
            else:
                obs_np = self.locals.get("new_obs")[0]

            action = self.locals.get("actions")[0]
            reward = float(self.locals.get("rewards")[0])
            done = bool(self.locals.get("dones")[0])
            info = self.locals.get("infos")[0]

            self.records.append({
                "step": self.num_timesteps,
                "date": info.get("date", ""),
                "s_day": round(float(obs_np[0]), 4),
                "s_trust": round(float(obs_np[1]), 4),
                "s_loaf": round(float(obs_np[2]), 4),
                "s_weekend": int(obs_np[3]),
                "s_holiday": int(obs_np[4]),
                "s_weather": int(obs_np[5]),
                "s_event": int(obs_np[6]),
                "a_sandwich": round(float(action[0]), 2),
                "a_snack": round(float(action[1]), 2),
                "a_loaf": round(float(action[2]), 2),
                "reward": round(reward, 4),
                "daily_profit": int(info.get("daily_profit", 0)),
                "customer_trust": int(info.get("customer_trust", 100)),
                "done": done
            })

            if len(self.records) >= self.max_steps and not self.is_saved:
                self._save()
        return True

    def _save(self):
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        df = pd.DataFrame(self.records)
        df.to_csv(self.save_path, index=False, encoding="utf-8-sig")
        print(f"\n[경험 수집 완료] 처음 {len(df)}스텝의 경험이 저장되었습니다: {self.save_path}")
        self.is_saved = True

    def _on_training_end(self) -> None:
        if not self.is_saved and len(self.records) > 0:
            self._save()


# ==============================================================================
# 2. 학습 곡선 로깅 및 시각화 콜백
# ==============================================================================
class LearningCurveCallback(BaseCallback):
    """에피소드 단위 보상 및 순이익을 추적하여 CSV 및 그래프(PNG)로 저장"""
    def __init__(self, csv_path: str, img_path: str, verbose: int = 0):
        super().__init__(verbose)
        self.csv_path = csv_path
        self.img_path = img_path
        self.episode_count = 0
        self.current_ep_reward = 0.0
        self.current_ep_profit = 0.0
        self.history = []

    def _on_step(self) -> bool:
        reward = float(self.locals.get("rewards")[0])
        done = bool(self.locals.get("dones")[0])
        info = self.locals.get("infos")[0]

        self.current_ep_reward += reward
        self.current_ep_profit += info.get("daily_profit", 0.0)

        if done:
            self.episode_count += 1
            self.history.append({
                "episode": self.episode_count,
                "timesteps": self.num_timesteps,
                "ep_reward": round(self.current_ep_reward, 4),
                "ep_profit": int(self.current_ep_profit),
                "final_trust": int(info.get("customer_trust", 0))
            })
            self.current_ep_reward = 0.0
            self.current_ep_profit = 0.0
        return True

    def _on_training_end(self) -> None:
        if not self.history:
            return
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        df = pd.DataFrame(self.history)
        df.to_csv(self.csv_path, index=False, encoding="utf-8-sig")
        print(f"[학습 기록 저장] 에피소드 이력({len(df)}개) 저장 완료: {self.csv_path}")

        # 이동 평균(10 에피소드) 계산
        df["ma_profit"] = df["ep_profit"].rolling(window=min(10, len(df)), min_periods=1).mean()

        # 학습 곡선 시각화
        plt.figure(figsize=(10, 5), dpi=150)
        plt.plot(df["episode"], df["ep_profit"] / 10000, label="에피소드 순이익 (만원)", color="#93c5fd", alpha=0.5)
        plt.plot(df["episode"], df["ma_profit"] / 10000, label="10-에피소드 이동평균", color="#2563eb", linewidth=2)
        plt.axhline(y=972.6, color="#059669", linestyle="--", label="사장님 노하우 기준 (972.6만원)")
        plt.title("SMIT 베이커리 PPO 학습 곡선 (v1: 순이익 직결형)", fontsize=13, fontweight="bold")
        plt.xlabel("에피소드 (한 판 = 28일)", fontsize=11)
        plt.ylabel("28일 누적 순이익 (만원)", fontsize=11)
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend(loc="lower right")
        plt.tight_layout()
        os.makedirs(os.path.dirname(self.img_path), exist_ok=True)
        plt.savefig(self.img_path)
        plt.close()
        print(f"[학습 곡선 저장] 그래프 저장 완료: {self.img_path}")


# ==============================================================================
# 3. 메인 학습 실행 함수
# ==============================================================================
def run_train(total_timesteps: int, is_test: bool = False):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 65)
    print(f"SMIT 베이커리 RL 에이전트 학습 ({'1분 시험 학습' if is_test else '본 학습'})")
    print(f"알고리즘: PPO (Stable-Baselines3)")
    print(f"학습 장치: {device.upper()} ({torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU'})")
    print(f"학습 기간: {config.TRAIN_START_DATE} ~ {config.TRAIN_END_DATE} (무작위 28일 에피소드)")
    print(f"목표 스텝 수: {total_timesteps:,} 스텝")
    print("=" * 65)

    # 1. 학습 환경 생성 (기본: 학습 기간 2016~2024 내 무작위 28일 에피소드)
    env = BakeryEnv()

    # 2. 콜백 설정
    exp_path = os.path.join("results", "experience_sample_v1.csv")
    curve_csv = os.path.join("results", "learning_curve_v1.csv")
    curve_png = os.path.join("results", "learning_curve_v1.png")
    model_dir = os.path.join("results", "models")
    os.makedirs(model_dir, exist_ok=True)
    model_save_path = os.path.join(model_dir, "v1")

    exp_cb = ExperienceRecorderCallback(save_path=exp_path, max_steps=1000)
    curve_cb = LearningCurveCallback(csv_path=curve_csv, img_path=curve_png)

    # 3. PPO 모델 초기화 (안정적인 하이퍼파라미터)
    # n_steps: 한 번에 수집하는 스텝 수 (28일 * 10에피소드 = 280)
    # batch_size: GPU 병렬 업데이트 크기 (64)
    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=280,
        batch_size=70,  # 280의 약수로 나누어떨어지게 설정
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        device=device,
        seed=config.TRAIN_SEED
    )

    # 4. 학습 시작 및 시간 측정
    start_time = time.time()
    try:
        model.learn(total_timesteps=total_timesteps, callback=[exp_cb, curve_cb])
    except Exception as e:
        print(f"\n[오류 발생] 학습 중 오류가 발생했습니다: {e}")
        raise e

    elapsed_time = time.time() - start_time
    sps = total_timesteps / max(0.001, elapsed_time)
    sec_per_step = elapsed_time / max(1, total_timesteps)

    # 5. 모델 저장
    model.save(model_save_path)
    print(f"\n[모델 저장 완료] {model_save_path}.zip")

    print("\n" + "=" * 65)
    print("학습 벤치마크 결과:")
    print(f"- 총 소요 시간: {elapsed_time:.2f}초 ({elapsed_time / 60:.2f}분)")
    print(f"- 완료된 스텝 수: {total_timesteps:,} 스텝")
    print(f"- 초당 스텝 수 (SPS): {sps:.1f} steps/s")
    print(f"- 스텝당 소요 시간: {sec_per_step * 1000:.3f} ms/step ({sec_per_step:.6f} 초/스텝)")
    
    # 10분(600초) 안쪽 권장 스텝 수 계산
    safe_target_steps = int(sps * 500)  # 500초(약 8분 20초) 기준 안전 스텝 수
    # 만 단위로 반올림
    safe_target_steps = max(20000, round(safe_target_steps / 10000) * 10000)
    print(f"- 내 PC 10분 안쪽 본 학습 권장 스텝 수: {safe_target_steps:,} 스텝 (예상 약 {safe_target_steps / sps / 60:.1f}분 소요)")
    print("=" * 65)

    return {
        "elapsed_time": elapsed_time,
        "sps": sps,
        "sec_per_step": sec_per_step,
        "safe_target_steps": safe_target_steps
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SMIT 베이커리 PPO 학습")
    parser.add_argument("--test", action="store_true", help="1분 안쪽 시험 학습 실행")
    parser.add_argument("--steps", type=int, default=None, help="학습할 총 스텝 수")
    args = parser.parse_args()

    if args.test:
        steps = 2800  # 100 에피소드 (28일 * 100 = 2,800스텝, RTX 3090 Ti 기준 약 15~20초 소요)
        run_train(total_timesteps=steps, is_test=True)
    else:
        steps = args.steps if args.steps else 50000
        run_train(total_timesteps=steps, is_test=False)
