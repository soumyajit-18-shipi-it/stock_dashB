# Investment Analytics Benchmarks

Command:

```powershell
cd backend
python scripts\benchmark_investment_platform.py
```

Measured on Windows 11, Python 3.14.5, five assets, and 1,260 daily
observations. Results are CPU wall-clock measurements and exclude provider
network latency.

| Operation | Median | p95 | Repetitions |
| --- | ---: | ---: | ---: |
| Complete technical indicator frame | 35.992 ms | 42.470 ms | 50 |
| Risk metrics with benchmark beta | 5.788 ms | 7.228 ms | 100 |
| Six-component decision policy | 0.064 ms | 0.094 ms | 2,000 |
| Five-asset portfolio analysis | 111.785 ms | 120.748 ms | 5 |

The portfolio measurement includes shrinkage covariance, risk contribution,
18-point efficient frontier, constrained rebalancing, correlation matrix,
allocation timeline, factor estimates, and 2,500 one-year Monte Carlo paths.

External provider calls and hosted sentiment inference dominate end-to-end
latency. Those operations use independent caches and graceful confidence
reduction rather than blocking deterministic analysis indefinitely.
