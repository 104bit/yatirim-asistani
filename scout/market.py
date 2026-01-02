import yfinance as yf
from datetime import datetime, timedelta
from typing import List
import pandas as pd
from .models import MarketData

def fetch_market_data(symbol: str, start_time: datetime, end_time: datetime) -> List[MarketData]:
    """
    Fetches hourly OHLCV data for the given symbol from yfinance.
    Uses a broader period and filters locally to avoid empty returns on strict start/end.
    """
    # Fetch 5 days to cover weekends/holidays and ensure we have ample data
    df = yf.download(symbol, period="5d", interval="1h", progress=False)
    
    market_data_list = []
    
    if df.empty:
        print(f"Warning: No market data found for {symbol}")
        return []
        
    # Reset index to get 'Datetime' column
    df = df.reset_index()
    
    # Flatten multi-level columns
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten: If MultiIndex (Price, Ticker), we want level 0 (Price)
        # Verify if 'Close' is in level 0
        if 'Close' in df.columns.get_level_values(0):
             df.columns = df.columns.get_level_values(0)
        else:
             # Fallback logic if structure is different
             df.columns = df.columns.get_level_values(0)
    
    # Debug info
    print(f"[Market Debug] Columns after reset: {df.columns}")
    
    # Fill missing values
    df = df.ffill()
    
    # Find the datetime column
    dt_col_name = 'Datetime' if 'Datetime' in df.columns else 'Date'
    if dt_col_name not in df.columns:
        # Check if it's named 'index' or something else
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                dt_col_name = col
                break
    
    print(f"[Market Debug] Using datetime column: {dt_col_name}")

    if dt_col_name in df.columns:
        # Debug before conversion
        print(f"[Market Debug] Sample TS (Raw): {df[dt_col_name].iloc[0]}")
        # Convert to timezone-naive
        try:
            df[dt_col_name] = pd.to_datetime(df[dt_col_name]).dt.tz_localize(None)
        except Exception:
            # Maybe already naive
            pass
            
    print(f"[Market Debug] Filtering Window: {start_time} to {end_time}")

    for _, row in df.iterrows():
        ts = row.get(dt_col_name)
        if not ts:
            continue
            
        # Filter
        if not (start_time <= ts <= end_time):
            continue

        try:
            data_point = MarketData(
                timestamp=ts,
                open_price=float(row['Open']),
                high_price=float(row['High']),
                low_price=float(row['Low']),
                close_price=float(row['Close']),
                volume=int(row['Volume'])
            )
            market_data_list.append(data_point)
        except Exception as e:
             continue
             
    # Fallback: If empty, return last 24 records available
    if not market_data_list and not df.empty:
        print(f"Warning: No data in specific window {start_time} to {end_time}. Returning last 24 available records.")
        recent_df = df.tail(24)
        for _, row in recent_df.iterrows():
            ts = row.get(dt_col_name)
            try:
                data_point = MarketData(
                    timestamp=ts,
                    open_price=float(row['Open']),
                    high_price=float(row['High']),
                    low_price=float(row['Low']),
                    close_price=float(row['Close']),
                    volume=int(row['Volume'])
                )
                market_data_list.append(data_point)
            except:
                pass

    return market_data_list
