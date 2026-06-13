#!/usr/bin/env python3
"""
GAT 模型長期穩定性統計驗證腳本
==================================
Phase 1 (立即可跑): Train/Test IC 比值表 + 近似 t 統計量
Phase 2 (需要逐日 IC CSV): Newey-West t 檢定、Diebold-Mariano、Block Bootstrap

執行環境:
  /Users/luoyi/Desktop/shortvideo_mmgcn_poc/.venv/bin/python stability_tests.py

如何取得 Phase 2 所需的逐日 IC CSV:
  在你的評估程式碼計算每日 IC 的地方，加入:
    pd.DataFrame({'date': dates, 'ic': daily_ic_list}).to_csv(
        f'{output_dir}/daily_ic_series.csv', index=False)
"""

import json, os, sys
import numpy as np
from pathlib import Path

RUNS_BASE = Path("/Users/luoyi/Desktop/Roy_Thesis/runs_gpu_static_to_20250601/static")
WINDOWS   = ["short", "medium", "long"]

MODEL_LABELS = {
    "baseline_linear"          : "Linear",
    "baseline_xgboost"         : "XGBoost",
    "baseline_lstm"            : "LSTM",
    "mlp"                      : "DNN",
    "gat_industry"             : "GAT-industry",
    "gat_universe"             : "GAT-universe",
    "gat_two_graph_no_neutral" : "GAT-TwoGraph",
    "dmfm_ind_neutral"         : "GAT-IndNeutral",
    "dmfm_full"                : "GAT-full",
}

# ─────────────────────────────────────────────────────────────────────────────
# 工具函數
# ─────────────────────────────────────────────────────────────────────────────

def load_metrics(window: str, model_dir: str) -> dict | None:
    p = RUNS_BASE / window / model_dir / "metrics.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def newey_west_se(x: np.ndarray, lags: int) -> float:
    """
    Newey-West (1987) HAC 標準誤（純 numpy 實作，不需 statsmodels）。
    Bartlett 核心：w_j = 1 - j/(lags+1)
    回傳 SE of sample mean.
    """
    n = len(x)
    d = x - x.mean()
    gamma_0 = np.dot(d, d) / n
    nw_var = gamma_0
    for j in range(1, lags + 1):
        w = 1.0 - j / (lags + 1)
        gamma_j = np.dot(d[j:], d[:-j]) / n
        nw_var += 2.0 * w * gamma_j
    # SE of mean = sqrt(Var / n)
    return float(np.sqrt(max(nw_var, 0.0) / n))


def block_bootstrap_icir(ic: np.ndarray,
                          block_size: int = 10,
                          n_boot: int = 2000,
                          seed: int = 42) -> tuple[float, float, np.ndarray]:
    """
    Stationary block bootstrap for ICIR = mean(IC) / std(IC).
    回傳 (lower_95, upper_95, bootstrap_distribution).
    """
    rng = np.random.default_rng(seed)
    n   = len(ic)
    boot_icirs = []
    for _ in range(n_boot):
        idx = []
        while len(idx) < n:
            start = rng.integers(0, n)
            block = [start + k for k in range(block_size)]
            idx.extend(block)
        idx = np.array(idx[:n]) % n   # wrap around (circular)
        sample = ic[idx]
        s_std  = sample.std(ddof=1)
        if s_std > 0:
            boot_icirs.append(sample.mean() / s_std)
    boot_icirs = np.array(boot_icirs)
    lo = np.percentile(boot_icirs, 2.5)
    hi = np.percentile(boot_icirs, 97.5)
    return lo, hi, boot_icirs


def diebold_mariano(ic_a: np.ndarray,
                    ic_b: np.ndarray,
                    lags: int | None = None) -> tuple[float, float]:
    """
    Diebold-Mariano (1995) 單側檢定：H0: E[IC_A - IC_B] <= 0
    回傳 (DM-statistic, one-tailed p-value).
    使用 Newey-West SE for d = ic_a - ic_b.
    """
    from scipy.stats import norm
    d = ic_a - ic_b
    n = len(d)
    if lags is None:
        lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    se = newey_west_se(d, lags)
    if se == 0:
        return float("inf"), 0.0
    dm  = d.mean() / se
    p1  = 1.0 - norm.cdf(dm)   # one-tailed: A > B
    return float(dm), float(p1)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Train/Test IC 比值表（無需逐日 IC）
# ─────────────────────────────────────────────────────────────────────────────

def phase1_ratio_table():
    print("\n" + "=" * 70)
    print("Phase 1: Train IC vs Test IC 比值表")
    print("=" * 70)

    header = f"{'模型':<22} {'視窗':<8} {'Train IC':>9} {'Test IC':>9} {'比值':>7} {'Test ICIR':>10}"
    print(header)
    print("-" * 70)

    for window in WINDOWS:
        for model_dir, label in MODEL_LABELS.items():
            m = load_metrics(window, model_dir)
            if m is None:
                continue
            tr_ic = m["train"]["IC"]
            te_ic = m["test"]["IC"]
            te_icir = m["test"]["ICIR"]
            ratio = tr_ic / te_ic if te_ic > 1e-9 else float("inf")
            flag = " ⚠" if ratio > 10 else ""
            print(f"{label:<22} {window:<8} {tr_ic:>9.4f} {te_ic:>9.4f} {ratio:>6.1f}x{flag:2}  {te_icir:>9.3f}")
        print()


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1b: 近似 t 統計量（用 mean / (std/√n) 估算，未做 NW 修正）
# 僅供快速參考，Phase 2 才是正式版
# ─────────────────────────────────────────────────────────────────────────────

def phase1_approx_tstat():
    print("\n" + "=" * 70)
    print("Phase 1b: 近似 t 統計量（naive，未修正序列相關）")
    print("說明: t = DailyIC / (DailyIC/ICIR / sqrt(n_test_days))")
    print("=" * 70)

    header = f"{'模型':<22} {'視窗':<8} {'DailyIC':>9} {'ICIR':>7} {'n_days':>7} {'t-stat':>8}"
    print(header)
    print("-" * 70)

    for window in WINDOWS:
        for model_dir, label in MODEL_LABELS.items():
            m = load_metrics(window, model_dir)
            if m is None:
                continue
            daily_ic = m["test"]["DailyIC"]
            icir     = m["test"]["ICIR"]
            n_days   = m["split"]["test_days"]
            std_ic   = daily_ic / icir if icir > 1e-9 else float("nan")
            t_naive  = daily_ic / (std_ic / np.sqrt(n_days)) if std_ic > 0 else float("nan")
            sig      = "***" if abs(t_naive) > 3.29 else ("**" if abs(t_naive) > 2.58 else ("*" if abs(t_naive) > 1.96 else ""))
            print(f"{label:<22} {window:<8} {daily_ic:>9.4f} {icir:>7.3f} {n_days:>7}  {t_naive:>7.2f} {sig}")
        print()

    print("顯著水準: * p<.05  ** p<.01  *** p<.001（naive 估算，僅供參考）")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: 正式統計檢定（需要逐日 IC CSV）
# ─────────────────────────────────────────────────────────────────────────────

def phase2_formal_tests(window: str = "long",
                         model_a: str = "dmfm_ind_neutral",
                         model_b: str = "mlp"):
    """
    正式三項統計檢定。
    需要: {runs_dir}/{window}/{model}/daily_ic_series.csv
    CSV 格式: date, ic  (兩欄，header 為此名稱)
    """
    import csv

    print("\n" + "=" * 70)
    print(f"Phase 2: 正式統計檢定 | 視窗={window}")
    print("=" * 70)

    def load_ic_series(model_dir: str) -> np.ndarray | None:
        p = RUNS_BASE / window / model_dir / "daily_ic_series.csv"
        if not p.exists():
            return None
        with open(p) as f:
            reader = csv.DictReader(f)
            return np.array([float(row["ic"]) for row in reader])

    label_a = MODEL_LABELS.get(model_a, model_a)
    label_b = MODEL_LABELS.get(model_b, model_b)

    ic_a = load_ic_series(model_a)
    ic_b = load_ic_series(model_b)

    if ic_a is None:
        print(f"\n[!] 找不到 {model_a}/daily_ic_series.csv")
        print("    請在評估程式碼中加入以下儲存步驟（見腳本頂部說明）")
        return
    if ic_b is None:
        print(f"\n[!] 找不到 {model_b}/daily_ic_series.csv")
        return

    n = min(len(ic_a), len(ic_b))
    ic_a, ic_b = ic_a[:n], ic_b[:n]

    # 推薦 lag 數：Andrews (1991) 規則
    lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    print(f"\n使用 Newey-West lag 數 = {lags}（Andrews 1991 規則）\n")

    # ── 1. Newey-West t 檢定（對每個模型）──────────────────────────────────
    print("─" * 50)
    print("1. Newey-West t 檢定  H₀: E[IC] = 0")
    print("─" * 50)

    from scipy.stats import norm

    for ic, label in [(ic_a, label_a), (ic_b, label_b)]:
        se   = newey_west_se(ic, lags)
        t    = ic.mean() / se
        p2   = 2 * (1 - norm.cdf(abs(t)))   # two-tailed
        p1   = 1 - norm.cdf(t)              # one-tailed (IC > 0)
        sig  = "***" if p1 < 0.001 else ("**" if p1 < 0.01 else ("*" if p1 < 0.05 else "n.s."))
        print(f"  {label:<20}  mean={ic.mean():.4f}  NW-SE={se:.5f}  t={t:.2f}  p(一尾)={p1:.4f} {sig}")

    # ── 2. Diebold-Mariano 檢定（A 是否顯著優於 B）──────────────────────────
    print()
    print("─" * 50)
    print(f"2. Diebold-Mariano 檢定  H₀: {label_a} 不優於 {label_b}")
    print("─" * 50)

    dm_stat, p_dm = diebold_mariano(ic_a, ic_b, lags)
    sig_dm = "***" if p_dm < 0.001 else ("**" if p_dm < 0.01 else ("*" if p_dm < 0.05 else "n.s."))
    print(f"  IC 差均值 = {(ic_a - ic_b).mean():.4f}")
    print(f"  DM statistic = {dm_stat:.3f}")
    print(f"  p-value (一尾) = {p_dm:.4f} {sig_dm}")
    if p_dm < 0.05:
        print(f"  → 拒絕 H₀，{label_a} 截面排序訊號顯著優於 {label_b}")
    else:
        print(f"  → 未能拒絕 H₀（差異未達統計顯著）")

    # ── 3. Block Bootstrap ICIR 信賴區間 ────────────────────────────────────
    print()
    print("─" * 50)
    print("3. Block Bootstrap ICIR 95% 信賴區間  (block_size=10, B=2000)")
    print("─" * 50)

    for ic, label in [(ic_a, label_a), (ic_b, label_b)]:
        actual_icir = ic.mean() / ic.std(ddof=1)
        lo, hi, _ = block_bootstrap_icir(ic, block_size=10, n_boot=2000)
        sig_str = "✓ 顯著 > 0" if lo > 0 else "✗ CI 包含 0"
        print(f"  {label:<20}  ICIR={actual_icir:.3f}  95% CI=[{lo:.3f}, {hi:.3f}]  {sig_str}")

    print()
    print("顯著水準: * p<.05  ** p<.01  *** p<.001")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2b: Monthly IC 勝率（需要逐日 IC CSV）
# ─────────────────────────────────────────────────────────────────────────────

def phase2_monthly_winrate(window: str = "long"):
    """
    計算各模型逐月 IC 均值，回報月度勝率（IC > 0 的月份比例）。
    CSV 格式: date (YYYY-MM-DD), ic
    """
    import csv
    from collections import defaultdict

    print("\n" + "=" * 70)
    print(f"Phase 2b: Monthly IC 勝率 | 視窗={window}")
    print("=" * 70)
    header = f"{'模型':<22} {'ICIR':>7} {'月份數':>6} {'正IC月份':>8} {'勝率':>7}"
    print(header)
    print("-" * 50)

    for model_dir, label in MODEL_LABELS.items():
        p = RUNS_BASE / window / model_dir / "daily_ic_series.csv"
        if not p.exists():
            continue
        monthly = defaultdict(list)
        with open(p) as f:
            for row in csv.DictReader(f):
                month = row["date"][:7]   # "YYYY-MM"
                monthly[month].append(float(row["ic"]))
        if not monthly:
            continue
        monthly_ic = np.array([np.mean(v) for v in monthly.values()])
        win_rate   = (monthly_ic > 0).mean()
        icir       = monthly_ic.mean() / monthly_ic.std(ddof=1) if len(monthly_ic) > 1 else float("nan")
        n_months   = len(monthly_ic)
        n_pos      = int((monthly_ic > 0).sum())
        print(f"{label:<22} {icir:>7.3f} {n_months:>6} {n_pos:>8} {win_rate:>6.1%}")


# ─────────────────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Phase 1: 立即可跑
    phase1_ratio_table()
    phase1_approx_tstat()

    # Phase 2: 需要 daily_ic_series.csv（先跑 scripts/regenerate_daily_ic_csv.sh）
    has_any_csv = any(
        (RUNS_BASE / w / m / "daily_ic_series.csv").exists()
        for w in WINDOWS for m in MODEL_LABELS
    )
    if has_any_csv:
        phase2_formal_tests(
            window  = "long",
            model_a = "dmfm_ind_neutral",
            model_b = "mlp",
        )
        phase2_monthly_winrate(window="long")
    else:
        print("\n[Phase 2 尚未解鎖]")
        print("  請先執行: bash scripts/regenerate_daily_ic_csv.sh")

    print("\n" + "=" * 70)
    print("Phase 2 說明:")
    print("  在評估腳本中，找到計算每日 IC 的地方，加入以下兩行:")
    print()
    print("    import pandas as pd")
    print("    pd.DataFrame({'date': date_list, 'ic': daily_ic_list})")
    print("      .to_csv(f'{output_dir}/daily_ic_series.csv', index=False)")
    print()
    print("  date_list: List[str]，格式 'YYYY-MM-DD'，長度 = 測試天數")
    print("  daily_ic_list: List[float]，每天截面 IC 值，長度相同")
    print("=" * 70)
