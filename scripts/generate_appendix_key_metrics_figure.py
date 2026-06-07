#!/usr/bin/env python3
"""Generate the compact appendix key-metrics comparison figure."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs_gpu_static_to_20250601" / "static"
OUTPUT = ROOT / "img" / "appendix_static_gpu_key_metrics_by_window.svg"
PDF_OUTPUT = OUTPUT.with_suffix(".pdf")
PNG_OUTPUT = OUTPUT.with_suffix(".png")

WINDOWS = ("short", "medium", "long")
WINDOW_LABELS = ("Short", "Medium", "Long")
MODELS = (
    ("baseline_linear", "Linear"),
    ("baseline_lstm", "LSTM"),
    ("baseline_xgboost", "XGBoost"),
    ("mlp", "DNN"),
    ("gat_industry", "GAT-industry"),
    ("gat_universe", "GAT-universe"),
    ("gat_two_graph_no_neutral", "GAT-TwoGraph"),
    ("dmfm_ind_neutral", "GAT-IndNeutral"),
    ("dmfm_full", "GAT-full"),
)
METRICS = (
    ("daily_ic", "Daily IC", "排序訊號", 4),
    ("icir", "ICIR", "訊號穩定性", 3),
    ("sharpe", "Sharpe", "投資可用性", 3),
)

THESIS_BLUE = (43, 108, 176)
THESIS_DARK = "#2d3748"
THESIS_LIGHT = (247, 250, 252)
THESIS_MID_GRAY = "#8291a0"
GRID = "#d9e2ec"
GROUP_FILL = ("#fffdf8", "#f7fafc", "#faf8ff")


def load_values() -> dict[str, dict[str, dict[str, float]]]:
    values: dict[str, dict[str, dict[str, float]]] = {}
    for window in WINDOWS:
        values[window] = {}
        for model_key, _ in MODELS:
            model_dir = RUNS / window / model_key
            metrics = json.loads((model_dir / "metrics.json").read_text())
            portfolio = json.loads((model_dir / "portfolio.json").read_text())
            values[window][model_key] = {
                "daily_ic": metrics["test"]["DailyIC"],
                "icir": metrics["test"]["ICIR"],
                "sharpe": portfolio["strategy"]["sharpe"],
            }
    return values


def mix_color(start: tuple[int, int, int], end: tuple[int, int, int], t: float) -> str:
    t = max(0.0, min(1.0, t))
    rgb = tuple(round(a + (b - a) * t) for a, b in zip(start, end))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def text(
    x: float,
    y: float,
    content: str,
    css_class: str,
    *,
    anchor: str = "start",
    fill: str | None = None,
) -> str:
    fill_attr = f' fill="{fill}"' if fill else ""
    return (
        f'<text class="{css_class}" x="{x}" y="{y}" '
        f'text-anchor="{anchor}"{fill_attr}>{escape(content)}</text>'
    )


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str = "none",
    stroke_width: float = 0,
    radius: float = 0,
) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def main() -> None:
    values = load_values()

    width, height = 1800, 1110
    label_right = 260
    panel_x = (300, 805, 1310)
    panel_width = 450
    cell_width = 150
    grid_top = 220
    row_height = 76
    grid_height = row_height * len(MODELS)

    all_values = {
        metric_key: [
            values[window][model_key][metric_key]
            for window in WINDOWS
            for model_key, _ in MODELS
        ]
        for metric_key, _, _, _ in METRICS
    }
    metric_min = {
        "daily_ic": 0.0,
        "icir": 0.0,
        "sharpe": min(all_values["sharpe"]),
    }
    metric_max = {key: max(metric_values) for key, metric_values in all_values.items()}

    best = {
        metric_key: {
            window: max(values[window][model_key][metric_key] for model_key, _ in MODELS)
            for window in WINDOWS
        }
        for metric_key, _, _, _ in METRICS
    }

    svg: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        """<style>
        .metricTitle{font:700 34px 'Times New Roman','Songti TC',serif;fill:#2d3748}
        .metricSub{font:500 21px 'Times New Roman','Songti TC',serif;fill:#8291a0}
        .window{font:700 21px 'Times New Roman','Songti TC',serif;fill:#2d3748}
        .model{font:500 22px 'Times New Roman','Songti TC',serif;fill:#2d3748}
        .value{font:500 21px 'Times New Roman','Songti TC',serif}
        .best{font:700 21px 'Times New Roman','Songti TC',serif}
        .group{font:500 18px 'Times New Roman','Songti TC',serif;fill:#8291a0}
        .note{font:500 19px 'Times New Roman','Songti TC',serif;fill:#59697a}
        </style>""",
        rect(0, 0, width, height, fill="#ffffff"),
    ]

    group_ranges = (
        (0, 4, GROUP_FILL[0], "基準模型"),
        (4, 7, GROUP_FILL[1], "GAT 模型"),
        (7, 9, GROUP_FILL[2], "中性化模型"),
    )
    for start, end, fill, label in group_ranges:
        y = grid_top + start * row_height
        group_height = (end - start) * row_height
        svg.append(rect(20, y + 2, label_right - 28, group_height - 4, fill=fill, radius=8))
        svg.append(rect(20, y + 2, 7, group_height - 4, fill=THESIS_MID_GRAY, radius=3))
        svg.append(text(38, y + 26, label, "group"))

    for row, (_, model_label) in enumerate(MODELS):
        y_center = grid_top + row * row_height + row_height / 2
        svg.append(text(label_right, y_center + 7, model_label, "model", anchor="end"))

    for panel_index, (metric_key, metric_label, metric_subtitle, digits) in enumerate(METRICS):
        x0 = panel_x[panel_index]
        svg.append(text(x0 + panel_width / 2, 63, metric_label, "metricTitle", anchor="middle"))
        svg.append(text(x0 + panel_width / 2, 98, metric_subtitle, "metricSub", anchor="middle"))

        for col, window_label in enumerate(WINDOW_LABELS):
            x = x0 + col * cell_width
            svg.append(
                rect(
                    x,
                    145,
                    cell_width,
                    58,
                    fill="#edf2f7",
                    stroke=GRID,
                    stroke_width=1.5,
                    radius=5,
                )
            )
            svg.append(text(x + cell_width / 2, 182, window_label, "window", anchor="middle"))

        low = metric_min[metric_key]
        high = metric_max[metric_key]
        for row, (model_key, _) in enumerate(MODELS):
            y = grid_top + row * row_height
            for col, window in enumerate(WINDOWS):
                x = x0 + col * cell_width
                value = values[window][model_key][metric_key]
                normalized = (value - low) / (high - low)
                color_strength = 0.10 + 0.88 * normalized
                fill = mix_color(THESIS_LIGHT, THESIS_BLUE, color_strength)
                is_best = abs(value - best[metric_key][window]) < 1e-12
                stroke = THESIS_DARK if is_best else GRID
                stroke_width = 4 if is_best else 1.5
                value_fill = "#ffffff" if normalized > 0.67 else THESIS_DARK
                css_class = "best" if is_best else "value"

                svg.append(
                    rect(
                        x,
                        y,
                        cell_width,
                        row_height,
                        fill=fill,
                        stroke=stroke,
                        stroke_width=stroke_width,
                        radius=4,
                    )
                )
                svg.append(
                    text(
                        x + cell_width / 2,
                        y + row_height / 2 + 7,
                        f"{value:.{digits}f}",
                        css_class,
                        anchor="middle",
                        fill=value_fill,
                    )
                )

    for separator_after in (4, 7):
        y = grid_top + separator_after * row_height
        svg.append(
            f'<line x1="20" y1="{y}" x2="{width - 40}" y2="{y}" '
            f'stroke="{THESIS_DARK}" stroke-opacity="0.30" stroke-width="2"/>'
        )

    legend_y = 960
    gradient_x, gradient_width = 395, 275
    steps = 16
    for step in range(steps):
        svg.append(
            rect(
                gradient_x + step * gradient_width / steps,
                legend_y,
                gradient_width / steps + 1,
                22,
                fill=mix_color(THESIS_LIGHT, THESIS_BLUE, step / (steps - 1)),
            )
        )
    svg.append(text(gradient_x - 18, legend_y + 18, "低", "note", anchor="end"))
    svg.append(text(gradient_x + gradient_width + 18, legend_y + 18, "高", "note"))
    svg.append(
        text(
            width / 2,
            1035,
            "色彩越深代表指標越高；粗框標示各視窗的最佳模型。完整指標與數值見後表。",
            "note",
            anchor="middle",
        )
    )

    svg.append("</svg>")
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Wrote {OUTPUT}")

    rsvg_convert = shutil.which("rsvg-convert")
    if rsvg_convert:
        subprocess.run(
            [rsvg_convert, "-f", "pdf", "-o", str(PDF_OUTPUT), str(OUTPUT)],
            check=True,
        )
        subprocess.run(
            [rsvg_convert, "-f", "png", "-w", "2700", "-o", str(PNG_OUTPUT), str(OUTPUT)],
            check=True,
        )
        print(f"Wrote {PDF_OUTPUT}")
        print(f"Wrote {PNG_OUTPUT}")


if __name__ == "__main__":
    main()
