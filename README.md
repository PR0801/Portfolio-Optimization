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

## Getting started
```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the example
python run_example.py
```

Feel free to extend the library with additional assets, constraints, or custom risk measures.
