# Investment Analytics Benchmarks

Command:

```powershell
cd backend
python scripts\benchmark_investment_platform.py
```

Measured on July 26, 2026, on Windows 11, Python 3.14.5, five assets, and 1,260 daily
observations. Results are CPU wall-clock measurements and exclude provider
network latency.

| Operation | Median | p95 | Repetitions |
| --- | ---: | ---: | ---: |
| Complete technical indicator frame | 173.555 ms | 209.557 ms | 50 |
| Risk metrics with benchmark beta | 26.551 ms | 38.551 ms | 100 |
| Six-component decision policy | 0.324 ms | 0.685 ms | 2,000 |
| Five-asset portfolio analysis | 605.659 ms | 651.897 ms | 5 |

The portfolio measurement includes shrinkage covariance, risk contribution,
18-point efficient frontier, constrained rebalancing, correlation matrix,
allocation timeline, factor estimates, and 2,500 one-year Monte Carlo paths.

External provider calls and hosted sentiment inference dominate end-to-end
latency. Those operations use independent caches and graceful confidence
reduction rather than blocking deterministic analysis indefinitely.

