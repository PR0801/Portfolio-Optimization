# Portfolio Optimization & Risk Management System

This repository implements a **Modern Portfolio Theory (MPT)** based toolbox for:

- Fetching historical price data using **yFinance**.
- Computing returns, covariance, correlation, and various risk metrics (volatility, Sharpe ratio, VaR, maximum drawdown).
- Building **minimum‑variance**, **maximum‑Sharpe**, and **risk‑constrained** portfolios.
- Performing **rolling‑window** analysis and **historical stress testing** to evaluate portfolio stability across market regimes.
- Visualising the **efficient frontier** and portfolio metrics with **Matplotlib**.

The core logic lives in `portfolio_optimization/portfolio_optimizer.py`.

## Project structure
```
portfolio_optimization/
├── __init__.py
├── asset_fetcher.py
├── cli.py
└── portfolio_optimizer.py
README.md
requirements.txt
run_example.py
tests/
```

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
npm --prefix frontend ci
```

Start the API and frontend in separate terminals:

```bash
python -m uvicorn portfolio_optimization.web:app --reload --port 8000
npm --prefix frontend run dev
```

Open `http://localhost:5173` during development. The Vite server proxies API
requests to FastAPI on port 8000. In the deployed container, FastAPI serves the
built frontend and API together on port 8000.

## Container usage
```bash
docker build -t portfolio-studio .
docker run --rm -p 8000:8000 portfolio-studio
```

Then open `http://localhost:8000`. The image runs as a non-root user and exposes
a health check at `/api/health`. Analysis requires outbound network access to
download market data from yFinance. The command-line interface remains available
as `portfolio-optimize` for scripted use.

Feel free to extend the library with additional assets, constraints, or custom risk measures.
