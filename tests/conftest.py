"""
Test Fixtures and Mocks
========================
Shared fixtures for all tests.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_stock_response():
    """Sample successful stock analysis response."""
    return {
        "sembol": "NVDA",
        "fiyat": 186.5,
        "degisim": "+3.7%",
        "volatilite": "2.9%",
        "rsi": 51.0,
        "sinyal": "TUT",
        "periyot": "1mo",
        "isim": "NVIDIA Corporation"
    }


@pytest.fixture
def sample_commodity_response():
    """Sample commodity (bakır) response."""
    return {
        "sembol": "HG",
        "fiyat": 4.52,
        "degisim": "+2.1%",
        "volatilite": "3.0%",
        "rsi": 45.0,
        "sinyal": "TUT",
        "periyot": "1mo",
        "isim": "Copper Mar 26"
    }


@pytest.fixture
def sample_bist_response():
    """Sample BIST stock response."""
    return {
        "sembol": "EREGL",
        "fiyat": 23.82,
        "degisim": "-0.7%",
        "volatilite": "1.4%",
        "rsi": 63.0,
        "sinyal": "TUT",
        "periyot": "1mo",
        "piyasa_degeri": "160.1B",
        "isim": "EREGLI DEMIR CELIK"
    }


@pytest.fixture
def sample_error_response():
    """Sample error response."""
    return {
        "err": "Veri bulunamadı: 'xyz' (sembol: XYZ). Lütfen geçerli bir hisse/emtia/kripto adı veya sembolü deneyin.",
        "tried_symbol": "XYZ",
        "suggestion": "web_search ile doğru sembolü arayın"
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_yfinance():
    """Mock yfinance Ticker."""
    with patch('yfinance.Ticker') as mock:
        ticker_instance = MagicMock()
        
        # Mock history data
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start='2025-12-01', periods=20, freq='D')
        mock_history = pd.DataFrame({
            'Open': np.random.uniform(100, 110, 20),
            'High': np.random.uniform(110, 120, 20),
            'Low': np.random.uniform(90, 100, 20),
            'Close': np.linspace(100, 105, 20),  # Slight uptrend
            'Volume': np.random.randint(1000000, 5000000, 20)
        }, index=dates)
        
        ticker_instance.history.return_value = mock_history
        ticker_instance.info = {
            "shortName": "Test Stock",
            "trailingPE": 25.5,
            "marketCap": 100000000000
        }
        
        mock.return_value = ticker_instance
        yield mock


@pytest.fixture
def mock_empty_yfinance():
    """Mock yfinance that returns empty data."""
    with patch('yfinance.Ticker') as mock:
        ticker_instance = MagicMock()
        
        import pandas as pd
        ticker_instance.history.return_value = pd.DataFrame()
        ticker_instance.info = {}
        
        mock.return_value = ticker_instance
        yield mock


@pytest.fixture
def mock_ddgs():
    """Mock DuckDuckGo search."""
    with patch('ddgs.DDGS') as mock:
        ddgs_instance = MagicMock()
        ddgs_instance.__enter__ = MagicMock(return_value=ddgs_instance)
        ddgs_instance.__exit__ = MagicMock(return_value=False)
        ddgs_instance.text.return_value = [
            {
                "title": "EREGL.IS Ereğli Demir Çelik",
                "body": "Ereğli Demir ve Çelik Fabrikaları hisse senedi EREGL.IS",
                "href": "https://example.com"
            }
        ]
        mock.return_value = ddgs_instance
        yield mock


# =============================================================================
# QUERY FIXTURES
# =============================================================================

@pytest.fixture
def valid_queries():
    """Valid test queries."""
    return [
        ("nvidia", "NVDA"),
        ("bitcoin", "BTC-USD"),
        ("altın", "GC=F"),
        ("bakır", "HG=F"),
        ("AAPL", "AAPL"),
        ("THYAO.IS", "THYAO.IS"),
        ("ereğli", None),  # Should use web search
    ]


@pytest.fixture
def invalid_queries():
    """Invalid/edge case queries."""
    return [
        "",           # Empty
        "asdfghjkl",  # Random
        "12345",      # Numbers only
        "   ",        # Whitespace
    ]
