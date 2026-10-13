"""HTTP API and static frontend host for the portfolio optimizer."""

import logging
import os
from datetime import date
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .portfolio_optimizer import (
    compute_correlation_matrix,
    compute_returns,
    download_price_data,
    historical_stress_test,
    maximum_drawdown,
    maximum_sharpe_portfolio,
    minimum_variance_portfolio,
    risk_constrained_portfolio,
    value_at_risk,
)

logger = logging.getLogger(__name__)
app = FastAPI(title="Portfolio Optimization API", version="1.0.0")


class AnalysisRequest(BaseModel):
    tickers: list[str] = Field(min_length=2, max_length=10)
    start: date
    end: date
    strategy: Literal["min_variance", "max_sharpe", "risk_constrained"] = "max_sharpe"
    risk_free_rate: float = Field(default=0.02, ge=0.0, le=0.25)
    target_volatility: float | None = Field(default=None, gt=0.0, le=1.0)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(request: AnalysisRequest) -> dict:
    tickers = list(dict.fromkeys(ticker.strip().upper() for ticker in request.tickers))
    if len(tickers) < 2 or any(not ticker for ticker in tickers):
        raise HTTPException(
            status_code=422, detail="Enter at least two unique tickers."
        )
    if request.start >= request.end:
        raise HTTPException(
            status_code=422, detail="Start date must be before end date."
        )
    if request.strategy == "risk_constrained" and request.target_volatility is None:
        raise HTTPException(
            status_code=422,
            detail="A target volatility is required for risk-constrained optimization.",
        )

    try:
        prices = download_price_data(
            tickers,
            start=request.start.isoformat(),
            end=request.end.isoformat(),
        )
    except Exception as exc:
        logger.exception("Market data download failed")
        raise HTTPException(
            status_code=502,
            detail=(
                "Market data provider request failed. "
                "Check the symbols and try again."
            ),
        ) from exc

    missing = [ticker for ticker in tickers if ticker not in prices.columns]
    if prices.empty or missing:
        detail = "No usable market data was returned."
        if missing:
            detail = "No market data returned for: " f"{', '.join(missing)}."
        raise HTTPException(status_code=422, detail=detail)

    returns = compute_returns(prices)
    if len(returns) < 2:
        raise HTTPException(status_code=422, detail="Not enough history for analysis.")

    covariance = returns.cov().to_numpy()
    if request.strategy == "min_variance":
        weights = minimum_variance_portfolio(covariance)
    elif request.strategy == "risk_constrained":
        target_daily_volatility = request.target_volatility / np.sqrt(252)
        try:
            weights = risk_constrained_portfolio(
                returns,
                covariance,
                target_vol=target_daily_volatility,
                risk_free_rate=request.risk_free_rate,
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=422,
                detail="That volatility target is not feasible for this history.",
            ) from exc
    else:
        weights = maximum_sharpe_portfolio(
            returns,
            covariance,
            risk_free_rate=request.risk_free_rate,
        )

    portfolio_returns = pd.Series(
        returns.to_numpy() @ weights,
        index=returns.index,
        name="portfolio",
    )
    benchmark_returns = returns.mean(axis=1)
    portfolio_values = 100.0 * (1.0 + portfolio_returns).cumprod()
    benchmark_values = 100.0 * (1.0 + benchmark_returns).cumprod()

    annual_return = float((1.0 + portfolio_returns.mean()) ** 252 - 1.0)
    annual_volatility = float(np.sqrt(weights @ covariance @ weights) * np.sqrt(252))
    sharpe_ratio = (
        (annual_return - request.risk_free_rate) / annual_volatility
        if annual_volatility > 0
        else 0.0
    )
    stress = historical_stress_test(
        portfolio_values.to_frame(), window=min(21, len(portfolio_values))
    )
    correlation = compute_correlation_matrix(returns)
    if request.strategy == "min_variance":
        strategy_note = (
            "Minimum variance prioritizes the lowest estimated portfolio "
            "volatility; it does not target a return level."
        )
    elif request.strategy == "risk_constrained":
        strategy_note = (
            "Risk-constrained optimization targets "
            f"{request.target_volatility:.1%} annual volatility while "
            "maximizing historical Sharpe ratio."
        )
    else:
        strategy_note = (
            "Maximum Sharpe prioritizes historical excess return per unit of "
            f"risk, using a {request.risk_free_rate:.1%} risk-free rate."
        )
    largest_index = int(np.argmax(weights))
    largest_weight = float(weights[largest_index])
    largest_ticker = str(prices.columns[largest_index])
    effective_holdings = float(1.0 / np.square(weights).sum())
    pairwise_correlations = correlation.to_numpy()[
        np.triu_indices(len(correlation.columns), k=1)
    ]
    average_correlation = (
        float(np.abs(pairwise_correlations).mean())
        if pairwise_correlations.size
        else 0.0
    )
    maximum_drawdown_value = float(maximum_drawdown(portfolio_values))

    recommendations = [
        {
            "category": "strategy",
            "severity": "info",
            "title": "Optimization objective",
            "detail": strategy_note,
        },
        {
            "category": "concentration",
            "severity": "caution" if largest_weight >= 0.4 else "info",
            "title": (
                "Single-name concentration"
                if largest_weight >= 0.4
                else "Allocation breadth"
            ),
            "detail": (
                f"{largest_ticker} has the largest weight at {largest_weight:.1%}. "
                f"The allocation has approximately {effective_holdings:.1f} "
                "effective holdings; concentrated weights can make results more "
                "sensitive to one asset's history."
            ),
        },
        {
            "category": "diversification",
            "severity": "caution" if average_correlation >= 0.75 else "info",
            "title": "Historical co-movement",
            "detail": (
                f"Average absolute pairwise correlation is "
                f"{average_correlation:.2f}. "
                + (
                    "The assets moved closely together in this sample, which may "
                    "limit diversification."
                    if average_correlation >= 0.75
                    else "Use this historical relationship as context, not a "
                    "guarantee of future diversification."
                )
            ),
        },
        {
            "category": "downside",
            "severity": "caution" if stress["stress_regime"] else "info",
            "title": (
                "Historical stress flag"
                if stress["stress_regime"]
                else "Historical downside"
            ),
            "detail": (
                f"Maximum drawdown was {maximum_drawdown_value:.1%}; the worst "
                f"rolling window returned {stress['worst_window_return']:.1%}. "
                + (
                    "The sample crossed the 5% stress threshold; review whether "
                    "that loss profile fits your stated risk tolerance."
                    if stress["stress_regime"]
                    else "No measured window crossed the 5% stress threshold."
                )
            ),
        },
    ]
    rolling_volatility = portfolio_returns.rolling(21, min_periods=2).std() * np.sqrt(
        252
    )

    return {
        "metadata": {
            "tickers": tickers,
            "start": request.start.isoformat(),
            "end": request.end.isoformat(),
            "observations": len(returns),
            "strategy": request.strategy,
        },
        "metrics": {
            "annual_return": annual_return,
            "annual_volatility": annual_volatility,
            "sharpe_ratio": sharpe_ratio,
            "daily_var_95": float(value_at_risk(portfolio_returns, confidence=0.95)),
            "maximum_drawdown": float(maximum_drawdown(portfolio_values)),
        },
        "weights": [
            {"ticker": ticker, "weight": float(weight)}
            for ticker, weight in zip(prices.columns, weights)
        ],
        "history": [
            {
                "date": timestamp.date().isoformat(),
                "portfolio": float(portfolio_value),
                "benchmark": float(benchmark_value),
                "rolling_volatility": (
                    float(rolling_volatility.loc[timestamp])
                    if pd.notna(rolling_volatility.loc[timestamp])
                    else None
                ),
            }
            for timestamp, portfolio_value, benchmark_value in zip(
                portfolio_values.index, portfolio_values, benchmark_values
            )
        ],
        "correlation": {
            "tickers": correlation.columns.tolist(),
            "matrix": correlation.to_numpy().tolist(),
        },
        "stress": {
            "worst_window_return": float(stress["worst_window_return"]),
            "worst_drawdown": float(stress["worst_drawdown"]),
            "stress_regime": bool(stress["stress_regime"]),
            "window_start": stress["stress_window_start"].isoformat(),
            "window_end": stress["stress_window_end"].isoformat(),
        },
        "recommendations": recommendations,
        "disclaimer": (
            "Model interpretations describe historical data and are not "
            "personalized investment advice or instructions to trade."
        ),
    }


frontend_dir = Path(
    os.environ.get(
        "PORTFOLIO_STATIC_DIR",
        Path(__file__).resolve().parents[1] / "frontend" / "dist",
    )
)
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
