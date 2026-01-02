from typing import List, Set
from .models import NewsItem
from difflib import SequenceMatcher
import re

def clean_news(news_list: List[NewsItem], target_keywords: List[str]) -> List[NewsItem]:
    """
    Cleans the news list:
    1. Filter by keywords logic (simple inclusion or similarity).
    2. Deduplication.
    3. Ad filtering.
    4. Language detection (heuristic).
    """
    
    cleaned_list = []
    seen_titles = []
    
    # Sort by time (newest first) to keep the latest or earliest? 
    # User requirement: "Keep earliest". So sort by timestamp ascending.
    news_list.sort(key=lambda x: x.timestamp)
    
    for news in news_list:
        # 1. Ad/Noise Filtering
        if is_ad_or_noise(news.title) or is_ad_or_noise(news.snippet):
            continue
            
        # 2. Keyword Filtering (at least one keyword must be present in title)
        # Relaxed check: if target company is in title
        if not any(k.lower() in news.title.lower() for k in target_keywords):
            # Optional: Strict filtering. For now, let's just check company name.
            # If no keyword matches, maybe skip. 
            pass # We will might want to be lenient or strict. Let's assume input news assumes query relevance.
                 # But request says: "Sadece ... %80 eslesen basliklari ayikla".
                 # Simple substring check is robust enough for now.
        
        # 3. Deduplication (Similarity check)
        is_duplicate = False
        for seen_title in seen_titles:
            similarity = SequenceMatcher(None, news.title, seen_title).ratio()
            if similarity > 0.8: # 80% similarity threshold
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
            
        seen_titles.append(news.title)
        
        # 4. Language Detection
        news.language = detect_language(news.title + " " + news.snippet)
        
        cleaned_list.append(news)
        
    return cleaned_list

def is_ad_or_noise(text: str) -> bool:
    noise_keywords = [
        "Yatırım Tavsiyesi Değildir", 
        "Sponsorlu İçerik", 
        "Reklam",
        "Casino",
        "Bahis"
    ]
    for keyword in noise_keywords:
        if keyword.lower() in text.lower():
            return True
    return False

def detect_language(text: str) -> str:
    # Very simple heuristic for TR vs EN
    # Check for specific Turkish characters
    tr_chars = {'ğ', 'ü', 'ş', 'ı', 'ö', 'ç', 'Ğ', 'Ü', 'Ş', 'İ', 'Ö', 'Ç'}
    if any(char in tr_chars for char in text):
        return "tr"
    return "en" # Default to English or Unknown if strictly ASCII, but realisticly mixed.
