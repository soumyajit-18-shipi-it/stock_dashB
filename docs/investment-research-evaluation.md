# Investment Intelligence Research Evaluation

Research was completed before implementation using the connected GitHub,
Hugging Face, and Kaggle discovery surfaces plus primary papers.

## Technical and Portfolio Libraries

| Candidate | Evidence | Decision |
| --- | --- | --- |
| [bukosabino/ta](https://github.com/bukosabino/ta) | Maintained Pandas/Numpy indicator library with broad conventional coverage. | Formula definitions and naming were compared. The repository's existing `TechnicalIndicators` class remains the integration surface to preserve saved-model compatibility and avoid two calculation paths. |
| [nardew/talipp](https://github.com/nardew/talipp) | Maintained incremental indicator implementation. | Not selected because this application analyzes daily batches and already uses Pandas frames; incremental state would add lifecycle complexity. |
| [PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt) | Mature efficient frontier, Black-Litterman, and HRP implementation. | Method behavior was compared. Runtime dependency was not selected because CVXPY materially increases the Render image and cold start; the constrained problem is handled by the existing SciPy stack. |
| [Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | Actively maintained, broad institutional risk measures. | Not selected for the same deployment footprint reason. Its breadth exceeds this platform's bounded long-only workflow. |
| [SHAP](https://github.com/shap/shap) | Actively maintained reference implementation of additive explanations. | Selected. `TreeExplainer` is used for RF; `LinearExplainer` is used after the persisted scaler transform. |

## Financial Sentiment Models

| Model | Model-card evidence | Assessment |
| --- | --- | --- |
| [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert) | Finance-domain BERT, Financial PhraseBank fine-tuning, very broad adoption, linked to the FinBERT paper. | Strong established baseline, but the Hub card does not declare an explicit software/model license. |
| [Financial DeBERTa v3](https://huggingface.co/mrm8488/deberta-v3-ft-financial-news-sentiment-analysis) | MIT license, hosted inference, explicit negative/neutral/positive mapping, Financial PhraseBank evaluation, 0.994 reported F1. | Selected default for deployability and explicit licensing. The very high card metric is not treated as independently verified; runtime output confidence is still coverage-weighted. |

The default model runs through hosted Hugging Face inference so Render does not
load a 142M-parameter transformer. `HUGGINGFACE_API_TOKEN` is required on Render.
There is no generic lexicon fallback because that would silently change the
measurement method.

## Dataset Review

- [Financial Sentiment Analysis on Kaggle](https://www.kaggle.com/datasets/sbhatti/financial-sentiment-analysis)
  combines FiQA and Financial PhraseBank under CC0 and is suitable for offline
  validation.
- [Financial PhraseBank on Hugging Face](https://huggingface.co/datasets/takala/financial_phrasebank)
  provides expert annotations but is non-commercially licensed; it is evaluated
  as a benchmark and is not redistributed by this repository.
- [FiQA sentiment classification](https://huggingface.co/datasets/TheFinAI/fiqa-sentiment-classification)
  is MIT licensed and suitable for a future independent temporal test suite.
- Kaggle portfolio datasets were not shipped because live provider data is
  already part of the product contract and static snapshots become stale.

## Primary Research Basis

- Lundberg and Lee, [A Unified Approach to Interpreting Model Predictions](https://papers.nips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html):
  selected SHAP for additive local attributions.
- Lundberg et al., [Explainable AI for Trees](https://arxiv.org/abs/1905.04610):
  selected the polynomial-time tree-specific explainer for random forests.
- Araci, [FinBERT](https://arxiv.org/abs/1908.10063):
  established the finance-domain sentiment baseline.
- He et al., [DeBERTa](https://arxiv.org/abs/2006.03654) and
  [DeBERTaV3](https://arxiv.org/abs/2111.09543):
  informed the selected sentiment architecture.
- Markowitz, [Portfolio Selection](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x):
  basis for the mean-variance frontier.
- Ledoit and Wolf, [A well-conditioned estimator for large-dimensional covariance matrices](https://doi.org/10.1016/S0047-259X(03)00096-4):
  basis for shrinkage covariance.

## Rejected Methods

- LIME and KernelExplainer were not selected for the existing RF and linear
  models because model-specific explainers are faster and exact for these
  families.
- Integrated Gradients was rejected because there is no differentiable neural
  prediction model in the current price pipeline.
- Raw sample covariance was rejected due to conditioning and estimation error.
- Predicted-price direction is deliberately capped at a 12% default policy
  weight and cannot independently pass the BUY policy guard.
