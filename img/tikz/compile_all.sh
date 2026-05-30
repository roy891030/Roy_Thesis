#!/usr/bin/env bash
# compile_all.sh – compile all TikZ standalone figures with xelatex
# Run from:  img/tikz/

set -euo pipefail
cd "$(dirname "$0")"

OUTDIR="../"   # PDFs go directly into img/
XELATEX="xelatex"
OPTS="-interaction=nonstopmode -halt-on-error -output-directory=."

# Map: source_basename → output PDF name in img/
declare -A FIGS=(
  [fig_edge_index]=edge_index_demo
  [fig_lstm]=LSTM_graph
  [fig_gnn_arch]=architecture_of_GNN
  [fig_gat_attention]=gat_attention_mechanism
  [fig_train_timeline]=train_test_split
  [fig_train_bar]=train_val_test_split_bar
  [fig_industry_graph]=industry_graph
  [fig_market_graph]=market_graph
  [fig_xgboost]=XGboost
)

for src in "${!FIGS[@]}"; do
  dest="${FIGS[$src]}"
  echo "──── Compiling ${src}.tex → ${dest}.pdf ────"
  $XELATEX $OPTS "${src}.tex"
  # xelatex outputs ${src}.pdf in cwd; move & rename
  mv -f "${src}.pdf" "${OUTDIR}${dest}.pdf"
  # clean aux files
  rm -f "${src}.aux" "${src}.log" "${src}.synctex.gz"
  echo "     ✓  ${dest}.pdf"
done

echo ""
echo "All figures compiled → img/"
