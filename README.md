# Portfolio Optimization & Risk Management System

This repository implements a **Modern Portfolio Theory (MPT)** based toolbox for:

- Fetching historical price data using **yFinance**.
- Computing returns, covariance, correlation, and various risk metrics (volatility, Sharpe ratio, VaR, maximum drawdown).
- Building **minimum‑variance**, **maximum‑Sharpe**, and **risk‑constrained** portfolios.
- Performing **rolling‑window** analysis and **historical stress testing** to evaluate portfolio stability across market regimes.
- Visualising the **efficient frontier** and portfolio metrics with **Matplotlib**.

The core logic lives in `portfolio_optimizer.py`. See the **Example usage** section at the bottom of that file for a quick start.

## Project structure
```
portfolio_optimization/
│   README.md               # This file
│   requirements.txt        # Python dependencies
│   portfolio_optimizer.py  # Core implementation
│   run_example.py          # Script that runs a demo and plots results
└── data/ (optional)        # Cached CSVs if you prefer offline data
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
