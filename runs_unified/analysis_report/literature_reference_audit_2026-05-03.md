# Literature and Reference Audit (2026-05-03)

## Scope

This audit checks whether the current literature review and references support the revised experiment design in `/Users/luoyi/Desktop/gat_9_15` and the unified results in `/Users/luoyi/Desktop/Roy_Thesis/runs_unified`.

## Literature Gaps to Fill or Strengthen

1. **Regularized linear benchmark**
   - Current thesis discusses linear regression as a benchmark, but the actual implementation uses Ridge regression (`alpha=1.0`), not plain OLS.
   - Add or cite Ridge regression as a regularized linear estimator for multicollinearity and high-dimensional tabular factors.
   - Verified source: Hoerl and Kennard, *Technometrics*, 1970, DOI `10.1080/00401706.1970.10488634`.

2. **LSTM as the time-series benchmark**
   - Current LSTM review covers financial applications, but the experiment design also needs the foundational LSTM architecture rationale.
   - The method section should cite Hochreiter and Schmidhuber because the implemented baseline uses a gated recurrent architecture with last hidden state prediction.
   - Verified source: Hochreiter and Schmidhuber, *Neural Computation*, 1997, DOI `10.1162/neco.1997.9.8.1735`.

3. **GAT and graph implementation basis**
   - The thesis already discusses GNN/GAT conceptually, but the experiment design uses PyTorch Geometric `edge_index`, GATConv, multi-head attention, and static/dynamic graph artifacts.
   - Add foundational GAT and PyTorch Geometric references to support model construction and implementation vocabulary.
   - Verified sources: Velickovic et al., ICLR 2018; Fey and Lenssen, ICLR RLGM Workshop 2019 / arXiv `10.48550/arXiv.1903.02428`.

4. **Correlation-based financial networks**
   - The dynamic graph is built from rolling return correlations with `abs_corr` and `signed_corr` edge attributes. The current literature review does not sufficiently justify correlation networks as a financial-market relation proxy.
   - Add financial correlation network literature to explain why rolling correlations can encode time-varying market co-movement, while emphasizing that correlation edges are not causal links.
   - Verified sources: Mantegna, *European Physical Journal B*, 1999, DOI `10.1007/s100510050929`; Onnela et al., *Physical Review E*, 2003, DOI `10.1103/PhysRevE.68.056110`.

5. **Optimization and normalization details**
   - Factor variants use BatchNorm, AdamW, dropout, weight decay, early stopping by validation ICIR, and gradient clipping. The literature review does not yet discuss why these choices are appropriate for unstable deep models.
   - Add short method-level support for BatchNorm and AdamW at minimum.
   - Verified sources: Ioffe and Szegedy, ICML 2015; Loshchilov and Hutter, ICLR 2019.

6. **Attention interpretation caveat**
   - The results section uses factor attention top features. This is useful as descriptive model behavior, but attention weights should not be framed as causal feature importance.
   - Add references that caution against over-interpreting attention as explanation.
   - Verified sources: Jain and Wallace, NAACL 2019, DOI `10.18653/v1/N19-1357`; Serrano and Smith, ACL 2019, DOI `10.18653/v1/P19-1282`.

7. **Portfolio metrics and benchmark comparison**
   - The thesis uses Sharpe ratio, annualized return, hit ratio, max drawdown, and 0050 benchmark comparison. The literature review currently focuses more on IC/ICIR and less on portfolio-performance evaluation.
   - Add Sharpe ratio and optionally active portfolio evaluation / backtest robustness references.
   - Verified source added for Sharpe: Sharpe, *The Journal of Portfolio Management*, 1994, DOI `10.3905/jpm.1994.409501`.
   - Recommended additional sources if the final thesis discusses model selection or many strategy trials: White, *Econometrica*, 2000, DOI `10.1111/1468-0262.00152`; Bailey and Lopez de Prado, *The Journal of Portfolio Management*, 2014, DOI `10.3905/jpm.2014.40.5.094`; Harvey, Liu, and Zhu, *Review of Financial Studies*, 2016, DOI `10.1093/rfs/hhv059`.

8. **Transaction costs and turnover**
   - The current backtest uses top 10% equal-weight long-only portfolios and 5-day rebalance, but the main tables do not yet incorporate transaction costs, slippage, liquidity constraints, or turnover.
   - If the conclusion discusses deployability, add literature on turnover-adjusted IR and transaction costs. The existing `zhang2021turnover_ir` helps, but it is arXiv; adding at least one peer-reviewed or industry-standard transaction cost reference would strengthen the discussion.

## Reference Field and Format Audit

| Key | Status | Issue | Recommended action |
|---|---|---|---|
| `fieberg2022ml_cross_section` | Fixed in `ref.bib` | DOI was valid, but volume/issue/pages were missing. | Added `volume=45`, `number=1`, `pages=289--323`. |
| `saifan2020ensemble_trading` | Fixed in `ref.bib` | Existing DOI pointed to IEEE Access and did not match the verified paper. Verified paper is in *Informatica*, title includes "Ensemble Machine Learning Methods", pages 311--325. | Replaced title/authors/journal/pages/DOI with verified Informatica record `10.31449/inf.v44i3.2904`. |
| `vidmant2019tree_volatility` | Still needs manual confirmation | DOI `10.1002/for.2506` resolves to a different *Journal of Forecasting* article. Web/Crossref searches did not verify the current title-author-journal combination. | Do not rely on this citation until the original PDF or publisher record is found. Replace with a verified volatility/tree-based source if this claim remains in Chapter 2. |
| `li2020stock` | Fixed in `ref.bib` | Page range was `185197--185215`, but verified records show `185232--185242`. | Updated pages to `185232--185242`. |
| `sonkavde2023review_ml_dl` | Fixed in `ref.bib` | Existing DOI `10.1016/j.eswa.2022.119043` resolves to a COVID/hazard-place ESWA article, not stock prediction. | Replaced with verified Sonkavde et al. IJFS 2023 review, DOI `10.3390/ijfs11030094`. |
| `wu2020comprehensive` | Fixed in `ref.bib` | DOI had an incorrect year/code and bibliographic fields were off. | Updated to `year=2021`, `volume=32`, `doi=10.1109/TNNLS.2020.2978386`. |
| `ye2008signal_quality` | Fixed in `ref.bib` | DOI should be `10.2469/faj.v64.n4.5`, not `.7`. | Updated DOI. |
| `Brock1992SimpleTT` | Needs style cleanup | URL is a Semantic Scholar API link, not a publisher/stable page. DOI is already present. | Remove URL or replace with DOI resolver/publisher URL. |
| `cheng2023stock` | Needs style decision | Uses `langid=chinese`, which may be ignored by IEEEtran BibTeX. Chinese thesis metadata may format inconsistently. | Keep if local requirement accepts Chinese references; otherwise use `language={Chinese}` and check final bibliography output. |
| arXiv entries (`wei2022factor`, `zhang2021turnover_ir`) | Mostly acceptable | Crossref may not resolve arXiv DOI, but arXiv/DataCite DOI and URL are valid. | Keep DOI plus URL; ensure citation text does not imply peer-reviewed publication. |
| Titles with acronyms | Needs style cleanup | BibTeX may downcase acronyms in titles depending on style. | Protect terms such as `{XGBoost}`, `{GAT}`, `{LSTM}`, `{ICIR}`, `{DJIA}`, `{PLoS ONE}` where needed. |

## Sources Checked Online

- Hoerl and Kennard Ridge regression: https://www.tandfonline.com/doi/abs/10.1080/00401706.1970.10488634
- GAT: https://mlanthology.org/iclr/2018/velickovic2018iclr-graph/
- Batch Normalization: https://proceedings.mlr.press/v37/ioffe15
- PyTorch Geometric: https://arxiv.org/abs/1903.02428
- AdamW: https://openreview.net/forum?id=Bkg6RiCqY7
- Saifan et al. Informatica paper: https://www.informatica.si/index.php/informatica/article/view/2904
- Sonkavde et al. IJFS review: https://www.mdpi.com/2227-7072/11/3/94
- Li and Bastos IEEE Access page audit: https://doaj.org/article/392dc53e878e44e99fa5a999a0a857bc
- Wu et al. GNN survey DOI audit: https://cir.nii.ac.jp/crid/1360292620698433152
- Ye signal quality DOI audit: https://rpc.cfainstitute.org/research/financial-analysts-journal/2008/how-variation-in-signal-quality-affects-performance
- Jain and Wallace attention caution: https://aclanthology.org/N19-1357/
- Serrano and Smith attention caution: https://aclanthology.org/P19-1282/
- White data snooping: https://www.econometricsociety.org/publications/econometrica/2000/09/01/reality-check-data-snooping
- Bailey and Lopez de Prado deflated Sharpe ratio: https://www.pm-research.com/content/iijpormgmt/40/5/94
- Harvey, Liu, and Zhu multiple testing in expected returns: https://academic.oup.com/rfs/article/29/1/5/1843824
