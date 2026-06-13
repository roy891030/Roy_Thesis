#!/usr/bin/env bash
# regenerate_daily_ic_csv.sh
# ─────────────────────────────────────────────────────────────────────────────
# 批次重跑 evaluate_metrics.py，為每個 GAT/DNN 模型產生 daily_ic_series.csv
# 執行方式: bash scripts/regenerate_daily_ic_csv.sh
# 執行位置: /Users/luoyi/Desktop/Roy_Thesis 或任意目錄均可（使用絕對路徑）
# ─────────────────────────────────────────────────────────────────────────────

set -e

PYTHON="/Users/luoyi/Desktop/shortvideo_mmgcn_poc/.venv/bin/python"
CODE_DIR="/Users/luoyi/Desktop/gat_9_15"
ARTIFACTS_BASE="/Users/luoyi/Downloads/artifacts_gpu_static_to_20250601/static"
RUNS_BASE="/Users/luoyi/Desktop/Roy_Thesis/runs_gpu_static_to_20250601/static"
INDUSTRY_CSV="/Users/luoyi/Desktop/gat_9_15/unique_2019q3to2025q3.csv"

# 只跑 GAT / DNN（neural network）模型，不含 linear/xgboost/lstm
MODELS=(
  mlp
  gat_industry
  gat_universe
  gat_two_graph_no_neutral
  dmfm_ind_neutral
  dmfm_full
)
WINDOWS=(short medium long)

cd "$CODE_DIR"

for WINDOW in "${WINDOWS[@]}"; do
  for MODEL in "${MODELS[@]}"; do
    ARTIFACT_DIR="$ARTIFACTS_BASE/$WINDOW"
    WEIGHTS="$ARTIFACT_DIR/${MODEL}_best.pt"
    OUT_JSON="$RUNS_BASE/$WINDOW/$MODEL/metrics.json"
    CSV_TARGET="$RUNS_BASE/$WINDOW/$MODEL/daily_ic_series.csv"

    if [ ! -f "$WEIGHTS" ]; then
      echo "[SKIP] 找不到權重: $WEIGHTS"
      continue
    fi

    if [ -f "$CSV_TARGET" ]; then
      echo "[SKIP] 已存在: $WINDOW/$MODEL/daily_ic_series.csv"
      continue
    fi

    echo "──────────────────────────────────────"
    echo "[RUN]  $WINDOW / $MODEL"
    echo "──────────────────────────────────────"

    $PYTHON evaluate_metrics.py \
      --artifact_dir "$ARTIFACT_DIR" \
      --weights      "$WEIGHTS" \
      --device       cpu \
      --industry_csv "$INDUSTRY_CSV" \
      --train_ratio  0.8 \
      --val_ratio    0.1 \
      --out_json     "$OUT_JSON"

    if [ -f "$CSV_TARGET" ]; then
      echo "[OK]  已產生: $WINDOW/$MODEL/daily_ic_series.csv"
    else
      echo "[WARN] CSV 未出現，請檢查 evaluate_metrics.py 修改是否正確"
    fi

  done
done

echo ""
echo "完成！請執行 stability_tests.py Phase 2 驗證結果："
echo "  /Users/luoyi/Desktop/shortvideo_mmgcn_poc/.venv/bin/python scripts/stability_tests.py"
