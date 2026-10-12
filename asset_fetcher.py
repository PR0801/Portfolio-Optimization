# asset_fetcher.py
"""Placeholder module for extended asset data fetching.

Future extensions could provide:
* Futures and options price series (via `yfinance` or dedicated APIs)
* Crypto assets (via `ccxt`)
* Custom CSV or database sources

The current implementation offers a simple wrapper that raises
`NotImplementedError` for unsupported asset types, making it easy to
extend without breaking existing functionality.
"""

from typing import List

def fetch_asset_data(tickers: List[str], start: str, end: str, asset_type: str = "equity"):
    """Fetch price data for the given *asset_type*.

    Parameters
    ----------
    tickers: list of symbols
    start, end: date strings (YYYY‑MM‑DD)
    asset_type: ``"equity"`` (default), ``"future"``, ``"option"``, ``"crypto"``

    Returns
    -------
    pandas.DataFrame with a DateTime index and one column per ticker.

    Notes
    -----
    Only ``"equity"`` is currently supported. Other types raise
    ``NotImplementedError`` so callers can handle them explicitly.
    """
    if asset_type != "equity":
        raise NotImplementedError(
            f"Asset type '{asset_type}' is not yet implemented. Extend "
            "asset_fetcher.py to add support."
        )
    # Defer to the existing portfolio optimizer download function.
    from .portfolio_optimizer import download_price_data

    return download_price_data(tickers, start=start, end=end)
