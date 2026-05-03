# 論文敘述與目前 model 設計口徑一致性盤點

本文件依論文章節順序整理本次檢查到的口徑不一致處，並標記本次已修正的方向。程式依據主要參考 `/Users/luoyi/Desktop/gat_9_15` 的 `run_pipeline.py`、`build_artifacts.py`、`model_dmfm_wei2022.py`、`train_factor_variants.py` 與 `train_baselines.py`。

## 摘要

- 舊口徑：模型比較寫成 Linear、XGBoost、LSTM、單圖 GAT 與完整中性化模型五模型。
- 目前設計：統一實驗為三個 baseline 加六個 factor ablation models；圖模型比較 static / dynamic graph。
- 修正方向：摘要改為 baseline + MLP / GAT-Factor-Ind / GAT-Factor-Mkt / GAT-Factor-Dual / GAT-Factor-IndNeu / GAT-Factor-Full，並更新 45 組實驗的關鍵結果。

## 第一章 緒論

- 舊口徑：研究問題與貢獻集中於完整中性化模型是否優於單圖 GAT。
- 目前設計：核心問題是圖建構口徑與中性化設計的消融比較，不是單一圖模型對完整中性化模型。
- 修正方向：緒論改為「baseline + factor variants + static/dynamic graph」的統一實驗敘述，研究貢獻新增 dynamic graph 比較與消融實驗。

## 第二章 文獻回顧

- 舊口徑：GAT 限制提到 static graph 問題，但未銜接到目前 dynamic graph 與消融設計。
- 目前設計：dynamic graph 以 rolling correlation top-k 建邊，但其效果需要實證檢驗。
- 修正方向：補上 static/dynamic graph 比較與 factor ablation 的方法論動機。

## 第三章 實驗設計

- 舊口徑：3.3 寫成單圖 GAT 與完整中性化模型兩段。
- 目前設計：正式 pipeline 不再用舊版單圖 GAT 作主文比較，而是用 `FactorGraphAblation` 六模型。
- 修正方向：模型設計改寫為非圖 baseline、factor ablation models、factor attention 三部分。

- 舊口徑：圖結構只描述 static 產業完全圖與全市場完全圖。
- 目前設計：同時建立 static graph 與 dynamic weighted graph；dynamic edge attributes 為 `[abs_corr, signed_corr]`。
- 修正方向：補入 dynamic graph 的 rolling lookback、min obs、top-k 與 edge_attr 設定。

- 舊口徑：部分特徵定義與程式不同，例如 `pct_pos` 被寫成區間位置、`beta_60` 被寫成對 0050 的市場 beta。
- 目前設計：`pct_pos` 是近 k 日日報酬為正的比例；`beta_60` 是個股報酬內部 rolling beta proxy。
- 修正方向：第三章摘要表與附錄完整特徵表均已修正。

## 第四章 實驗結果

- 舊口徑：結果仍引用舊的五模型數值，例如 XGBoost Short IC 0.0863、完整中性化模型 Long ICIR 0.8905。
- 目前設計：主結果來自 `runs_unified/analysis_report`，共 45 組實驗。
- 修正方向：第四章改為統一實驗 winner、dynamic-static delta、模型穩定性與注意力特徵頻率四段，並引用 `runs_unified/analysis_report/charts` 圖表。

## 第五章 結論與未來工作

- 舊口徑：僅列未來工作，沒有根據新實驗結果形成結論。
- 目前設計：需明確說明沒有單一模型全面最佳，dynamic graph 是條件性改善。
- 修正方向：第五章改為「結論與未來工作」，加入新實驗結論與後續研究方向。

## 附錄

- 舊口徑：附錄圖表仍指向 `runs_gpu_full1`，並列舊版單圖 GAT / 完整中性化模型圖。
- 目前設計：正式輸出位於 `runs_unified`，完整分析位於 `runs_unified/analysis_report`。
- 修正方向：附錄完整輸出改為 `runs_unified` 的全模型關鍵指標與 analysis_report 圖表。
