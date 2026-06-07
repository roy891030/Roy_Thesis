#!/usr/bin/env python3
"""
Chapter-4 comparison figures – thesis colour palette only.
Colours used:
  Short window / XGBoost / Baseline : AMBER   (#C98C1E)
  Medium window                     : FOREST  (#2D7A4F)   ← "綠色為中期"
  Long window / GAT family          : BLUE    (#2B6CB0)
  Train IC / primary signal         : BLUE    (#2B6CB0)
  Test IC  / warning                : CRIMSON (#9B2235)
  DNN                               : CRIMSON (#9B2235)
  GAT-neutral                       : PURPLE  (#6B46C1)
  Overview – Linear (weakest)       : MIDGRAY (#82919F)
  Overview – LSTM                   : TEAL    (#4A9D8F)   ← never used as window colour
"""

import json, os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ── strict thesis palette ────────────────────────────────────────────────────
BLUE    = "#2B6CB0"
AMBER   = "#C98C1E"
CRIMSON = "#9B2235"
FOREST  = "#2D7A4F"   # medium-window colour ("綠色")
DARK    = "#2D3748"
LIGHT   = "#EDF2F7"
PURPLE  = "#6B46C1"
TEAL    = "#4A9D8F"   # overview-only, LSTM line
MIDGRAY = "#82919F"   # overview-only, Linear line

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
WIN_LABEL = {"short": "Short", "medium": "Medium", "long": "Long"}

# ── global rcParams ──────────────────────────────────────────────────────────
RC = {
    "font.family"      : "sans-serif",
    "font.size"        : 14,
    "axes.titlesize"   : 15,
    "axes.labelsize"   : 14,
    "xtick.labelsize"  : 13,
    "ytick.labelsize"  : 13,
    "legend.fontsize"  : 13,
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

def ax_style(ax):
    ax.yaxis.grid(True, linestyle="--", linewidth=0.7, color="#D8E2EE", alpha=0.9)
    ax.set_axisbelow(True)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="both", length=3, color=MIDGRAY)

def bar_label(ax, bar, v, fmt, offset, is_neg_ok=False):
    """Place a value label above (positive) or below (negative) a bar.
    clip_on=False prevents axis-boundary clipping."""
    if v >= 0:
        ax.text(bar.get_x() + bar.get_width() / 2,
                v + offset, format(v, fmt),
                ha="center", va="bottom", fontsize=9.5,
                color=DARK, clip_on=False)
    else:
        ax.text(bar.get_x() + bar.get_width() / 2,
                v - offset * 0.5, format(v, fmt),
                ha="center", va="top", fontsize=9.5,
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


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig A – Baseline model comparison                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_baseline_comparison():
    models  = ["Linear", "XGBoost", "LSTM", "DNN"]
    win_clr = {"short": AMBER, "medium": FOREST, "long": BLUE}
    bw, gap = 0.22, 0.06
    x       = np.arange(len(models))

    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
        fig.subplots_adjust(wspace=0.32, top=0.88)

        for col, (metric, ylabel, title, fmt) in enumerate([
            ("daily_ic", "Daily IC",     "Daily IC by Training Window",     ".3f"),
            ("sharpe",   "Sharpe Ratio", "Sharpe Ratio by Training Window", ".2f"),
        ]):
            ax = axes[col]
            offsets  = np.array([-1, 0, 1]) * (bw + gap / 2)
            all_vals = []

            for w, off in zip(WINDOWS, offsets):
                vals = [D[w][m][metric] for m in models]
                all_vals.extend(vals)
                bars = ax.bar(x + off, vals, width=bw,
                              color=win_clr[w], label=WIN_LABEL[w],
                              edgecolor="white", linewidth=0.5, zorder=3)
                offset_amt = 0.0003 if metric == "daily_ic" else 0.012
                for bar, v in zip(bars, vals):
                    bar_label(ax, bar, v, fmt, offset_amt)

            ax.set_xticks(x)
            ax.set_xticklabels(models, fontsize=13)
            ax.set_ylabel(ylabel, color=DARK, fontsize=14)
            ax.set_title(title, color=DARK, fontsize=15, pad=8)
            ax_style(ax)
            set_ylim_with_room(ax, all_vals, top_frac=0.26, bot_frac=0.20)

            if metric == "sharpe":
                ax.axhline(0, color=MIDGRAY, linewidth=0.8, linestyle="--", zorder=2)

        handles = [Patch(facecolor=win_clr[w], label=WIN_LABEL[w]) for w in WINDOWS]
        fig.legend(handles=handles, loc="upper center", ncol=3,
                   bbox_to_anchor=(0.5, 1.00), frameon=False,
                   fontsize=13, handlelength=1.4, handletextpad=0.5)

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

    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=(7.5, 6.2))   # taller figure → more headroom

        b1 = ax.bar(x - bw/2, train, width=bw, color=BLUE,
                    label="Train IC", edgecolor="white", linewidth=0.5, zorder=3)
        b2 = ax.bar(x + bw/2, test,  width=bw, color=CRIMSON,
                    label="Test IC",  edgecolor="white", linewidth=0.5, zorder=3)

        # ── Train IC: value inside bar (white bold) ──
        for bar, v in zip(b1, train):
            cx = bar.get_x() + bar.get_width() / 2
            cy = v * 0.50           # mid-point of bar
            ax.text(cx, cy, f"{v:.4f}",
                    ha="center", va="center", fontsize=11,
                    color="white", fontweight="bold", clip_on=False)

        # ── Test IC: value above bar (dark small text) ──
        for bar, v in zip(b2, test):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    v + 0.012, f"{v:.4f}",
                    ha="center", va="bottom", fontsize=10,
                    color=DARK, clip_on=False)

        # ── ratio annotation: centred between bars, far above ──
        # Use group centre (xi) so text is fully inside the axes for every window
        for xi, (tr, r) in enumerate(zip(train, ratio)):
            ax.text(xi,                 # group centre, not train-bar centre
                    tr + 0.150,         # much higher than +0.07 to avoid any overlap
                    f"×{r:.1f}",
                    ha="center", va="bottom", fontsize=14,
                    fontweight="bold", color=DARK, clip_on=False)

        ax.set_xticks(x)
        ax.set_xticklabels([WIN_LABEL[w] for w in WINDOWS], fontsize=13)
        ax.set_ylabel("Information Coefficient (IC)", color=DARK, fontsize=14)
        ax.set_title("XGBoost: Train IC vs. Test IC by Window",
                     color=DARK, fontsize=15, pad=8)
        ax_style(ax)
        ax.legend(frameon=False, fontsize=13, handlelength=1.4, loc="upper left")
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
        fig, axes = plt.subplots(1, 3, figsize=(14, 5.5))
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
            ax.set_xticklabels(models, fontsize=11.5, rotation=15, ha="right")
            ax.set_ylabel(ylabel, color=DARK, fontsize=14)
            ax.set_title(title, color=DARK, fontsize=15, pad=8)
            ax_style(ax)
            set_ylim_with_room(ax, all_vals)

        handles = [Patch(facecolor=win_clr[w], label=WIN_LABEL[w])
                   for w in ["medium", "long"]]
        fig.legend(handles=handles, loc="upper center", ncol=2,
                   bbox_to_anchor=(0.5, 1.00), frameon=False,
                   fontsize=13, handlelength=1.4)

        fig.savefig(os.path.join(OUT_DIR, "ch4_fig_topology_comparison.png"))
        plt.close(fig)
        print("✓  ch4_fig_topology_comparison.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig D – Neutralization mechanism comparison                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_neutralization():
    models  = ["GAT-industry", "GAT-TwoGraph", "GAT-IndNeutral", "GAT-full"]
    win_clr = {"medium": AMBER, "long": BLUE}
    bw, gap = 0.30, 0.08
    x       = np.arange(len(models))
    metrics = [
        ("icir",   "ICIR",         "ICIR by Neutralization",         ".3f"),
        ("sharpe", "Sharpe Ratio", "Sharpe Ratio by Neutralization", ".3f"),
    ]

    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
        fig.subplots_adjust(wspace=0.32, top=0.88)

        for col, (metric, ylabel, title, fmt) in enumerate(metrics):
            ax       = axes[col]
            offsets  = [-bw/2 - gap/2, bw/2 + gap/2]
            all_vals = []

            for w, off in zip(["medium", "long"], offsets):
                vals = [D[w][m][metric] for m in models]
                all_vals.extend(vals)
                bars = ax.bar(x + off, vals, width=bw,
                              color=win_clr[w], label=WIN_LABEL[w],
                              edgecolor="white", linewidth=0.5, zorder=3)
                for bar, v in zip(bars, vals):
                    bar_label(ax, bar, v, fmt, 0.010)

            ax.set_xticks(x)
            ax.set_xticklabels(models, fontsize=11.5, rotation=12, ha="right")
            ax.set_ylabel(ylabel, color=DARK, fontsize=14)
            ax.set_title(title, color=DARK, fontsize=15, pad=8)
            ax_style(ax)
            set_ylim_with_room(ax, all_vals)

        handles = [Patch(facecolor=win_clr[w], label=WIN_LABEL[w])
                   for w in ["medium", "long"]]
        fig.legend(handles=handles, loc="upper center", ncol=2,
                   bbox_to_anchor=(0.5, 1.00), frameon=False,
                   fontsize=13, handlelength=1.4)

        fig.savefig(os.path.join(OUT_DIR, "ch4_fig_neutralization.png"))
        plt.close(fig)
        print("✓  ch4_fig_neutralization.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig E – Window-length effect across model groups (line chart)         ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_window_effect():
    def avg(mlist, metric, w):
        return np.mean([D[w][m][metric] for m in mlist])

    baselines = ["Linear", "XGBoost", "LSTM"]
    gat_grp   = ["GAT-industry", "GAT-universe", "GAT-TwoGraph"]
    neut_grp  = ["GAT-IndNeutral", "GAT-full"]
    xs        = [0, 1, 2]
    xlabels   = ["Short", "Medium", "Long"]

    series = {
        "Baseline avg\n(excl. DNN)" : {
            "sharpe"  : [avg(baselines, "sharpe",   w) for w in WINDOWS],
            "daily_ic": [avg(baselines, "daily_ic", w) for w in WINDOWS],
            "style"   : dict(color=AMBER,  linestyle="--", linewidth=2.2,
                             marker="o", markersize=7),
        },
        "DNN" : {
            "sharpe"  : [D[w]["DNN"]["sharpe"]   for w in WINDOWS],
            "daily_ic": [D[w]["DNN"]["daily_ic"] for w in WINDOWS],
            "style"   : dict(color=CRIMSON, linestyle="-", linewidth=2.2,
                             marker="s", markersize=7),
        },
        "GAT family avg" : {
            "sharpe"  : [avg(gat_grp, "sharpe",   w) for w in WINDOWS],
            "daily_ic": [avg(gat_grp, "daily_ic", w) for w in WINDOWS],
            "style"   : dict(color=BLUE,  linestyle="-", linewidth=2.2,
                             marker="^", markersize=7),
        },
        "GAT-neutral avg" : {
            "sharpe"  : [avg(neut_grp, "sharpe",   w) for w in WINDOWS],
            "daily_ic": [avg(neut_grp, "daily_ic", w) for w in WINDOWS],
            "style"   : dict(color=PURPLE, linestyle="-", linewidth=2.2,
                             marker="D", markersize=7),
        },
    }

    with plt.rc_context(RC):
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        fig.subplots_adjust(wspace=0.30)

        for col, (metric, ylabel, title) in enumerate([
            ("sharpe",   "Sharpe Ratio", "Sharpe Ratio across Training Windows"),
            ("daily_ic", "Daily IC",     "Daily IC across Training Windows"),
        ]):
            ax = axes[col]
            for label, info in series.items():
                ax.plot(xs, info[metric], label=label, **info["style"],
                        zorder=4, clip_on=False)
            if metric == "sharpe":
                ax.axhline(0, color=MIDGRAY, linewidth=0.9, linestyle=":", zorder=1)
            ax.set_xticks(xs)
            ax.set_xticklabels(xlabels, fontsize=13)
            ax.set_ylabel(ylabel, color=DARK, fontsize=14)
            ax.set_title(title, color=DARK, fontsize=15, pad=8)
            ax_style(ax)

        handles = [
            Line2D([0],[0], color=AMBER,  linestyle="--", linewidth=2, marker="o", markersize=7),
            Line2D([0],[0], color=CRIMSON, linestyle="-", linewidth=2, marker="s", markersize=7),
            Line2D([0],[0], color=BLUE,   linestyle="-", linewidth=2, marker="^", markersize=7),
            Line2D([0],[0], color=PURPLE, linestyle="-", linewidth=2, marker="D", markersize=7),
        ]
        labels = ["Baseline avg (excl. DNN)", "DNN",
                  "GAT family avg", "GAT-neutral avg"]
        fig.legend(handles=handles, labels=labels,
                   loc="upper center", ncol=4,
                   bbox_to_anchor=(0.5, 1.02), frameon=False,
                   fontsize=12.5, handlelength=1.8, handletextpad=0.6)

        fig.savefig(os.path.join(OUT_DIR, "ch4_fig_window_effect.png"))
        plt.close(fig)
        print("✓  ch4_fig_window_effect.png")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig F – Table 14 visualisation: all model categories × all windows    ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def fig_portfolio_metrics_overview():
    """
    Line chart: x = Short/Medium/Long, one line per model category.
    2×2 panels: Daily IC | ICIR | Sharpe | Annual Return.

    Colour rules (no overlap with window colours Amber/Forest/Blue):
      Linear    → MIDGRAY  (#82919F)  thin dashed-dot
      LSTM      → TEAL     (#4A9D8F)  dashed   ← NOT Forest (Forest=Medium window)
      XGBoost   → AMBER    (#C98C1E)  dashed   (warm = overfit risk)
      DNN       → CRIMSON  (#9B2235)  solid
      GAT fam.  → BLUE     (#2B6CB0)  solid
      GAT-neut. → PURPLE   (#6B46C1)  solid thick
    """
    cats = {
        "Linear": dict(
            daily_ic   = [0.0036, 0.0253, 0.0214],
            icir       = [0.037,  0.278,  0.235],
            sharpe     = [-0.423, 0.561,  0.884],
            annual_ret = [-16.92, 18.14,  22.32],
            style = dict(color=MIDGRAY, ls=(0,(3,1,1,1)), lw=1.8, marker="o", ms=6),
        ),
        "LSTM": dict(
            daily_ic   = [0.0057, 0.0359, 0.0418],
            icir       = [0.048,  0.345,  0.479],
            sharpe     = [-0.223, 0.776,  1.336],
            annual_ret = [-9.28,  26.53,  33.45],
            style = dict(color=TEAL,    ls="--",          lw=1.8, marker="v", ms=6),
        ),
        "XGBoost": dict(
            daily_ic   = [0.0261, 0.0485, 0.0408],
            icir       = [0.209,  0.430,  0.459],
            sharpe     = [0.010,  0.938,  1.714],
            annual_ret = [0.44,   32.10,  43.37],
            style = dict(color=AMBER,   ls="--",          lw=1.8, marker="s", ms=6),
        ),
        "DNN": dict(
            daily_ic   = [0.0396, 0.0453, 0.0535],
            icir       = [0.408,  0.581,  0.726],
            sharpe     = [-0.098, 0.980,  1.564],
            annual_ret = [-4.06,  31.88,  35.35],
            style = dict(color=CRIMSON, ls="-",           lw=2.2, marker="D", ms=7),
        ),
        "GAT family": dict(
            daily_ic   = [0.0275, 0.0454, 0.0502],
            icir       = [0.247,  0.478,  0.569],
            sharpe     = [-0.036, 0.842,  1.704],
            annual_ret = [-1.54,  29.21,  37.87],
            style = dict(color=BLUE,    ls="-",           lw=2.2, marker="^", ms=8),
        ),
        "GAT-neutral": dict(
            daily_ic   = [0.0278, 0.0548, 0.0587],
            icir       = [0.253,  0.583,  0.760],
            sharpe     = [-0.084, 0.873,  1.826],
            annual_ret = [-3.68,  29.86,  40.36],
            style = dict(color=PURPLE,  ls="-",           lw=2.8, marker="*", ms=9),
        ),
    }

    xs      = [0, 1, 2]
    xlabels = ["Short", "Medium", "Long"]
    panels  = [
        ("daily_ic",   "Daily IC",        "Daily IC by Model Category"),
        ("icir",       "ICIR",            "ICIR by Model Category"),
        ("sharpe",     "Sharpe Ratio",    "Sharpe Ratio by Model Category"),
        ("annual_ret", "Annual Return (%)", "Annual Return by Model Category"),
    ]

    with plt.rc_context(RC):
        fig, axes = plt.subplots(2, 2, figsize=(14, 9))
        fig.subplots_adjust(hspace=0.38, wspace=0.28)

        for idx, (metric, ylabel, title) in enumerate(panels):
            ax = axes[idx // 2][idx % 2]
            for cat_name, info in cats.items():
                ax.plot(xs, info[metric], label=cat_name, **info["style"],
                        zorder=4, clip_on=False)

            if metric in ("sharpe", "annual_ret"):
                ax.axhline(0, color=MIDGRAY, lw=0.9, ls=":", zorder=1)

            ax.set_xticks(xs)
            ax.set_xticklabels(xlabels, fontsize=13)
            ax.set_ylabel(ylabel, color=DARK, fontsize=13)
            ax.set_title(title, color=DARK, fontsize=14, pad=7)
            ax_style(ax)

            if metric == "annual_ret":
                ax.yaxis.set_major_formatter(
                    mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))

        # shared legend below the 2×2 grid
        handles = []
        for c, info in cats.items():
            h = Line2D([0],[0], label=c, **info["style"])
            if h.get_marker() == "*":
                h.set_markersize(8)
            handles.append(h)

        fig.legend(handles=handles,
                   loc="lower center", ncol=6,
                   bbox_to_anchor=(0.5, -0.04),
                   frameon=False, fontsize=12.5,
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

    fig, ax = plt.subplots(figsize=(13, 4.8))
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

    def cell_text(x, y, w, h, txt, fs=10, fc=DARK, fw="normal"):
        ax.text(x + w/2, y + h/2, txt,
                ha="center", va="center", fontsize=fs,
                color=fc, fontweight=fw, zorder=3, clip_on=False)

    # ── header row (y = n_rows to n_rows+HDR_H) ───────────────────────────
    y_hdr = n_rows * ROW_H
    # header background
    add_rect(0, y_hdr, TOTAL_X, HDR_H, BLUE, ec=BLUE)
    # "Model" header
    cell_text(STRIPE_W, y_hdr, NAME_W, HDR_H, "Model",
              fs=11, fc="white", fw="bold")
    # metric column headers
    for j, cname in enumerate(col_names):
        cx = STRIPE_W + NAME_W + j * COL_W
        cell_text(cx, y_hdr, COL_W, HDR_H, cname,
                  fs=10.5, fc="white", fw="bold")

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
                  fs=10.5, fc=DARK, fw="bold")

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
              ncol=3, frameon=False, fontsize=11,
              handlelength=1.2, handletextpad=0.4)

    fig.tight_layout(pad=0.2)
    fig.savefig(OUT_DIR + "/ch4_fig_topology_heatmap.png",
                dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("✓  ch4_fig_topology_heatmap.png")


# ── run all ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fig_baseline_comparison()
    fig_xgboost_gap()
    fig_topology_comparison()
    fig_neutralization()
    fig_window_effect()
    fig_topology_heatmap()
    fig_portfolio_metrics_overview()
    print("\nAll 7 Chapter-4 figures generated successfully.")
