# cli.py
"""Command-line interface for the portfolio optimisation toolbox.

Usage example::

    python -m portfolio_optimization.cli \
        --tickers AAPL MSFT GOOGL AMZN TLT GLD \
        --start 2019-01-01 --end 2024-12-31 \
        --optimisation max_sharpe

The CLI supports three optimisation modes:
* ``min_var`` - minimum-variance portfolio
* ``max_sharpe`` - maximum-Sharpe portfolio (risk-free rate defaults to 0)
* ``risk_constrained`` - target volatility (provide ``--target-vol``)

Additional flags allow you to export the resulting weights to CSV, plot the efficient frontier, or run a rolling-window analysis.
"""

import argparse
import sys
from datetime import datetime

# Package-relative imports
from .portfolio_optimizer import (
    download_price_data,
    compute_returns,
    minimum_variance_portfolio,
    maximum_sharpe_portfolio,
    risk_constrained_portfolio,
    rolling_window_weights,
    plot_efficient_frontier,
    portfolio_metrics,
    logger,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="portfolio-optimiser",
        description="Modern Portfolio Theory based optimiser",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        required=True,
        help="List of ticker symbols (e.g. AAPL MSFT GOOGL)",
    )
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--interval",
        default="1d",
        help="yFinance interval (default: 1d)",
    )
    parser.add_argument(
        "--optimisation",
        choices=["min_var", "max_sharpe", "risk_constrained"],
        default="max_sharpe",
        help="Optimisation mode (default: max_sharpe)",
    )
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        default=0.0,
        help="Risk-free rate for Sharpe calculation (default: 0.0)",
    )
    parser.add_argument(
        "--target-vol",
        type=float,
        default=None,
        help="Target annualised volatility for risk-constrained optimisation",
    )
    parser.add_argument(
        "--rolling-window",
        action="store_true",
        help="Run rolling-window analysis (60-day window, 30-day step)",
    )
    parser.add_argument(
        "--export-weights",
        metavar="FILE",
        help="Export the final weights to a CSV file",
    )
    parser.add_argument(
        "--plot-frontier",
        action="store_true",
        help="Plot the efficient frontier after optimisation",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logger.info("Downloading price data for %s", ", ".join(args.tickers))
    try:
        prices = download_price_data(
            args.tickers, start=args.start, end=args.end, interval=args.interval
        )
    except Exception as exc:
        logger.error("Failed to download price data: %s", exc)
        return 1

    returns = compute_returns(prices)
    cov = returns.cov().values

    # Choose optimisation
    if args.optimisation == "min_var":
        logger.info("Running minimum-variance optimisation")
        weights = minimum_variance_portfolio(cov)
    elif args.optimisation == "max_sharpe":
        logger.info(
            "Running maximum-Sharpe optimisation (risk-free rate=%s)", args.risk_free_rate
        )
        weights = maximum_sharpe_portfolio(returns, cov, risk_free_rate=args.risk_free_rate)
    else:  # risk_constrained
        if args.target_vol is None:
            logger.error("--target-vol is required for risk_constrained optimisation")
            return 1
        logger.info(
            "Running risk-constrained optimisation (target_vol=%.2f)", args.target_vol
        )
        weights = risk_constrained_portfolio(
            returns, cov, target_vol=args.target_vol, risk_free_rate=args.risk_free_rate
        )

    # Show results
    metrics = portfolio_metrics(weights, returns)
    logger.info("Optimised portfolio metrics: %s", metrics)
    for t, w in zip(args.tickers, weights):
        logger.info("%s: %.2f%%", t, w * 100)

    if args.export_weights:
        import pandas as pd

        df = pd.DataFrame({"Ticker": args.tickers, "Weight": weights})
        df.to_csv(args.export_weights, index=False)
        logger.info("Weights exported to %s", args.export_weights)

    if args.plot_frontier:
        plot_efficient_frontier(returns, cov, num_points=30)

    if args.rolling_window:
        rw = rolling_window_weights(
            prices, window=60, step=30, optimisation=args.optimisation, risk_free_rate=args.risk_free_rate
        )
        logger.info("Latest rolling-window weights (%.2f%%):", rw.tail(1).iloc[0].sum() * 100)
        logger.info("%s", rw.tail(1).T)

    return 0

if __name__ == "__main__":
    sys.exit(main())
