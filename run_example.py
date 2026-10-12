# run_example.py
"""Convenient script to demonstrate the portfolio optimisation toolkit.

Run with:
    python run_example.py
"""

from portfolio_optimizer import (
    download_price_data,
    compute_returns,
    minimum_variance_portfolio,
    maximum_sharpe_portfolio,
    rolling_window_weights,
    plot_efficient_frontier,
)

if __name__ == "__main__":
    # Define a set of assets – you can replace these with any tickers you like.
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TLT", "GLD"]
    # Download adjusted close prices for the last 5 years.
    price_df = download_price_data(tickers, start="2019-01-01", end="2024-12-31")
    returns_df = compute_returns(price_df)
    cov_mat = returns_df.cov().values

    # Minimum‑variance portfolio
    w_min = minimum_variance_portfolio(cov_mat)
    print("Minimum‑variance portfolio weights:")
    for t, w in zip(tickers, w_min):
        print(f"  {t}: {w:.2%}")

    # Maximum‑Sharpe portfolio (assume risk‑free rate of 0%)
    w_max = maximum_sharpe_portfolio(returns_df, cov_mat, risk_free_rate=0.0)
    print("\nMaximum‑Sharpe portfolio weights:")
    for t, w in zip(tickers, w_max):
        print(f"  {t}: {w:.2%}")

    # Plot the efficient frontier for visual inspection
    plot_efficient_frontier(returns_df, cov_mat, num_points=30)

    # Rolling‑window analysis – 60‑day window, step every 30 days
    rw_weights = rolling_window_weights(price_df, window=60, step=30, optimisation="max_sharpe")
    print("\nLatest rolling‑window weights (max Sharpe):")
    print(rw_weights.tail(1).T)
