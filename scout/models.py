from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class ScoutInput:
    """Input parameters for the Scout agent."""
    target_company: str
    symbol: str  # e.g., "SAHOL.IS"
    start_time: datetime
    end_time: datetime

@dataclass
class MarketData:
    """Hourly market data point."""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int

@dataclass
class NewsItem:
    """Single news item with metadata."""
    title: str
    timestamp: datetime
    source: str
    snippet: str
    language: str = "unknown"

@dataclass
class ScoutOutput:
    """Final output structure of the Scout agent."""
    meta: dict
    numerical_stats: List[MarketData]
    textual_insights: List[NewsItem]
