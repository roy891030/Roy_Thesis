#!/usr/bin/env python3
"""Generate dynamic-vs-static comparison dashboard."""

import json
import glob
import os
from pathlib import Path

BASE = Path("/Users/luoyi/Desktop/Roy_Thesis")

MODEL_LABELS = {
    "mlp": "MLP",
    "gat_industry": "GAT-Industry",
    "gat_universe": "GAT-Universe",
    "gat_two_graph_no_neutral": "GAT-TwoGraph",
    "dmfm_ind_neutral": "DMFM-IndNeut",
    "dmfm_full": "DMFM-Full",
    "baseline_linear": "Linear",
    "baseline_xgboost": "XGBoost",
    "baseline_lstm": "LSTM",
}

WINDOWS = ["short", "medium", "long"]
WINDOW_LABELS = {"short": "Short (5d)", "medium": "Medium (20d)", "long": "Long (60d)"}

SHARED_MODELS = ["mlp", "gat_industry", "gat_universe", "gat_two_graph_no_neutral", "dmfm_ind_neutral", "dmfm_full"]
BASELINE_MODELS = ["baseline_linear", "baseline_xgboost", "baseline_lstm"]


def collect_metrics(base_dir: Path, mode_key: str) -> dict:
    data = {}
    for p in base_dir.rglob("metrics.json"):
        parts = list(p.parts)
        try:
            idx = parts.index(mode_key)
            window = parts[idx + 1]
            model = parts[idx + 2]
        except (ValueError, IndexError):
            continue
        with open(p) as f:
            d = json.load(f)
        data[(window, model)] = d
    return data


def collect_portfolio(base_dir: Path, mode_key: str) -> dict:
    data = {}
    for p in base_dir.rglob("portfolio.json"):
        parts = list(p.parts)
        try:
            idx = parts.index(mode_key)
            window = parts[idx + 1]
            model = parts[idx + 2]
        except (ValueError, IndexError):
            continue
        with open(p) as f:
            d = json.load(f)
        data[(window, model)] = d
    return data


dyn_metrics = collect_metrics(BASE / "runs_dynamic_only_6_8", "dynamic")
sta_metrics = collect_metrics(BASE / "runs_gpu_static_to_20250601", "static")
dyn_port = collect_portfolio(BASE / "runs_dynamic_only_6_8", "dynamic")
sta_port = collect_portfolio(BASE / "runs_gpu_static_to_20250601", "static")

def fmt(v, decimals=4, pct=False):
    if v is None:
        return "—"
    if pct:
        return f"{v*100:.2f}%"
    return f"{v:.{decimals}f}"

def delta_color(d, higher_is_better=True):
    if d is None:
        return ""
    if higher_is_better:
        if d > 0.001:
            return "color:#16a34a;font-weight:600"
        elif d < -0.001:
            return "color:#dc2626;font-weight:600"
    else:
        if d < -0.001:
            return "color:#16a34a;font-weight:600"
        elif d > 0.001:
            return "color:#dc2626;font-weight:600"
    return "color:#6b7280"

def delta_str(d, pct=False):
    if d is None:
        return "—"
    sign = "+" if d > 0 else ""
    if pct:
        return f"{sign}{d*100:.2f}%"
    return f"{sign}{d:.4f}"


# --- Build HTML ---

def build_metrics_section():
    """Full test-set metrics table for all shared models × 3 windows."""
    metric_cols = [
        ("IC", "test_IC", True),
        ("ICIR", "test_ICIR", True),
        ("DirAcc", "test_DirAcc", True),
        ("Sharpe", "strategy_sharpe", True),
        ("CAGR", "strategy_cagr", True),
        ("MaxDD", "strategy_max_drawdown", False),
        ("MSE", "test_MSE", False),
    ]

    sections = []
    for window in WINDOWS:
        rows = []
        for model in SHARED_MODELS:
            sta = sta_metrics.get((window, model), {})
            dyn = dyn_metrics.get((window, model), {})
            sta_p = sta_port.get((window, model), {})
            dyn_p = dyn_port.get((window, model), {})

            def get_val(d, dp, key):
                if key.startswith("strategy_"):
                    k = key[len("strategy_"):]
                    return dp.get("strategy", {}).get(k)
                else:
                    split = "test"
                    metric = key[len("test_"):]
                    return d.get(split, {}).get(metric)

            row_cells = [f"<td style='font-weight:600'>{MODEL_LABELS.get(model, model)}</td>"]
            for label, key, higher_better in metric_cols:
                sv = get_val(sta, sta_p, key)
                dv = get_val(dyn, dyn_p, key)
                d = (dv - sv) if sv is not None and dv is not None else None
                is_pct = key in ("strategy_cagr", "strategy_max_drawdown", "test_DirAcc")

                s_str = fmt(sv, 4, is_pct)
                d_str = fmt(dv, 4, is_pct)
                delta = delta_str(d, is_pct)
                style = delta_color(d, higher_better)

                row_cells.append(
                    f"<td style='text-align:right'>{s_str}</td>"
                    f"<td style='text-align:right'>{d_str}</td>"
                    f"<td style='text-align:right;{style}'>{delta}</td>"
                )
            rows.append("<tr>" + "".join(row_cells) + "</tr>")

        # Baseline rows (static only)
        for model in BASELINE_MODELS:
            sta = sta_metrics.get((window, model), {})
            sta_p = sta_port.get((window, model), {})

            def get_val_sta(key):
                if key.startswith("strategy_"):
                    k = key[len("strategy_"):]
                    return sta_p.get("strategy", {}).get(k)
                else:
                    split = "test"
                    metric = key[len("test_"):]
                    return sta.get(split, {}).get(metric)

            row_cells = [f"<td style='font-weight:600;color:#6b7280'>{MODEL_LABELS.get(model, model)} (static only)</td>"]
            for label, key, higher_better in metric_cols:
                sv = get_val_sta(key)
                is_pct = key in ("strategy_cagr", "strategy_max_drawdown", "test_DirAcc")
                s_str = fmt(sv, 4, is_pct)
                row_cells.append(
                    f"<td style='text-align:right;color:#9ca3af'>{s_str}</td>"
                    f"<td colspan='2' style='text-align:center;color:#d1d5db'>—</td>"
                )
            rows.append("<tr style='background:#fafafa'>" + "".join(row_cells) + "</tr>")

        header_cols = "".join(
            f"<th colspan='3' style='border-left:2px solid #e5e7eb'>{label}</th>"
            for label, _, _ in metric_cols
        )
        subheader = "".join(
            "<th style='color:#6b7280;font-size:11px'>Static</th>"
            "<th style='color:#3b82f6;font-size:11px'>Dynamic</th>"
            "<th style='color:#8b5cf6;font-size:11px'>Δ</th>"
            for _ in metric_cols
        )

        sections.append(f"""
<div class="section">
  <h2>{WINDOW_LABELS[window]} Window — Test Set</h2>
  <div style="overflow-x:auto">
  <table>
    <thead>
      <tr>
        <th rowspan='2'>Model</th>
        {header_cols}
      </tr>
      <tr>{subheader}</tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  </div>
</div>
""")
    return "\n".join(sections)


def build_delta_heatmap_data():
    """Return JS data arrays for delta heatmaps."""
    metrics = [
        ("IC (Δ)", "test_IC", True),
        ("ICIR (Δ)", "test_ICIR", True),
        ("DirAcc (Δ)", "test_DirAcc", True),
        ("Sharpe (Δ)", "strategy_sharpe", True),
        ("CAGR (Δ)", "strategy_cagr", True),
        ("MaxDD (Δ)", "strategy_max_drawdown", False),
    ]

    all_data = {}
    for mkey, col, higher in metrics:
        grid = []
        for model in SHARED_MODELS:
            row = []
            for window in WINDOWS:
                sta = sta_metrics.get((window, model), {})
                dyn = dyn_metrics.get((window, model), {})
                sta_p = sta_port.get((window, model), {})
                dyn_p = dyn_port.get((window, model), {})
                if col.startswith("strategy_"):
                    k = col[len("strategy_"):]
                    sv = sta_p.get("strategy", {}).get(k)
                    dv = dyn_p.get("strategy", {}).get(k)
                else:
                    metric = col[len("test_"):]
                    sv = sta.get("test", {}).get(metric)
                    dv = dyn.get("test", {}).get(metric)
                d = round(dv - sv, 5) if sv is not None and dv is not None else None
                row.append(d)
            grid.append(row)
        all_data[mkey] = {"grid": grid, "higher_better": higher}

    return json.dumps(all_data)


def build_portfolio_chart_data():
    """Return chart data for portfolio comparison bars."""
    metrics = ["sharpe", "cagr", "max_drawdown"]
    out = {}
    for window in WINDOWS:
        wdata = {"models": [], "static": {m: [] for m in metrics}, "dynamic": {m: [] for m in metrics}}
        for model in SHARED_MODELS:
            wdata["models"].append(MODEL_LABELS.get(model, model))
            sp = sta_port.get((window, model), {}).get("strategy", {})
            dp = dyn_port.get((window, model), {}).get("strategy", {})
            for m in metrics:
                wdata["static"][m].append(round(sp.get(m, 0) or 0, 4))
                wdata["dynamic"][m].append(round(dp.get(m, 0) or 0, 4))
        out[window] = wdata
    return json.dumps(out)


def build_ic_chart_data():
    """IC/ICIR per model per window for both modes."""
    out = {}
    for window in WINDOWS:
        wdata = {"models": [], "static_ic": [], "dynamic_ic": [], "static_icir": [], "dynamic_icir": []}
        for model in SHARED_MODELS:
            wdata["models"].append(MODEL_LABELS.get(model, model))
            sd = sta_metrics.get((window, model), {}).get("test", {})
            dd = dyn_metrics.get((window, model), {}).get("test", {})
            wdata["static_ic"].append(round(sd.get("IC", 0) or 0, 4))
            wdata["dynamic_ic"].append(round(dd.get("IC", 0) or 0, 4))
            wdata["static_icir"].append(round(sd.get("ICIR", 0) or 0, 4))
            wdata["dynamic_icir"].append(round(dd.get("ICIR", 0) or 0, 4))
        out[window] = wdata
    return json.dumps(out)


def build_summary_cards():
    """High-level summary numbers."""
    wins = 0
    total = 0
    total_ic_delta = 0
    total_icir_delta = 0
    best_delta = {"ic": -999, "model": "", "window": ""}

    for window in WINDOWS:
        for model in SHARED_MODELS:
            sd = sta_metrics.get((window, model), {}).get("test", {})
            dd = dyn_metrics.get((window, model), {}).get("test", {})
            sic = sd.get("IC")
            dic = dd.get("IC")
            sicir = sd.get("ICIR")
            dicir = dd.get("ICIR")
            if sic is not None and dic is not None:
                total += 1
                d = dic - sic
                total_ic_delta += d
                if d > 0:
                    wins += 1
                if d > best_delta["ic"]:
                    best_delta = {"ic": d, "model": MODEL_LABELS.get(model, model), "window": window}
            if sicir is not None and dicir is not None:
                total_icir_delta += dicir - sicir

    avg_ic_delta = total_ic_delta / total if total else 0
    avg_icir_delta = total_icir_delta / total if total else 0

    cards = [
        ("Win Rate (IC↑)", f"{wins}/{total}", f"{wins/total*100:.0f}% of model-window pairs show higher IC in dynamic mode"),
        ("Avg IC Δ", f"{avg_ic_delta:+.4f}", "Mean (dynamic − static) test IC across all model-window pairs"),
        ("Avg ICIR Δ", f"{avg_icir_delta:+.4f}", "Mean (dynamic − static) test ICIR across all model-window pairs"),
        ("Best Gain", f"{best_delta['model']}\n{best_delta['window']}", f"IC Δ = {best_delta['ic']:+.4f}"),
    ]

    html = ""
    for title, value, desc in cards:
        color = "#16a34a" if ("+" in str(value) or "%" in str(value)) else "#1e40af"
        html += f"""
<div class="card">
  <div class="card-title">{title}</div>
  <div class="card-value" style="color:{color}">{value.replace(chr(10),'<br>')}</div>
  <div class="card-desc">{desc}</div>
</div>"""
    return html


heatmap_data = build_delta_heatmap_data()
portfolio_data = build_portfolio_chart_data()
ic_data = build_ic_chart_data()
metrics_tables = build_metrics_section()
summary_cards = build_summary_cards()

HTML = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>Dynamic vs Static Graph — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f8fafc; color: #1e293b; font-size: 14px; }}
  .header {{ background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%); color: white; padding: 32px 40px; }}
  .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
  .header .meta {{ font-size: 13px; opacity: 0.85; }}
  .main {{ max-width: 1400px; margin: 0 auto; padding: 24px 20px; }}
  .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  h2 {{ font-size: 18px; font-weight: 600; color: #0f172a; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0; }}
  h3 {{ font-size: 15px; font-weight: 600; color: #334155; margin: 16px 0 10px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #f1f5f9; padding: 8px 10px; text-align: center; font-weight: 600; border-bottom: 2px solid #e2e8f0; white-space: nowrap; }}
  td {{ padding: 7px 10px; border-bottom: 1px solid #f1f5f9; white-space: nowrap; }}
  tr:hover td {{ background: #f8fafc; }}
  .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
  .card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.08); text-align: center; }}
  .card-title {{ font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 8px; }}
  .card-value {{ font-size: 26px; font-weight: 700; line-height: 1.2; margin-bottom: 6px; }}
  .card-desc {{ font-size: 12px; color: #94a3b8; line-height: 1.4; }}
  .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 16px; }}
  .chart-box {{ position: relative; height: 280px; }}
  .heatmap-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .heatmap-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  .heatmap-table th {{ background: #f1f5f9; padding: 6px 8px; font-weight: 600; font-size: 11px; }}
  .heatmap-table td {{ padding: 6px 10px; text-align: center; font-weight: 600; }}
  .legend {{ display: flex; gap: 16px; align-items: center; margin-bottom: 12px; font-size: 12px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; }}
  .tab-bar {{ display: flex; gap: 4px; margin-bottom: 20px; }}
  .tab {{ padding: 8px 20px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 500; background: #f1f5f9; color: #64748b; border: none; }}
  .tab.active {{ background: #1e40af; color: white; }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  .param-table {{ width: 100%; border-collapse: collapse; }}
  .param-table th {{ text-align: left; background: #f8fafc; padding: 8px 12px; font-size: 12px; color: #64748b; border-bottom: 1px solid #e2e8f0; }}
  .param-table td {{ padding: 8px 12px; border-bottom: 1px solid #f1f5f9; font-size: 13px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .badge-blue {{ background: #dbeafe; color: #1e40af; }}
  .badge-green {{ background: #dcfce7; color: #16a34a; }}
  .badge-gray {{ background: #f1f5f9; color: #475569; }}
  @media (max-width: 900px) {{ .cards {{ grid-template-columns: 1fr 1fr; }} .chart-grid {{ grid-template-columns: 1fr; }} .heatmap-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>Dynamic vs Static Graph — Experiment Dashboard</h1>
  <div class="meta">
    Static run: 2026-05-24 → 2026-05-25 &nbsp;|&nbsp;
    Dynamic run: 2026-06-08 01:35 → 03:51 &nbsp;|&nbsp;
    Test period: ~2024-12-03 to 2025-05-29 (116 days) &nbsp;|&nbsp;
    Models: 6 shared + 3 baseline (static only) &nbsp;|&nbsp;
    Windows: Short / Medium / Long
  </div>
</div>
<div class="main">

  <!-- Summary Cards -->
  <div class="cards">
    {summary_cards}
  </div>

  <!-- Parameter Comparison -->
  <div class="section">
    <h2>Experiment Configuration Comparison</h2>
    <div style="overflow-x:auto">
    <table class="param-table">
      <thead><tr>
        <th>Parameter</th>
        <th>Static (runs_gpu_static_to_20250601)</th>
        <th>Dynamic (runs_dynamic_only_6_8)</th>
        <th>Difference</th>
      </tr></thead>
      <tbody>
        <tr><td>Graph mode</td><td><span class="badge badge-gray">static</span></td><td><span class="badge badge-blue">dynamic</span></td><td>Static = fixed graph; Dynamic = rebuilt each day via rolling correlation</td></tr>
        <tr><td>Dynamic graphs</td><td>false</td><td>true</td><td>—</td></tr>
        <tr><td>Graph lookback (dynamic only)</td><td>N/A</td><td>60 days</td><td>Window for rolling correlation computation</td></tr>
        <tr style="background:#fef9c3"><td><b>Industry 建圖方式</b></td><td><b>同產業全連接（intra-industry full clique）</b></td><td><b>滾動相關 top 50%（top_pct=0.5）</b></td><td>Static 更稠密；Dynamic 依相關性篩選</td></tr>
        <tr style="background:#fef9c3"><td><b>Universe 建圖方式</b></td><td><b>完全圖（N×N，全連接）</b></td><td><b>滾動相關 top-100 per node</b></td><td>Static N²全連；Dynamic 稀疏有權重</td></tr>
        <tr><td>Industry 邊數</td><td>~27,923（固定，每日相同）</td><td>avg ~18,937 / day（每日變動）</td><td>Static 反而更多邊</td></tr>
        <tr><td>Universe 邊數</td><td>594,441（固定，771×771完全圖）</td><td>avg ~100,954 / day（每日變動）</td><td>Static 約多 5.9× 邊</td></tr>
        <tr><td>Edge attributes</td><td>無（edge_dim=null）</td><td>abs_corr, signed_corr（edge_dim=2）</td><td>Dynamic 每條邊帶相關係數特徵</td></tr>
        <tr><td>Parallel jobs</td><td>1</td><td>2</td><td>—</td></tr>
        <tr><td>Baseline models included</td><td>Yes (linear, XGBoost, LSTM)</td><td>No</td><td>Dynamic run skipped baselines</td></tr>
        <tr><td>Split ratio (train/val/test)</td><td>0.8 / 0.1 / 0.1</td><td>0.8 / 0.1 / 0.1</td><td>Same</td></tr>
      </tbody>
    </table>
    </div>
  </div>

  <!-- IC/ICIR Bar Charts -->
  <div class="section">
    <h2>Test IC &amp; ICIR Comparison — by Window</h2>
    <div class="legend">
      <span><span class="legend-dot" style="background:#3b82f6"></span>Static IC</span>
      <span><span class="legend-dot" style="background:#1d4ed8"></span>Dynamic IC</span>
      <span><span class="legend-dot" style="background:#f59e0b;margin-left:12px"></span>Static ICIR</span>
      <span><span class="legend-dot" style="background:#d97706"></span>Dynamic ICIR</span>
    </div>
    <div class="tab-bar" id="ic-tabs">
      <button class="tab active" onclick="switchTab('ic','short',this)">Short</button>
      <button class="tab" onclick="switchTab('ic','medium',this)">Medium</button>
      <button class="tab" onclick="switchTab('ic','long',this)">Long</button>
    </div>
    <div id="ic-short" class="tab-content active" style="position:relative;height:300px"><canvas id="ic-chart-short"></canvas></div>
    <div id="ic-medium" class="tab-content" style="position:relative;height:300px"><canvas id="ic-chart-medium"></canvas></div>
    <div id="ic-long" class="tab-content" style="position:relative;height:300px"><canvas id="ic-chart-long"></canvas></div>
  </div>

  <!-- Portfolio Bar Charts -->
  <div class="section">
    <h2>Portfolio Performance Comparison — by Window</h2>
    <div class="legend">
      <span><span class="legend-dot" style="background:#64748b"></span>Static</span>
      <span><span class="legend-dot" style="background:#3b82f6"></span>Dynamic</span>
    </div>
    <div class="tab-bar" id="port-tabs">
      <button class="tab active" onclick="switchTab('port','short',this)">Short</button>
      <button class="tab" onclick="switchTab('port','medium',this)">Medium</button>
      <button class="tab" onclick="switchTab('port','long',this)">Long</button>
    </div>
    <div id="port-short" class="tab-content active">
      <div class="chart-grid">
        <div class="chart-box"><canvas id="port-sharpe-short"></canvas></div>
        <div class="chart-box"><canvas id="port-cagr-short"></canvas></div>
        <div class="chart-box"><canvas id="port-maxdd-short"></canvas></div>
      </div>
    </div>
    <div id="port-medium" class="tab-content">
      <div class="chart-grid">
        <div class="chart-box"><canvas id="port-sharpe-medium"></canvas></div>
        <div class="chart-box"><canvas id="port-cagr-medium"></canvas></div>
        <div class="chart-box"><canvas id="port-maxdd-medium"></canvas></div>
      </div>
    </div>
    <div id="port-long" class="tab-content">
      <div class="chart-grid">
        <div class="chart-box"><canvas id="port-sharpe-long"></canvas></div>
        <div class="chart-box"><canvas id="port-cagr-long"></canvas></div>
        <div class="chart-box"><canvas id="port-maxdd-long"></canvas></div>
      </div>
    </div>
  </div>

  <!-- Delta Heatmaps -->
  <div class="section">
    <h2>Δ Heatmaps — Dynamic minus Static (test set)</h2>
    <p style="font-size:13px;color:#64748b;margin-bottom:16px">Green = Dynamic improves over Static &nbsp;|&nbsp; Red = Dynamic regresses &nbsp;|&nbsp; Gray ≈ neutral</p>
    <div id="heatmap-container"></div>
  </div>

  <!-- Full Metrics Tables -->
  <div class="section">
    <h2>Full Test-Set Metrics Tables</h2>
    <p style="font-size:13px;color:#64748b;margin-bottom:20px">
      Static | Dynamic | Δ (Dynamic−Static). Baselines are static-only (no dynamic equivalent).
    </p>
    {metrics_tables}
  </div>

</div>

<script>
const IC_DATA = {ic_data};
const PORT_DATA = {portfolio_data};
const HEATMAP_DATA = {heatmap_data};
const WINDOWS = ['short','medium','long'];
const MODELS = ['MLP','GAT-Industry','GAT-Universe','GAT-TwoGraph','DMFM-IndNeut','DMFM-Full'];

function switchTab(group, win, btn) {{
  document.querySelectorAll(`#${{group}}-tabs .tab`).forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  ['short','medium','long'].forEach(w => {{
    const el = document.getElementById(`${{group}}-${{w}}`);
    if (el) el.classList.toggle('active', w === win);
  }});
}}

// IC Charts
function makeICChart(window) {{
  const d = IC_DATA[window];
  const ctx = document.getElementById(`ic-chart-${{window}}`).getContext('2d');
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: d.models,
      datasets: [
        {{ label: 'Static IC', data: d.static_ic, backgroundColor: 'rgba(59,130,246,0.5)', borderColor: '#3b82f6', borderWidth: 1 }},
        {{ label: 'Dynamic IC', data: d.dynamic_ic, backgroundColor: 'rgba(29,78,216,0.7)', borderColor: '#1d4ed8', borderWidth: 1 }},
        {{ label: 'Static ICIR', data: d.static_icir, backgroundColor: 'rgba(245,158,11,0.4)', borderColor: '#f59e0b', borderWidth: 1 }},
        {{ label: 'Dynamic ICIR', data: d.dynamic_icir, backgroundColor: 'rgba(217,119,6,0.6)', borderColor: '#d97706', borderWidth: 1 }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: 'top', labels: {{ font: {{ size: 11 }} }} }} }},
      scales: {{
        y: {{ grid: {{ color: '#f1f5f9' }} }},
        x: {{ ticks: {{ font: {{ size: 11 }} }} }}
      }}
    }}
  }});
}}
WINDOWS.forEach(makeICChart);

// Portfolio Charts
function makePortChart(window, metric, label, canvasId, higherBetter) {{
  const d = PORT_DATA[window];
  const ctx = document.getElementById(canvasId).getContext('2d');
  const isPct = metric === 'cagr' || metric === 'max_drawdown';
  const fmt = v => isPct ? (v*100).toFixed(1)+'%' : v.toFixed(3);
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: d.models,
      datasets: [
        {{ label: 'Static', data: d.static[metric], backgroundColor: 'rgba(100,116,139,0.5)', borderColor: '#64748b', borderWidth: 1 }},
        {{ label: 'Dynamic', data: d.dynamic[metric], backgroundColor: 'rgba(59,130,246,0.6)', borderColor: '#3b82f6', borderWidth: 1 }},
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        title: {{ display: true, text: label, font: {{ size: 13, weight: '600' }} }},
        legend: {{ position: 'top', labels: {{ font: {{ size: 11 }} }} }}
      }},
      scales: {{
        y: {{ grid: {{ color: '#f1f5f9' }}, ticks: {{ callback: v => isPct ? (v*100).toFixed(0)+'%' : v.toFixed(2) }} }},
        x: {{ ticks: {{ font: {{ size: 10 }}, maxRotation: 30 }} }}
      }}
    }}
  }});
}}

WINDOWS.forEach(w => {{
  makePortChart(w, 'sharpe', 'Sharpe Ratio', `port-sharpe-${{w}}`, true);
  makePortChart(w, 'cagr', 'CAGR', `port-cagr-${{w}}`, true);
  makePortChart(w, 'max_drawdown', 'Max Drawdown', `port-maxdd-${{w}}`, false);
}});

// Heatmaps
const METRIC_KEYS = Object.keys(HEATMAP_DATA);
const WIN_LABELS = {{ short: 'Short', medium: 'Medium', long: 'Long' }};

function heatColor(v, higherBetter) {{
  if (v === null) return '#f1f5f9';
  const intensity = Math.min(Math.abs(v) * 50, 1);
  const positive = higherBetter ? v > 0 : v < 0;
  if (positive) {{
    const g = Math.round(165 + intensity * 90);
    return `rgba(22, ${{g}}, 74, ${{0.15 + intensity * 0.5}})`;
  }} else {{
    const r = Math.round(185 + intensity * 70);
    return `rgba(${{r}}, 38, 38, ${{0.12 + intensity * 0.45}})`;
  }}
}}

function buildHeatmaps() {{
  const container = document.getElementById('heatmap-container');
  METRIC_KEYS.forEach(metric => {{
    const info = HEATMAP_DATA[metric];
    const grid = info.grid;
    const hb = info.higher_better;

    let html = `<h3>${{metric}}</h3><div style="overflow-x:auto;margin-bottom:20px"><table class="heatmap-table"><thead><tr><th>Model</th>`;
    ['Short','Medium','Long'].forEach(w => html += `<th>${{w}}</th>`);
    html += '</tr></thead><tbody>';

    MODELS.forEach((m, mi) => {{
      html += `<tr><td style="text-align:left;font-weight:600">${{m}}</td>`;
      [0,1,2].forEach(wi => {{
        const v = grid[mi][wi];
        const bg = heatColor(v, hb);
        const txt = v === null ? '—' : (Math.abs(v) < 0.01 ? v.toFixed(4) : v > 0 ? `+${{v.toFixed(4)}}` : v.toFixed(4));
        const col = v === null ? '#94a3b8' : (hb ? (v > 0.001 ? '#166534' : v < -0.001 ? '#991b1b' : '#475569') : (v < -0.001 ? '#166534' : v > 0.001 ? '#991b1b' : '#475569'));
        html += `<td style="background:${{bg}};color:${{col}}">${{txt}}</td>`;
      }});
      html += '</tr>';
    }});
    html += '</tbody></table></div>';
    container.innerHTML += html;
  }});
}}
buildHeatmaps();
</script>
</body>
</html>
"""

out_path = BASE / "dashboard_dynamic_vs_static.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"Dashboard written to: {out_path}")
print(f"File size: {out_path.stat().st_size / 1024:.1f} KB")
