# tests/test_portfolio_optimizer.py
"""Basic unit tests for the portfolio optimisation toolkit.

These tests use synthetic data so they run quickly and deterministically.
"""

import pandas as pd
import pytest

from portfolio_optimization import (
    compute_returns,
    compute_correlation_matrix,
    value_at_risk,
    maximum_drawdown,
    historical_stress_test,
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


def test_compute_correlation_matrix(synthetic_prices):
    returns = compute_returns(synthetic_prices)
    corr = compute_correlation_matrix(returns)
    assert corr.shape == (2, 2)
    assert corr.loc["A", "A"] == pytest.approx(1.0)
    assert corr.loc["B", "B"] == pytest.approx(1.0)


def test_value_at_risk_and_maximum_drawdown():
    returns = pd.Series([-0.10, -0.05, 0.02, 0.03, -0.12, 0.01])
    assert value_at_risk(returns, confidence=0.95) == pytest.approx(0.10, rel=1e-6)

    prices = pd.Series([100.0, 110.0, 90.0, 95.0, 80.0])
    assert maximum_drawdown(prices) == pytest.approx(0.2727272727, rel=1e-6)


def test_historical_stress_test():
    prices = pd.DataFrame(
        {
            "A": [100, 110, 105, 98, 90, 85, 95, 88],
            "B": [100, 102, 101, 99, 92, 90, 87, 84],
        },
        index=pd.date_range("2020-01-01", periods=8, freq="D"),
    )
    stress = historical_stress_test(prices, window=3, threshold=0.05)
    assert "worst_window_return" in stress
    assert "worst_drawdown" in stress
    assert "stress_regime" in stress
    assert stress["stress_regime"] is True
