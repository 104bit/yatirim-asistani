import json
import dataclasses
from datetime import datetime
from typing import Optional
import os

from .models import ScoutInput, ScoutOutput
from .market import fetch_market_data
from .news import fetch_news
from .scrubber import clean_news

class ScoutAgent:
    def __init__(self):
        self.market_data = []
        self.news_data = []

    def run(self, input_data: ScoutInput):
        """
        Runs the Scout agent processes.
        """
        print(f"Starting Scout Agent for {input_data.target_company} ({input_data.symbol})...")
        
        # Run synchronously to avoid yfinance threading issues
        print("Starting data collection tasks (Sequential)...")
        
        # 1. Market Data
        market_thread_start = datetime.now()
        self._run_market_task(input_data)
        
        # 2. News Data
        news_thread_start = datetime.now()
        self._run_news_task(input_data)
        
        # Threads variable no longer used, but keeping structure logical
        # t_market.join()
        # t_news.join()
        
        print(f"Tasks completed.")
        # Compile Output
        output = ScoutOutput(
            meta={
                "target_company": input_data.target_company,
                "symbol": input_data.symbol,
                "timestamp": datetime.now().isoformat(),
                "agent_id": "scout_v1"
            },
            numerical_stats=self.market_data,
            textual_insights=self.news_data
        )
        
        self._persist_output(output)
        self._report_status(output)

    def _run_market_task(self, input_data: ScoutInput):
        try:
            print(f"[Market Data] Fetching data for {input_data.symbol}...")
            data = fetch_market_data(input_data.symbol, input_data.start_time, input_data.end_time)
            self.market_data = data
            print(f"[Market Data] Fetched {len(data)} records.")
        except Exception as e:
            print(f"[Market Data] Error: {e}")

    def _run_news_task(self, input_data: ScoutInput):
        try:
            print(f"[News] Fetching news for '{input_data.target_company}'...")
            raw_news = fetch_news(input_data.target_company)
            
            print(f"[News] Cleaning {len(raw_news)} raw items...")
            cleaned = clean_news(raw_news, [input_data.target_company])
            
            self.news_data = cleaned
            print(f"[News] Processed {len(cleaned)} relevant items.")
        except Exception as e:
            print(f"[News] Error: {e}")

    def _persist_output(self, output: ScoutOutput):
        # Determine filename
        filename = f"{output.meta['target_company'].replace(' ', '_').lower()}_scout_output.json"
        filepath = os.path.join(os.getcwd(), filename)
        
        # Custom encoder for datetime
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, datetime):
                    return o.isoformat()
                return super().default(o)
                
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataclasses.asdict(output), f, cls=DateTimeEncoder, indent=4, ensure_ascii=False)
            
        print(f"Output saved to: {filepath}")

    def _report_status(self, output: ScoutOutput):
        print("-" * 50)
        print(f"1. Aşama başarıyla tamamlandı.")
        print(f"X (Sayısal Veri): {len(output.numerical_stats)}")
        print(f"Y (Haber Adedi): {len(output.textual_insights)}")
        print("-" * 50)
