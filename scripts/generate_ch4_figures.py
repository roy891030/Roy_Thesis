#!/usr/bin/env python3
"""
Chapter-4 comparison figures.
Colour palette: hex values match thesis_colors.tex TikZ definitions exactly.
  Short window / XGBoost / Baseline : AMBER   = thesisAmber  (#C98C1E)
  Medium window                     : FOREST  = thesisForest (#2D7A4F)
  Long window / GAT family          : BLUE    = thesisBlue   (#2B6CB0)
  Train IC / primary signal         : BLUE    = thesisBlue   (#2B6CB0)
  Test IC  / warning / DNN          : CRIMSON = thesisCrimson (#9B2235)
  GAT-neutral                       : PURPLE  = thesisPurple (#6B46C1)
  Overview – Linear                 : MIDGRAY = thesisMidGray (#82919F)
  Overview – LSTM                   : TEAL    = thesisTeal   (#4A9D8F)
Typography: serif (Times New Roman + Chinese fallback), sized for \textwidth embed.
"""

import json, os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.font_manager as _fm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ── register Noto Serif CJK TC from local path ───────────────────────────────
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "10_NotoSerifCJKtc", "OTF", "TraditionalChinese")
for _wt in ("Regular", "Bold", "Medium", "Light"):
    _fp = os.path.join(_FONT_DIR, f"NotoSerifCJKtc-{_wt}.otf")
    if os.path.exists(_fp):
        _fm.fontManager.addfont(_fp)

# ── thesis palette (mirrors thesis_colors.tex TikZ definitions exactly) ──────
BLUE    = "#2B6CB0"   # thesisBlue   RGB(43,108,176)
AMBER   = "#C98C1E"   # thesisAmber  RGB(201,140,30)
CRIMSON = "#9B2235"   # thesisCrimson RGB(155,35,53)
FOREST  = "#2D7A4F"   # thesisForest RGB(45,122,79)  – medium-window colour
DARK    = "#2D3748"   # thesisDark   RGB(45,55,72)
LIGHT   = "#EDF2F7"   # thesisLight  RGB(237,242,247)
PURPLE  = "#6B46C1"   # thesisPurple RGB(107,70,193)
TEAL    = "#4A9D8F"   # thesisTeal   RGB(74,157,143) – LSTM line
MIDGRAY = "#82919F"   # thesisMidGray RGB(130,145,160) – Linear / grid

OUT_DIR = "/Users/luoyi/Desktop/Roy_Thesis/img"
RUNS    = "/Users/luoyi/Desktop/Roy_Thesis/runs_gpu_static_to_20250601/static"

MODEL_MAP = {
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
WINDOWS   = ["short", "medium", "long"]
WIN_LABEL = {"short": "短期", "medium": "中期", "long": "長期"}
WINDOW_COLORS = {"short": AMBER, "medium": FOREST, "long": BLUE}

# ── global rcParams aligned with thesis typography ───────────────────────────
# Thesis body: 12 pt Times New Roman + CJK.  Figures embed at \textwidth ≈ 8.5 in;
# scale factor ≈ 0.74 → 14 pt matplotlib ≈ 10.4 pt in PDF ≈ thesis body size.
# Tick/legend at 12 pt ≈ 8.9 pt in PDF (standard for thesis figures).
# font.family: Noto Serif CJK TC — single face covering Latin + Traditional
# Chinese glyphs in a serif style matching the thesis body (Times New Roman /
# Kaiti TC). Registered from local 10_NotoSerifCJKtc/ at script startup.
RC = {
    "font.family"      : "Noto Serif CJK TC",
    "font.size"        : 14,          # ≈10.4 pt in PDF at 8.5-inch embed
    "axes.titlesize"   : 15,          # ≈11.1 pt
    "axes.labelsize"   : 14,          # ≈10.4 pt
    "xtick.labelsize"  : 12,          # ≈ 8.9 pt
    "ytick.labelsize"  : 12,          # ≈ 8.9 pt
    "legend.fontsize"  : 12,          # ≈ 8.9 pt
    "axes.spines.top"  : False,
    "axes.spines.right": False,
    "axes.linewidth"   : 0.8,
    "axes.edgecolor"   : MIDGRAY,
    "xtick.color"      : DARK,
    "ytick.color"      : DARK,
    "text.color"       : DARK,
    "figure.facecolor" : "white",
    "axes.facecolor"   : "white",
    "savefig.dpi"      : 300,
    "savefig.bbox"     : "tight",
}

# For narrow single-panel figures (≈7.5 in, scale≈0.84): 12 pt ≈ 10.1 pt in PDF.
RC_NARROW = {**RC,
    "font.size"      : 12,
    "axes.titlesize" : 13,
    "axes.labelsize" : 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
}

def ax_style(ax):
    ax.yaxis.grid(True, linestyle="--", linewidth=0.7, color="#D8E2EE", alpha=0.9)
    ax.set_axisbelow(True)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="both", length=3, color=MIDGRAY)

def bar_label(ax, bar, v, fmt, offset, is_neg_ok=False):
    """Place a value label above (positive) or below (negative) a bar."""
    if v >= 0:
        ax.text(bar.get_x() + bar.get_width() / 2,
                v + offset, format(v, fmt),
                ha="center", va="bottom", fontsize=11,
                color=DARK, clip_on=False)
    else:
        ax.text(bar.get_x() + bar.get_width() / 2,
                v - offset * 0.5, format(v, fmt),
                ha="center", va="top", fontsize=11,
                color=DARK, clip_on=False)

def set_ylim_with_room(ax, all_vals, top_frac=0.22, bot_frac=0.18):
    """Set ylim so bar labels never clip."""
    lo, hi = min(all_vals), max(all_vals)
    span   = max(hi - lo, abs(hi) * 0.2, 0.01)
    ax.set_ylim(lo - span * bot_frac, hi + span * top_frac)


# ── load data ────────────────────────────────────────────────────────────────
def load_data():
    data = {}
    for w in WINDOWS:
        data[w] = {}
        for mkey, mname in MODEL_MAP.items():
            mp = os.path.join(RUNS, w, mkey)
            with open(os.path.join(mp, "metrics.json"))   as f: m = json.load(f)
            with open(os.path.join(mp, "portfolio.json")) as f: p = json.load(f)
            data[w][mname] = {
                "train_ic"  : m["train"]["IC"],
                "test_ic"   : m["test"]["IC"],
                "daily_ic"  : m["test"]["DailyIC"],
                "icir"      : m["test"]["ICIR"],
                "sharpe"    : p["strategy"]["sharpe"],
                "annual_ret": p["strategy"]["annual_return"],
                "total_ret" : p["strategy"]["total_return"],
                "max_dd"    : p["strategy"]["max_drawdown"],
            }
    return data

D = load_data()

CATEGORY_MODELS = {
    "Linear": ["Linear"],
    "XGBoost": ["XGBoost"],
    "LSTM": ["LSTM"],
    "DNN": ["DNN"],
    "GAT 拓樸系列": ["GAT-industry", "GAT-universe", "GAT-TwoGraph"],
    "GAT 中性化系列": ["GAT-IndNeutral", "GAT-full"],
}

CATEGORY_STYLES = {
    "Linear": dict(color=MIDGRAY, linestyle=(0, (3, 1, 1, 1)), linewidth=1.8,
                   marker="o", markersize=6),
    "XGBoost": dict(color=AMBER, linestyle="--", linewidth=1.8,
                    marker="s", markersize=6),
    "LSTM": dict(color=TEAL, linestyle="--", linewidth=1.8,
                 marker="v", markersize=6),
    "DNN": dict(color=CRIMSON, linestyle="-", linewidth=2.2,
                marker="D", markersize=7),
    "GAT 拓樸系列": dict(color=BLUE, linestyle="-", linewidth=2.2,
                         marker="^", markersize=8),
    "GAT 中性化系列": dict(color=PURPLE, linestyle="-", linewidth=2.8,
                           marker="*", markersize=9),
}

def category_values(category, metric):
    models = CATEGORY_MODELS[category]
    scale = 100 if metric == "total_ret" else 1
    return [np.mean([D[w][m][metric] for m in models]) * scale for w in WINDOWS]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig A – Baseline model comparison                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_baseline_comparison():
    models  = ["Linear", "XGBoost", "LSTM", "DNN"]
    bw, gap = 0.22, 0.06
    x       = np.arange(len(models))

    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 2, figsize=(8.5, 5.0))
        fig.subplots_adjust(wspace=0.30, top=0.88)

        for col, (metric, ylabel, title, fmt) in enumerate([
            ("daily_ic", "測試 Daily IC",   "不同訓練視窗之測試 Daily IC", ".3f"),
            ("sharpe",   "測試 Sharpe 比率", "不同訓練視窗之測試 Sharpe 比率", ".2f"),
        ]):
            ax = axes[col]
            offsets  = np.array([-1, 0, 1]) * (bw + gap / 2)
            all_vals = []

            for w, off in zip(WINDOWS, offsets):
                vals = [D[w][m][metric] for m in models]
                all_vals.extend(vals)
                bars = ax.bar(x + off, vals, width=bw,
                              color=WINDOW_COLORS[w], label=WIN_LABEL[w],
                              edgecolor="white", linewidth=0.5, zorder=3)
                offset_amt = 0.0003 if metric == "daily_ic" else 0.012
                for bar, v in zip(bars, vals):
                    bar_label(ax, bar, v, fmt, offset_amt)

            ax.set_xticks(x)
            ax.set_xticklabels(models, fontsize=12)
            ax.set_ylabel(ylabel, color=DARK)
            ax.set_title(title, color=DARK, pad=8)
            ax_style(ax)
            set_ylim_with_room(ax, all_vals, top_frac=0.26, bot_frac=0.20)

            if metric == "sharpe":
                ax.axhline(0, color=MIDGRAY, linewidth=0.8, linestyle="--", zorder=2)

        handles = [Patch(facecolor=WINDOW_COLORS[w], label=WIN_LABEL[w]) for w in WINDOWS]
        fig.legend(handles=handles, loc="upper center", ncol=3,
                   bbox_to_anchor=(0.5, 1.00), frameon=False,
                   handlelength=1.4, handletextpad=0.5)

        fig.savefig(os.path.join(OUT_DIR, "ch4_fig_baseline_comparison.png"))
        plt.close(fig)
        print("✓  ch4_fig_baseline_comparison.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig B – XGBoost train-vs-test IC gap                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_xgboost_gap():
    x     = np.arange(3)
    bw    = 0.32
    train = [D[w]["XGBoost"]["train_ic"] for w in WINDOWS]
    test  = [D[w]["XGBoost"]["test_ic"]  for w in WINDOWS]
    ratio = [tr / te for tr, te in zip(train, test)]

    with plt.rc_context(RC_NARROW):
        fig, ax = plt.subplots(figsize=(7.5, 6.2))

        b1 = ax.bar(x - bw/2, train, width=bw, color=BLUE,
                    label="Train IC", edgecolor="white", linewidth=0.5, zorder=3)
        b2 = ax.bar(x + bw/2, test,  width=bw, color=CRIMSON,
                    label="Test IC",  edgecolor="white", linewidth=0.5, zorder=3)

        # ── Train IC: value inside bar (white bold) ──
        for bar, v in zip(b1, train):
            cx = bar.get_x() + bar.get_width() / 2
            cy = v * 0.50
            ax.text(cx, cy, f"{v:.4f}",
                    ha="center", va="center", fontsize=11,
                    color="white", fontweight="bold", clip_on=False)

        # ── Test IC: value above bar ──
        for bar, v in zip(b2, test):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    v + 0.012, f"{v:.4f}",
                    ha="center", va="bottom", fontsize=10,
                    color=DARK, clip_on=False)

        # ── ratio annotation centred between bars ──
        for xi, (tr, r) in enumerate(zip(train, ratio)):
            ax.text(xi, tr + 0.150, f"×{r:.1f}",
                    ha="center", va="bottom", fontsize=13,
                    fontweight="bold", color=DARK, clip_on=False)

        ax.set_xticks(x)
        ax.set_xticklabels([WIN_LABEL[w] for w in WINDOWS])
        ax.set_ylabel("Information Coefficient (IC)", color=DARK)
        ax.set_title("XGBoost: Train IC vs. Test IC by Window", color=DARK, pad=8)
        ax_style(ax)
        ax.legend(frameon=False, handlelength=1.4, loc="upper left")
        # explicit xlim with left margin so Short-window text is never clipped
        ax.set_xlim(-0.55, 2.55)
        # ample top room for the tallest annotation (train_long + 0.15 + text height)
        ax.set_ylim(0, max(train) * 1.52)

        fig.savefig(os.path.join(OUT_DIR, "ch4_fig_xgboost_gap.png"))
        plt.close(fig)
        print("✓  ch4_fig_xgboost_gap.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig C – Graph topology comparison                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_topology_comparison():
    models  = ["DNN", "GAT-industry", "GAT-universe", "GAT-TwoGraph"]
    win_clr = {"medium": AMBER, "long": BLUE}
    bw, gap = 0.30, 0.08
    x       = np.arange(len(models))
    metrics = [
        ("daily_ic", "Daily IC",     "Daily IC by Topology",     ".3f"),
        ("icir",     "ICIR",         "ICIR by Topology",         ".2f"),
        ("sharpe",   "Sharpe Ratio", "Sharpe Ratio by Topology", ".2f"),
    ]

    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 3, figsize=(8.5, 4.8))
        fig.subplots_adjust(wspace=0.32, top=0.88)

        for col, (metric, ylabel, title, fmt) in enumerate(metrics):
            ax    = axes[col]
            offsets   = [-bw/2 - gap/2, bw/2 + gap/2]
            all_vals  = []

            for w, off in zip(["medium", "long"], offsets):
                vals = [D[w][m][metric] for m in models]
                all_vals.extend(vals)
                bars = ax.bar(x + off, vals, width=bw,
                              color=win_clr[w], label=WIN_LABEL[w],
                              edgecolor="white", linewidth=0.5, zorder=3)
                offset_amt = 0.0005 if metric == "daily_ic" else 0.012
                for bar, v in zip(bars, vals):
                    bar_label(ax, bar, v, fmt, offset_amt)

            ax.set_xticks(x)
            ax.set_xticklabels(models, fontsize=10, rotation=15, ha="right")
            ax.set_ylabel(ylabel, color=DARK)
            ax.set_title(title, color=DARK, pad=8)
            ax_style(ax)
            set_ylim_with_room(ax, all_vals)

        handles = [Patch(facecolor=win_clr[w], label=WIN_LABEL[w])
                   for w in ["medium", "long"]]
        fig.legend(handles=handles, loc="upper center", ncol=2,
                   bbox_to_anchor=(0.5, 1.00), frameon=False,
                   handlelength=1.4)

        fig.savefig(os.path.join(OUT_DIR, "ch4_fig_topology_comparison.png"))
        plt.close(fig)
        print("✓  ch4_fig_topology_comparison.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig D – Neutralization mechanism comparison                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_neutralization():
    models  = ["GAT-industry", "GAT-TwoGraph", "GAT-IndNeutral", "GAT-full"]
    bw, gap = 0.30, 0.08
    x       = np.arange(len(models))
    metrics = [
        ("daily_ic", "測試 Daily IC", "測試 Daily IC", ".3f"),
        ("icir",     "測試 ICIR",     "測試 ICIR", ".3f"),
        ("sharpe",   "測試 Sharpe 比率", "測試 Sharpe 比率", ".3f"),
    ]

    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 3, figsize=(8.5, 4.5))
        fig.subplots_adjust(wspace=0.34, top=0.88)

        for col, (metric, ylabel, title, fmt) in enumerate(metrics):
            ax       = axes[col]
            offsets  = [-bw/2 - gap/2, bw/2 + gap/2]
            all_vals = []

            for w, off in zip(["medium", "long"], offsets):
                vals = [D[w][m][metric] for m in models]
                all_vals.extend(vals)
                bars = ax.bar(x + off, vals, width=bw,
                              color=WINDOW_COLORS[w], label=WIN_LABEL[w],
                              edgecolor="white", linewidth=0.5, zorder=3)
                for bar, v in zip(bars, vals):
                    bar_label(ax, bar, v, fmt, 0.0005 if metric == "daily_ic" else 0.010)

            ax.set_xticks(x)
            ax.set_xticklabels(models, fontsize=10, rotation=12, ha="right")
            ax.set_ylabel(ylabel, color=DARK)
            ax.set_title(title, color=DARK, pad=8)
            ax_style(ax)
            set_ylim_with_room(ax, all_vals)

        handles = [Patch(facecolor=WINDOW_COLORS[w], label=WIN_LABEL[w])
                   for w in ["medium", "long"]]
        fig.legend(handles=handles, loc="upper center", ncol=2,
                   bbox_to_anchor=(0.5, 1.00), frameon=False,
                   handlelength=1.4)

        fig.savefig(os.path.join(OUT_DIR, "ch4_fig_neutralization.png"))
        plt.close(fig)
        print("✓  ch4_fig_neutralization.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig E – Window-length effect across model groups (line chart)         ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_window_effect():
    xs        = [0, 1, 2]
    xlabels   = [WIN_LABEL[w] for w in WINDOWS]

    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 2, figsize=(8.5, 4.5))
        fig.subplots_adjust(wspace=0.30)

        for col, (metric, ylabel, title) in enumerate([
            ("sharpe",   "測試 Sharpe 比率", "不同訓練視窗之測試 Sharpe 比率"),
            ("daily_ic", "測試 Daily IC",     "不同訓練視窗之測試 Daily IC"),
        ]):
            ax = axes[col]
            for category in CATEGORY_MODELS:
                ax.plot(xs, category_values(category, metric), label=category,
                        **CATEGORY_STYLES[category],
                        zorder=4, clip_on=False)
            if metric == "sharpe":
                ax.axhline(0, color=MIDGRAY, linewidth=0.9, linestyle=":", zorder=1)
            ax.set_xticks(xs)
            ax.set_xticklabels(xlabels)
            ax.set_ylabel(ylabel, color=DARK)
            ax.set_title(title, color=DARK, pad=8)
            ax_style(ax)

        handles = [Line2D([0], [0], label=category, **CATEGORY_STYLES[category])
                   for category in CATEGORY_MODELS]
        fig.legend(handles=handles,
                   loc="upper center", ncol=6,
                   bbox_to_anchor=(0.5, 1.02), frameon=False,
                   handlelength=1.8, handletextpad=0.5)

        fig.savefig(os.path.join(OUT_DIR, "ch4_fig_window_effect.png"))
        plt.close(fig)
        print("✓  ch4_fig_window_effect.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig F – Table 14 visualisation: all model categories × all windows    ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_portfolio_metrics_overview():
    xs      = [0, 1, 2]
    xlabels = [WIN_LABEL[w] for w in WINDOWS]
    panels  = [
        ("daily_ic",  "測試 Daily IC",   "各模型類別之測試 Daily IC"),
        ("icir",      "測試 ICIR",       "各模型類別之測試 ICIR"),
        ("sharpe",    "測試 Sharpe 比率", "各模型類別之測試 Sharpe 比率"),
        ("total_ret", "測試總報酬（%）", "各模型類別之測試總報酬"),
    ]

    with plt.rc_context(RC):
        fig, axes = plt.subplots(2, 2, figsize=(8.5, 7.5))
        fig.subplots_adjust(hspace=0.38, wspace=0.30)

        for idx, (metric, ylabel, title) in enumerate(panels):
            ax = axes[idx // 2][idx % 2]
            for category in CATEGORY_MODELS:
                ax.plot(xs, category_values(category, metric), label=category,
                        **CATEGORY_STYLES[category],
                        zorder=4, clip_on=False)

            if metric in ("sharpe", "total_ret"):
                ax.axhline(0, color=MIDGRAY, lw=0.9, ls=":", zorder=1)

            ax.set_xticks(xs)
            ax.set_xticklabels(xlabels)
            ax.set_ylabel(ylabel, color=DARK)
            ax.set_title(title, color=DARK, pad=7)
            ax_style(ax)

            if metric == "total_ret":
                ax.yaxis.set_major_formatter(
                    mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))

        handles = [Line2D([0], [0], label=category, **CATEGORY_STYLES[category])
                   for category in CATEGORY_MODELS]

        fig.legend(handles=handles,
                   loc="lower center", ncol=3,
                   bbox_to_anchor=(0.5, -0.06),
                   frameon=False,
                   handlelength=1.8, handletextpad=0.5, columnspacing=1.2)

        fig.savefig(OUT_DIR + "/ch4_fig_portfolio_metrics_overview.png",
                    bbox_inches="tight")
        plt.close(fig)
        print("✓  ch4_fig_portfolio_metrics_overview.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig G – Topology heatmap (replaces bar chart, matches Table 11)       ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_topology_heatmap():
    """
    Coloured-cell table showing Long-window topology comparison.
    Each column is independently normalised white→thesisBlue (rank 0→1).
    Max DD: higher value (less negative) = better = darker.
    Left stripe: Amber=DNN, Blue=GAT, Purple=GAT-neutral.
    """
    from matplotlib.patches import Rectangle

    BLUE_RGB = np.array([43/255, 108/255, 176/255])

    row_names  = ["DNN", "GAT-universe", "GAT-industry",
                  "GAT-TwoGraph", "GAT-IndNeutral", "GAT-full"]
    row_stripes = [AMBER, BLUE, BLUE, BLUE, PURPLE, PURPLE]

    col_names  = ["Daily IC", "ICIR", "Sharpe", "Ann. Ret.", "Total Ret.", "Max DD", "DirAcc"]
    col_vals   = [
        [0.0535, 0.0452, 0.0543, 0.0512, 0.0590, 0.0583],   # Daily IC
        [0.726,  0.526,  0.677,  0.504,  0.786,  0.735],    # ICIR
        [1.564,  1.506,  1.779,  1.827,  1.803,  1.849],    # Sharpe
        [35.35,  36.01,  38.13,  39.45,  38.70,  42.02],    # Ann Ret %
        [106.45, 108.10, 120.83, 127.33, 123.60, 139.08],   # Total Ret %
        [-21.79, -23.12, -20.44, -19.23, -20.11, -21.86],   # Max DD % (higher=better)
        [42.58,  42.93,  57.51,  57.50,  57.51,  57.52],    # DirAcc %
    ]
    col_fmts   = [".4f", ".3f", ".3f", ".1f", ".1f", ".2f", ".1f"]
    # suffix per column
    col_suffix = ["", "", "", "%", "%", "%", "%"]

    n_rows = len(row_names)
    n_cols = len(col_names)

    # ── coordinate layout ──────────────────────────────────────────────────
    STRIPE_W = 0.12    # left type stripe
    NAME_W   = 2.20    # model-name column
    COL_W    = 1.54    # each metric column   (7 × 1.54 = 10.78)
    TOTAL_X  = STRIPE_W + NAME_W + n_cols * COL_W    # ≈ 13.10

    HDR_H = 1.0    # header row
    ROW_H = 1.0    # each data row
    TOTAL_Y = HDR_H + n_rows * ROW_H   # 7.0

    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.set_xlim(0, TOTAL_X)
    ax.set_ylim(0, TOTAL_Y)
    ax.axis("off")

    # ── helpers ────────────────────────────────────────────────────────────
    def blue_grad(t):
        r = 1.0 + (BLUE_RGB[0] - 1.0) * t
        g = 1.0 + (BLUE_RGB[1] - 1.0) * t
        b = 1.0 + (BLUE_RGB[2] - 1.0) * t
        return (r, g, b, 1.0)

    def text_color(rgba):
        lum = 0.2126*rgba[0] + 0.7152*rgba[1] + 0.0722*rgba[2]
        return "white" if lum < 0.50 else DARK

    def col_norm(vals):
        lo, hi = min(vals), max(vals)
        if hi == lo: return [0.5]*len(vals)
        return [(v - lo)/(hi - lo) for v in vals]

    def add_rect(x, y, w, h, fc, ec="white", lw=0.8):
        ax.add_patch(Rectangle((x, y), w, h,
                               facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2))

    def cell_text(x, y, w, h, txt, fs=12, fc=DARK, fw="normal"):
        ax.text(x + w/2, y + h/2, txt,
                ha="center", va="center", fontsize=fs,
                color=fc, fontweight=fw, zorder=3, clip_on=False)

    # ── header row ─────────────────────────────────────────────────────────
    y_hdr = n_rows * ROW_H
    add_rect(0, y_hdr, TOTAL_X, HDR_H, BLUE, ec=BLUE)
    cell_text(STRIPE_W, y_hdr, NAME_W, HDR_H, "Model",
              fs=13, fc="white", fw="bold")
    for j, cname in enumerate(col_names):
        cx = STRIPE_W + NAME_W + j * COL_W
        cell_text(cx, y_hdr, COL_W, HDR_H, cname,
                  fs=12, fc="white", fw="bold")

    # ── data rows ──────────────────────────────────────────────────────────
    for i, (rname, rstripe) in enumerate(zip(row_names, row_stripes)):
        # rows drawn top-to-bottom → row 0 = topmost → y = (n_rows-1)*ROW_H
        y_row = (n_rows - 1 - i) * ROW_H

        # alternating row background
        row_bg = "#F7F9FC" if i % 2 == 0 else "white"
        add_rect(0, y_row, TOTAL_X, ROW_H, row_bg, ec="none")

        # type stripe
        add_rect(0, y_row, STRIPE_W, ROW_H, rstripe, ec="none")

        # model name
        cell_text(STRIPE_W, y_row, NAME_W, ROW_H, rname,
                  fs=13, fc=DARK, fw="bold")

    # ── metric cells ───────────────────────────────────────────────────────
    for j, (cname, cvals, cfmt, csuf) in enumerate(
            zip(col_names, col_vals, col_fmts, col_suffix)):

        norms = col_norm(cvals)
        best_idx = int(np.argmax(cvals))   # highest = best for all cols

        for i, (v, t) in enumerate(zip(cvals, norms)):
            y_row = (n_rows - 1 - i) * ROW_H
            cx    = STRIPE_W + NAME_W + j * COL_W

            bg = blue_grad(t)
            add_rect(cx, y_row, COL_W, ROW_H, bg)

            # value string
            val_str = format(v, cfmt) + csuf
            tc = text_color(bg)
            fs_cell = 10 if i != best_idx else 10
            fw_cell = "bold" if i == best_idx else "normal"
            cell_text(cx, y_row, COL_W, ROW_H, val_str,
                      fs=fs_cell, fc=tc, fw=fw_cell)

    # ── white grid lines ────────────────────────────────────────────────────
    # horizontal (between rows)
    for r in range(n_rows + 1):
        y_line = r * ROW_H
        ax.plot([0, TOTAL_X], [y_line, y_line],
                color="white", lw=0.9, zorder=4)
    # vertical (between metric columns, and name/metric boundary)
    for j in range(n_cols + 1):
        x_line = STRIPE_W + NAME_W + j * COL_W
        ax.plot([x_line, x_line], [0, TOTAL_Y],
                color="white", lw=0.9, zorder=4)

    # ── legend for stripe colours ───────────────────────────────────────────
    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor=AMBER,  label="DNN (no graph)"),
        Patch(facecolor=BLUE,   label="GAT topology family"),
        Patch(facecolor=PURPLE, label="GAT-neutral family"),
    ]
    ax.legend(handles=legend_handles,
              loc="upper center", bbox_to_anchor=(0.5, -0.04),
              ncol=3, frameon=False, fontsize=12,
              handlelength=1.2, handletextpad=0.4)

    fig.tight_layout(pad=0.2)
    fig.savefig(OUT_DIR + "/ch4_fig_topology_heatmap.png",
                dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("✓  ch4_fig_topology_heatmap.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig H – §4.1 Overview heatmap: 3 windows × 6 categories × 4 metrics  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_overview_heatmap():
    """
    Condensed summary table for §4.1.
    Rows: 18 (3 windows × 6 model categories), grouped by window.
    Cols: Daily IC | ICIR | Sharpe | Ann. Ret.(%)
    Gradient: white→thesisBlue by GLOBAL column rank (rank 0..17).
    Best value per column globally shown in bold.
    Left stripe: Amber=Short, Forest=Medium, Blue=Long.
    """
    from matplotlib.patches import Rectangle

    BLUE_RGB = np.array([43/255, 108/255, 176/255])

    windows    = ["Short", "Medium", "Long"]
    win_colors = [AMBER, FOREST, BLUE]

    cats = ["Linear", "XGBoost", "LSTM", "DNN", "GAT family", "GAT-neutral"]

    # Data sourced from results_portfolio_metrics.tex
    raw = {
        ("Short",  "Linear"):      [0.0036, 0.037, -0.423, -16.92],
        ("Short",  "LSTM"):        [0.0057, 0.048, -0.223,  -9.28],
        ("Short",  "XGBoost"):     [0.0261, 0.209,  0.010,   0.44],
        ("Short",  "DNN"):         [0.0396, 0.408, -0.098,  -4.06],
        ("Short",  "GAT family"):  [0.0275, 0.247, -0.036,  -1.54],
        ("Short",  "GAT-neutral"): [0.0278, 0.253, -0.084,  -3.68],
        ("Medium", "Linear"):      [0.0253, 0.278,  0.561,  18.14],
        ("Medium", "LSTM"):        [0.0359, 0.345,  0.776,  26.53],
        ("Medium", "XGBoost"):     [0.0485, 0.430,  0.938,  32.10],
        ("Medium", "DNN"):         [0.0453, 0.581,  0.980,  31.88],
        ("Medium", "GAT family"):  [0.0454, 0.478,  0.842,  29.21],
        ("Medium", "GAT-neutral"): [0.0548, 0.583,  0.873,  29.86],
        ("Long",   "Linear"):      [0.0214, 0.235,  0.884,  22.32],
        ("Long",   "LSTM"):        [0.0418, 0.479,  1.336,  33.45],
        ("Long",   "XGBoost"):     [0.0408, 0.459,  1.714,  43.37],
        ("Long",   "DNN"):         [0.0535, 0.726,  1.564,  35.35],
        ("Long",   "GAT family"):  [0.0502, 0.569,  1.704,  37.87],
        ("Long",   "GAT-neutral"): [0.0587, 0.760,  1.826,  40.36],
    }

    col_names  = ["Daily IC", "ICIR", "Sharpe", "Ann. Ret. (%)"]
    col_fmts   = [".4f", ".3f", ".3f", ".1f"]
    col_suffix = ["", "", "", "%"]
    n_cols     = len(col_names)

    # Flatten 18 rows in window-then-category order
    flat_keys = [(w, c) for w in windows for c in cats]
    flat_vals = [raw[k] for k in flat_keys]
    n_data    = len(flat_vals)   # 18

    # Global column rank normalisation (0=worst → 1=best)
    norm_mat     = np.zeros((n_data, n_cols))
    best_per_col = []
    for col in range(n_cols):
        col_arr = [flat_vals[r][col] for r in range(n_data)]
        order   = np.argsort(col_arr)          # ascending rank
        ranks   = np.empty(n_data)
        for rank_pos, orig_idx in enumerate(order):
            ranks[orig_idx] = rank_pos
        norm_mat[:, col] = ranks / (n_data - 1)
        best_per_col.append(int(np.argmax(col_arr)))

    # ── layout constants ─────────────────────────────────────────────────────
    STRIPE_W = 0.12   # left window-colour stripe
    NAME_W   = 1.90   # model-category name column
    COL_W    = 1.60   # each metric column  (4 × 1.60 = 6.40)
    TOTAL_X  = STRIPE_W + NAME_W + n_cols * COL_W   # = 8.42

    TOP_H  = 0.80    # column-name header row
    GRP_H  = 0.55    # window-group header row
    ROW_H  = 0.78    # each data row
    # Total Y: 1 top-header + 3 × (1 group-header + 6 data rows)
    TOTAL_Y = TOP_H + 3 * (GRP_H + 6 * ROW_H)   # = 0.80 + 3×5.23 = 16.49

    fig, ax = plt.subplots(figsize=(8.5, 8.0))
    ax.set_xlim(0, TOTAL_X)
    ax.set_ylim(0, TOTAL_Y)
    ax.axis("off")

    # ── colour helpers ───────────────────────────────────────────────────────
    def blue_grad(t):
        return (1.0 + (BLUE_RGB[0]-1.0)*t,
                1.0 + (BLUE_RGB[1]-1.0)*t,
                1.0 + (BLUE_RGB[2]-1.0)*t, 1.0)

    def text_color(rgba):
        lum = 0.2126*rgba[0] + 0.7152*rgba[1] + 0.0722*rgba[2]
        return "white" if lum < 0.50 else DARK

    def add_rect(x, y, w, h, fc, ec="white", lw=0.6):
        ax.add_patch(Rectangle((x, y), w, h,
                                facecolor=fc, edgecolor=ec,
                                linewidth=lw, zorder=2))

    def cell_text(x, y, w, h, txt, fs=11, fc=DARK, fw="normal"):
        ax.text(x + w/2, y + h/2, txt,
                ha="center", va="center", fontsize=fs,
                color=fc, fontweight=fw, zorder=3, clip_on=False)

    # ── Top column-name header ───────────────────────────────────────────────
    y_top = TOTAL_Y - TOP_H
    add_rect(0, y_top, TOTAL_X, TOP_H, DARK, ec=DARK)
    cell_text(0, y_top, STRIPE_W + NAME_W, TOP_H,
              "Model Category", fs=13, fc="white", fw="bold")
    for j, cname in enumerate(col_names):
        cx = STRIPE_W + NAME_W + j * COL_W
        cell_text(cx, y_top, COL_W, TOP_H, cname,
                  fs=12, fc="white", fw="bold")

    # ── Three window groups (top to bottom: Short → Medium → Long) ──────────
    for wi, (wname, wcolor) in enumerate(zip(windows, win_colors)):
        block_h = GRP_H + 6 * ROW_H
        y_grp   = TOTAL_Y - TOP_H - wi * block_h - GRP_H

        # Window group header
        add_rect(0, y_grp, TOTAL_X, GRP_H, wcolor, ec=wcolor)
        ax.text(TOTAL_X / 2, y_grp + GRP_H / 2,
                f"{wname}  Window",
                ha="center", va="center", fontsize=13,
                color="white", fontweight="bold", zorder=3)

        # Six model-category rows
        for ci, cat in enumerate(cats):
            row_global = wi * 6 + ci
            y_row = y_grp - (ci + 1) * ROW_H

            row_bg = "#F7F9FC" if ci % 2 == 0 else "white"
            add_rect(0, y_row, TOTAL_X, ROW_H, row_bg, ec="none")
            add_rect(0, y_row, STRIPE_W, ROW_H, wcolor, ec="none")
            ax.text(STRIPE_W + 0.12, y_row + ROW_H/2, cat,
                    ha="left", va="center", fontsize=11,
                    color=DARK, fontweight="normal", zorder=3)

            for col in range(n_cols):
                t   = norm_mat[row_global, col]
                bg  = blue_grad(t)
                tc  = text_color(bg)
                cx  = STRIPE_W + NAME_W + col * COL_W
                add_rect(cx, y_row, COL_W, ROW_H, bg)
                val_str = format(flat_vals[row_global][col], col_fmts[col]) \
                          + col_suffix[col]
                is_best = (row_global == best_per_col[col])
                cell_text(cx, y_row, COL_W, ROW_H, val_str,
                          fs=11, fc=tc,
                          fw="bold" if is_best else "normal")

    # ── Horizontal dividers between groups ───────────────────────────────────
    for wi in range(3):
        block_h = GRP_H + 6 * ROW_H
        y_line  = TOTAL_Y - TOP_H - wi * block_h
        ax.plot([0, TOTAL_X], [y_line, y_line],
                color="white", lw=1.4, zorder=5)

    # ── Vertical grid between metric columns ─────────────────────────────────
    for j in range(n_cols + 1):
        xv = STRIPE_W + NAME_W + j * COL_W
        ax.plot([xv, xv], [0, TOTAL_Y],
                color="white", lw=0.8, zorder=4)

    fig.savefig(OUT_DIR + "/ch4_fig_overview_heatmap.png",
                dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("✓  ch4_fig_overview_heatmap.png")


# ── run all ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fig_baseline_comparison()
    fig_neutralization()
    fig_window_effect()
    fig_portfolio_metrics_overview()
    print("\nAll 4 Chapter-4 figures generated successfully.")
