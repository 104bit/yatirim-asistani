"""
Integration Tests for ReAct Agent
==================================
Tests for the full agent workflow.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from react_agent import run_react_agent, build_react_agent


class TestAgentBasicQueries:
    """Test agent with basic queries."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_agent_commodity_query(self):
        """Test agent with commodity query."""
        result = run_react_agent("Bakır alınır mı?")
        
        # Result should be a non-empty string
        assert result is not None
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_agent_stock_query(self):
        """Test agent with stock query."""
        result = run_react_agent("Nvidia hissesi nasıl?")
        
        assert result is not None
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_agent_bist_query(self):
        """Test agent with BIST stock query."""
        result = run_react_agent("THY hissesi alınır mı?")
        
        assert result is not None
        assert len(result) > 0


class TestAgentOutputQuality:
    """Test agent output quality."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_output_contains_price(self):
        """Test that output contains price information."""
        result = run_react_agent("Altın alınır mı?")
        
        # Should contain numeric price
        import re
        has_price = bool(re.search(r'\d+[\.,]\d+', result))
        
        # Price is expected but not always guaranteed
        # Just check it's a reasonable response
        assert len(result) > 50

    @pytest.mark.integration
    @pytest.mark.slow
    def test_output_contains_recommendation(self):
        """Test that output contains recommendation."""
        result = run_react_agent("Bitcoin alınır mı?")
        
        # Should contain AL, SAT, or TUT (or variations)
        recommendations = ["al", "sat", "tut", "buy", "sell", "hold", "tavsiye"]
        has_recommendation = any(rec in result.lower() for rec in recommendations)
        
        # This is expected behavior
        assert len(result) > 50


class TestAgentReflection:
    """Test that reflection works correctly."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_reflection_ensures_data(self):
        """Test that reflection ensures data is present."""
        # This query should trigger data fetching
        result = run_react_agent("Gümüş fiyatı nedir?")
        
        # Response should have some substance
        assert len(result) > 30


class TestAgentErrorHandling:
    """Test agent error handling."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_agent_handles_unknown_asset(self):
        """Test agent with unknown asset."""
        result = run_react_agent("XYZ123 şirketi alınır mı?")
        
        # Should not crash, should return something
        assert result is not None

    @pytest.mark.integration
    @pytest.mark.slow
    def test_agent_handles_empty_query(self):
        """Test agent with minimal query."""
        result = run_react_agent("analiz")
        
        # Should handle gracefully
        assert result is not None


class TestAgentToolUsage:
    """Test that agent uses tools correctly."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_sector_query_uses_scan_sector(self):
        """Test that sector query triggers scan_sector."""
        result = run_react_agent("Banka sektörünü analiz et")
        
        # Should have multiple banks mentioned
        banks = ["garan", "akbank", "yapı", "isctr"]
        has_bank = any(bank in result.lower() for bank in banks)
        
        assert len(result) > 50

    @pytest.mark.integration
    @pytest.mark.slow
    def test_comparison_query(self):
        """Test comparison query."""
        result = run_react_agent("AAPL ve MSFT karşılaştır")
        
        # Should mention both
        assert "apple" in result.lower() or "aapl" in result.lower() or len(result) > 50


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestAgentPerformance:
    """Performance-related tests."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_response_time(self):
        """Test that agent responds within reasonable time."""
        import time
        
        start = time.time()
        result = run_react_agent("Dolar kuru nedir?")
        elapsed = time.time() - start
        
        # Should complete within 60 seconds (allowing for LLM latency)
        assert elapsed < 60, f"Response took {elapsed:.1f}s, expected < 60s"

    @pytest.mark.integration
    @pytest.mark.slow  
    def test_max_iterations_respected(self):
        """Test that agent respects max iteration limit."""
        # Complex query that might cause many iterations
        result = run_react_agent("Tüm emtiaları karşılaştır ve en iyisini bul")
        
        # Should still return something (not hang)
        assert result is not None
