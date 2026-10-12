# portfolio_optimizer.py
"""
Portfolio Optimization and Risk Management Toolkit
================================================

This module provides a set of functions to build and evaluate portfolios
using Modern Portfolio Theory (MPT). It leverages **yFinance** to download
historical price data and **NumPy**, **Pandas**, **SciPy** for the numerical
computations. **Matplotlib** is used for visualisation.

Key Features
------------
- Fetch historical adjusted close prices for a list of tickers.
- Compute daily returns, covariance, and correlation matrices.
- Construct:
  * Minimum‑variance portfolio
  * Maximum‑Sharpe‑ratio portfolio
  * Risk‑constrained portfolios (target volatility, target VaR, etc.)
- Rolling‑window analysis to see how the optimal weights evolve over time.
- Visualise the efficient frontier and portfolio metrics.

All functions are pure and can be combined freely. The bottom of the file
contains a small ``example`` block that demonstrates typical usage – it can
be executed directly or imported from ``run_example.py``.
"""

import numpy as np
import logging
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict

# ---------------------------------------------------------------------------
# Data acquisition
# ---------------------------------------------------------------------------


def download_price_data(
    tickers: List[str],
    start: str,
    end: str,
    interval: str = "1d",
) -> pd.DataFrame:
    """Download adjusted‑close prices for *tickers*.

    Parameters
    ----------
    tickers: list of ticker symbols (e.g. ["AAPL", "MSFT"]).
    start, end: ISO‑format dates ("YYYY‑MM‑DD").
    interval: Data frequency accepted by yFinance (default "1d").

    Returns
    -------
    DataFrame with dates as the index and tickers as columns.
    """
    data = yf.download(tickers, start=start, end=end, interval=interval, progress=False)
    # yFinance returns a multi‑level column when multiple fields are requested.
    # We only need the Adjusted Close price.
    if isinstance(data.columns, pd.MultiIndex):
        # Try common price levels
        if "Adj Close" in data.columns.get_level_values(1):
            price = data["Adj Close"]
        elif "Close" in data.columns.get_level_values(1):
            price = data["Close"]
        else:
            price = data
    else:
        if "Adj Close" in data.columns:
            price = data["Adj Close"]
        elif "Close" in data.columns:
            price = data["Close"]
        else:
            price = data
    price = price.dropna(how="all")  # drop rows where all tickers are NaN
    # Forward‑fill missing values, then drop any ticker that still has NaNs.
    price = price.ffill().bfill()
    price = price.dropna(axis=1, how="any")
    return price


# ---------------------------------------------------------------------------
# Return & risk calculations
# ---------------------------------------------------------------------------


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute simple daily returns from price series.

    Returns a DataFrame of the same shape (minus the first row) where each
    element is ``(P_t / P_{t-1}) - 1``.
    """
    returns = prices.pct_change().dropna()
    return returns


def annualised_statistics(
    weights: np.ndarray,
    returns: pd.DataFrame,
    cov_matrix: np.ndarray,
    periods_per_year: int = 252,
) -> Tuple[float, float, float]:
    """Calculate portfolio expected return, volatility and Sharpe ratio.

    Parameters
    ----------
    weights: array‑like, shape (n_assets,)
    returns: DataFrame of daily returns.
    cov_matrix: covariance matrix of daily returns.
    periods_per_year: trading days per year (default 252).

    Returns
    -------
    (exp_return, volatility, sharpe)
    """
    exp_daily_ret = np.dot(weights, returns.mean())
    exp_annual_ret = (1 + exp_daily_ret) ** periods_per_year - 1
    vol_daily = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    vol_annual = vol_daily * np.sqrt(periods_per_year)
    sharpe = exp_annual_ret / vol_annual if vol_annual != 0 else 0.0
    return exp_annual_ret, vol_annual, sharpe


def portfolio_metrics(weights: np.ndarray, returns: pd.DataFrame) -> Dict[str, float]:
    """Convenient wrapper returning a dict of common metrics."""
    cov = returns.cov().values
    exp_ret, vol, sharpe = annualised_statistics(weights, returns, cov)
    return {"return": exp_ret, "volatility": vol, "sharpe": sharpe}


# ---------------------------------------------------------------------------
# Optimization helpers
# ---------------------------------------------------------------------------


def _portfolio_variance(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    return np.dot(weights.T, np.dot(cov_matrix, weights))


def _negative_sharpe(
    weights: np.ndarray,
    returns: pd.DataFrame,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.0,
) -> float:
    port_ret, port_vol, _ = annualised_statistics(weights, returns, cov_matrix)
    sharpe = (port_ret - risk_free_rate) / port_vol if port_vol != 0 else 0.0
    return -sharpe


def _weight_sum_constraint(weights: np.ndarray) -> float:
    return np.sum(weights) - 1.0


def minimum_variance_portfolio(cov_matrix: np.ndarray) -> np.ndarray:
    """Return the weight vector of the global minimum‑variance portfolio.

    The optimisation is a simple quadratic problem with the only constraint
    that the weights sum to 1 and are non‑negative (no short‑selling).
    """
    n = cov_matrix.shape[0]
    init = np.ones(n) / n
    bounds = [(0.0, 1.0) for _ in range(n)]
    constraints = [{"type": "eq", "fun": _weight_sum_constraint}]
    result = minimize(
        _portfolio_variance,
        init,
        args=(cov_matrix,),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    if not result.success:
        raise RuntimeError("Minimum variance optimisation failed: " + result.message)
    return result.x


def maximum_sharpe_portfolio(
    returns: pd.DataFrame, cov_matrix: np.ndarray, risk_free_rate: float = 0.0
) -> np.ndarray:
    """Return the weight vector that maximises the Sharpe ratio.

    Short‑selling is prohibited by default (bounds 0‑1). Adjust ``bounds`` if
    you need a different policy.
    """
    n = cov_matrix.shape[0]
    init = np.ones(n) / n
    bounds = [(0.0, 1.0) for _ in range(n)]
    constraints = [{"type": "eq", "fun": _weight_sum_constraint}]
    result = minimize(
        _negative_sharpe,
        init,
        args=(returns, cov_matrix, risk_free_rate),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    if not result.success:
        raise RuntimeError("Maximum Sharpe optimisation failed: " + result.message)
    return result.x


def risk_constrained_portfolio(
    returns: pd.DataFrame,
    cov_matrix: np.ndarray,
    target_vol: float,
    risk_free_rate: float = 0.0,
) -> np.ndarray:
    """Portfolio with volatility closest to *target_vol* while maximising Sharpe.

    The optimisation adds an equality constraint on portfolio volatility.
    """
    n = cov_matrix.shape[0]
    init = np.ones(n) / n
    bounds = [(0.0, 1.0) for _ in range(n)]
    constraints = [
        {"type": "eq", "fun": _weight_sum_constraint},
        {
            "type": "eq",
            "fun": lambda w: np.sqrt(_portfolio_variance(w, cov_matrix)) - target_vol,
        },
    ]
    result = minimize(
        _negative_sharpe,
        init,
        args=(returns, cov_matrix, risk_free_rate),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    if not result.success:
        raise RuntimeError("Risk‑constrained optimisation failed: " + result.message)
    return result.x


# ---------------------------------------------------------------------------
# Rolling‑window analysis
# ---------------------------------------------------------------------------


def rolling_window_weights(
    prices: pd.DataFrame,
    window: int,
    step: int,
    optimisation: str = "max_sharpe",
    **opt_kwargs,
) -> pd.DataFrame:
    """Compute optimal weights over a rolling window.

    Parameters
    ----------
    prices: price DataFrame.
    window: number of days in each rolling window.
    step: days to step forward between successive windows.
    optimisation: ``"min_var"``, ``"max_sharpe"`` or ``"risk_constrained"``.
    **opt_kwargs: additional arguments forwarded to the optimisation function.

    Returns
    -------
    DataFrame indexed by the *window end date* with one column per asset.
    """
    dates = prices.index
    results = []
    for start_idx in range(0, len(dates) - window + 1, step):
        end_idx = start_idx + window
        window_prices = prices.iloc[start_idx:end_idx]
        rets = compute_returns(window_prices)
        cov = rets.cov().values
        if optimisation == "min_var":
            w = minimum_variance_portfolio(cov)
        elif optimisation == "max_sharpe":
            w = maximum_sharpe_portfolio(rets, cov, **opt_kwargs)
        elif optimisation == "risk_constrained":
            w = risk_constrained_portfolio(rets, cov, **opt_kwargs)
        else:
            raise ValueError(f"Unsupported optimisation mode: {optimisation}")
        results.append((window_prices.index[-1], w))
    weights_df = pd.DataFrame(
        data=[w for _, w in results],
        index=[d for d, _ in results],
        columns=prices.columns,
    )
    return weights_df


# ---------------------------------------------------------------------------
# Visualisation helpers
# ---------------------------------------------------------------------------


def plot_efficient_frontier(
    returns: pd.DataFrame,
    cov_matrix: np.ndarray,
    num_points: int = 50,
    risk_free_rate: float = 0.0,
) -> None:
    """Plot the efficient frontier.

    The function solves a series of quadratic programmes that minimise variance
    for a given target return.
    """
    n = cov_matrix.shape[0]
    mu = returns.mean().values
    target_returns = np.linspace(mu.min(), mu.max(), num_points)
    frontier_vol = []
    for target in target_returns:
        # minimise variance subject to expected return == target
        constraints = [
            {"type": "eq", "fun": lambda w: np.dot(w, mu) - target},
            {"type": "eq", "fun": _weight_sum_constraint},
        ]
        bounds = [(0.0, 1.0) for _ in range(n)]
        init = np.ones(n) / n
        result = minimize(
            _portfolio_variance,
            init,
            args=(cov_matrix,),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if result.success:
            vol = np.sqrt(_portfolio_variance(result.x, cov_matrix)) * np.sqrt(252)
            frontier_vol.append(vol)
        else:
            frontier_vol.append(np.nan)
    plt.figure(figsize=(8, 5))
    plt.plot(frontier_vol, target_returns, "-o", label="Efficient Frontier")
    # Plot the two classic portfolios for reference
    min_var_w = minimum_variance_portfolio(cov_matrix)
    mv_ret, mv_vol, _ = annualised_statistics(min_var_w, returns, cov_matrix)
    plt.scatter(mv_vol, mv_ret, color="red", marker="*", s=200, label="Min‑Var")
    max_sharpe_w = maximum_sharpe_portfolio(returns, cov_matrix, risk_free_rate)
    ms_ret, ms_vol, _ = annualised_statistics(max_sharpe_w, returns, cov_matrix)
    plt.scatter(ms_vol, ms_ret, color="green", marker="*", s=200, label="Max‑Sharpe")
    plt.xlabel("Annualised Volatility")
    plt.ylabel("Annualised Return")
    plt.title("Efficient Frontier")
    plt.legend()
    plt.grid(True)
    plt.show()


# ---------------------------------------------------------------------------
# Example usage (executed when run as script)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Example tickers – feel free to customise
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TLT", "GLD"]
    price_df = download_price_data(tickers, start="2018-01-01", end="2023-12-31")
    returns_df = compute_returns(price_df)
    cov_mat = returns_df.cov().values

    # Minimum variance portfolio
    w_min = minimum_variance_portfolio(cov_mat)
    print("Minimum‑variance weights:")
    for t, w in zip(tickers, w_min):
        print(f"  {t}: {w:.3%}")

    # Maximum Sharpe portfolio (assume 0% risk‑free rate)
    w_max = maximum_sharpe_portfolio(returns_df, cov_mat, risk_free_rate=0.0)
    print("\nMaximum‑Sharpe weights:")
    for t, w in zip(tickers, w_max):
        print(f"  {t}: {w:.3%}")

    # Plot efficient frontier
    plot_efficient_frontier(returns_df, cov_mat, num_points=30)

    # Rolling‑window demonstration (60‑day window, 30‑day step)
    rw = rolling_window_weights(price_df, window=60, step=30, optimisation="max_sharpe")
    print("\nRolling‑window latest weights (max Sharpe):")
    print(rw.tail(1).T)


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
# Configure a basic root logger only if no handlers are already present.
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s"
    )
