# tests/test_portfolio_optimizer.py
"""Basic unit tests for the portfolio optimisation toolkit.

These tests use synthetic data so they run quickly and deterministically.
"""

import pandas as pd
import pytest

from portfolio_optimization import (
    compute_returns,
    minimum_variance_portfolio,
    maximum_sharpe_portfolio,
    risk_constrained_portfolio,
)


# Helper synthetic data – two assets with known statistics
@pytest.fixture
def synthetic_prices():
    dates = pd.date_range(start="2020-01-01", periods=5, freq="D")
    data = {
        "A": [100, 101, 102, 103, 104],
        "B": [200, 202, 201, 206, 204],
    }
    return pd.DataFrame(data, index=dates)


def test_compute_returns(synthetic_prices):
    returns = compute_returns(synthetic_prices)
    # Returns should have one fewer row than prices
    assert len(returns) == len(synthetic_prices) - 1
    # Simple check: first return for A is (101/100)-1 = 0.01
    assert pytest.approx(returns.iloc[0]["A"], rel=1e-6) == 0.01


def test_minimum_variance_portfolio(synthetic_prices):
    returns = compute_returns(synthetic_prices)
    cov = returns.cov().values
    weights = minimum_variance_portfolio(cov)
    # Weights must sum to 1 and be non‑negative
    assert pytest.approx(weights.sum(), rel=1e-6) == 1.0
    assert all(w >= 0 for w in weights)


def test_maximum_sharpe_portfolio(synthetic_prices):
    returns = compute_returns(synthetic_prices)
    cov = returns.cov().values
    weights = maximum_sharpe_portfolio(returns, cov, risk_free_rate=0.0)
    assert pytest.approx(weights.sum(), rel=1e-6) == 1.0
    assert all(w >= 0 for w in weights)


def test_risk_constrained_portfolio(synthetic_prices):
    returns = compute_returns(synthetic_prices)
    cov = returns.cov().values
    # Target a modest volatility
    target_vol = 0.01
    weights = risk_constrained_portfolio(
        returns, cov, target_vol=target_vol, risk_free_rate=0.0
    )
    assert pytest.approx(weights.sum(), rel=1e-6) == 1.0
    assert all(w >= 0 for w in weights)
