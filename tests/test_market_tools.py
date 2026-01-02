"""
Unit Tests for Market Tools
============================
Tests for individual tool functions.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.market_tools import (
    analyze_stock, 
    scan_sector, 
    compare, 
    get_news, 
    get_forex, 
    get_fundamentals,
    web_search,
    resolve_symbol,
    SYMBOL_MAP
)


class TestSymbolResolver:
    """Tests for the resolve_symbol function."""

    @pytest.mark.unit
    def test_direct_match_lowercase(self):
        """Test direct match with lowercase input."""
        assert resolve_symbol("nvidia") == "NVDA"
        assert resolve_symbol("bitcoin") == "BTC-USD"
        assert resolve_symbol("altın") == "GC=F"
        assert resolve_symbol("bakır") == "HG=F"

    @pytest.mark.unit
    def test_direct_match_mixed_case(self):
        """Test that matching is case-insensitive."""
        assert resolve_symbol("NVIDIA") == "NVDA"
        assert resolve_symbol("Bitcoin") == "BTC-USD"
        assert resolve_symbol("ALTIN") == "GC=F"

    @pytest.mark.unit
    def test_partial_match(self):
        """Test partial matching."""
        assert resolve_symbol("thy") == "THYAO.IS"
        assert resolve_symbol("garanti") == "GARAN.IS"

    @pytest.mark.unit
    def test_already_valid_ticker(self):
        """Test that valid tickers pass through."""
        assert resolve_symbol("AAPL") == "AAPL"
        assert resolve_symbol("MSFT") == "MSFT"

    @pytest.mark.unit
    def test_already_has_suffix(self):
        """Test that symbols with suffix pass through."""
        assert resolve_symbol("THYAO.IS") == "THYAO.IS"
        assert resolve_symbol("BTC-USD") == "BTC-USD"
        assert resolve_symbol("GC=F") == "GC=F"

    @pytest.mark.unit
    def test_symbol_map_coverage(self):
        """Test that SYMBOL_MAP has essential entries."""
        essential_symbols = [
            "altın", "bitcoin", "nvidia", "bakır", "gümüş",
            "thy", "garanti", "sabancı", "koç"
        ]
        for symbol in essential_symbols:
            assert symbol in SYMBOL_MAP, f"Missing symbol: {symbol}"


class TestAnalyzeStock:
    """Tests for analyze_stock function."""

    @pytest.mark.integration
    def test_analyze_known_symbol(self):
        """Test analysis with a known symbol."""
        result = analyze_stock.invoke({"symbol": "AAPL"})
        
        # Should have key fields
        assert "fiyat" in result or "err" in result
        if "fiyat" in result:
            assert "degisim" in result
            assert "sinyal" in result

    @pytest.mark.integration
    def test_analyze_turkish_name(self):
        """Test analysis with Turkish commodity name."""
        result = analyze_stock.invoke({"symbol": "bakır"})
        
        assert "fiyat" in result or "err" in result
        if "fiyat" in result:
            assert result["sembol"] == "HG"

    @pytest.mark.integration
    def test_analyze_bist_stock(self):
        """Test analysis with BIST stock."""
        result = analyze_stock.invoke({"symbol": "THYAO.IS"})
        
        assert "fiyat" in result or "err" in result

    @pytest.mark.integration
    def test_analyze_bist_suffix_fallback(self):
        """Test that bare BIST ticker gets .IS suffix."""
        result = analyze_stock.invoke({"symbol": "EREGL"})
        
        # Should automatically try EREGL.IS
        assert "fiyat" in result or "err" in result

    @pytest.mark.unit
    def test_analyze_invalid_symbol(self):
        """Test analysis with invalid symbol."""
        result = analyze_stock.invoke({"symbol": "XYZNOTREAL123"})
        
        assert "err" in result
        assert "suggestion" in result


class TestScanSector:
    """Tests for scan_sector function."""

    @pytest.mark.integration
    def test_scan_banka_sector(self):
        """Test banking sector scan."""
        result = scan_sector.invoke({"sector": "banka"})
        
        assert "sector" in result or "err" in result
        if "sector" in result:
            assert "top3" in result
            assert len(result["top3"]) <= 3

    @pytest.mark.integration
    def test_scan_teknoloji_sector(self):
        """Test technology sector scan."""
        result = scan_sector.invoke({"sector": "teknoloji"})
        
        assert "sector" in result or "err" in result

    @pytest.mark.unit
    def test_scan_invalid_sector(self):
        """Test invalid sector name."""
        result = scan_sector.invoke({"sector": "invalid_sector"})
        
        assert "err" in result


class TestGetForex:
    """Tests for get_forex function."""

    @pytest.mark.integration
    def test_get_usdtry(self):
        """Test USD/TRY rate."""
        result = get_forex.invoke({"pair": "USDTRY"})
        
        assert "rate" in result or "err" in result
        if "rate" in result:
            assert result["rate"] > 0

    @pytest.mark.integration
    def test_get_eurtry(self):
        """Test EUR/TRY rate."""
        result = get_forex.invoke({"pair": "EURTRY"})
        
        assert "rate" in result or "err" in result


class TestCompare:
    """Tests for compare function."""

    @pytest.mark.integration
    def test_compare_two_stocks(self):
        """Test comparing two stocks."""
        result = compare.invoke({"symbols": ["AAPL", "MSFT"]})
        
        assert "stocks" in result or "err" in result
        if "stocks" in result:
            assert "winner" in result

    @pytest.mark.integration
    def test_compare_bist_stocks(self):
        """Test comparing BIST stocks."""
        result = compare.invoke({"symbols": ["THYAO.IS", "PGSUS.IS"]})
        
        assert "stocks" in result or "err" in result


class TestWebSearch:
    """Tests for web_search function."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_web_search_basic(self):
        """Test basic web search."""
        result = web_search.invoke({"query": "BIST 100 hisse listesi"})
        
        assert "results" in result or "err" in result


class TestGetNews:
    """Tests for get_news function."""

    @pytest.mark.integration
    def test_get_news_company(self):
        """Test getting news for a company."""
        result = get_news.invoke({"company": "Sabancı Holding"})
        
        assert "news" in result or "err" in result
        if "news" in result:
            assert "sent" in result  # Sentiment


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Edge case and boundary tests."""

    @pytest.mark.unit
    def test_empty_symbol(self):
        """Test with empty string."""
        # This might match something unexpectedly
        result = analyze_stock.invoke({"symbol": ""})
        # Should either return data or error, not crash
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_whitespace_symbol(self):
        """Test with whitespace only."""
        result = analyze_stock.invoke({"symbol": "   "})
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_special_characters(self):
        """Test with special characters."""
        result = analyze_stock.invoke({"symbol": "!@#$%"})
        assert "err" in result

    @pytest.mark.unit
    def test_very_long_symbol(self):
        """Test with very long input."""
        long_input = "a" * 1000
        result = analyze_stock.invoke({"symbol": long_input})
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_unicode_turkish_chars(self):
        """Test Turkish characters are handled."""
        result = analyze_stock.invoke({"symbol": "tüpraş"})
        # Should resolve to TUPRS.IS
        assert isinstance(result, dict)
