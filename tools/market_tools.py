"""
Optimized Market Tools (v2)
============================
8 powerful, compact tools for financial analysis.
"""

from typing import List, Dict, Any
from langchain_core.tools import tool


# =============================================================================
# SYMBOL MAPPING - Türkçe/İngilizce isimlerden yfinance sembollerine
# =============================================================================
SYMBOL_MAP = {
    # Emtialar / Commodities
    "altın": "GC=F", "gold": "GC=F", "altin": "GC=F",
    "gümüş": "SI=F", "silver": "SI=F", "gumus": "SI=F",
    "petrol": "CL=F", "oil": "CL=F", "crude": "CL=F", "brent": "BZ=F",
    "doğalgaz": "NG=F", "natural gas": "NG=F", "dogalgaz": "NG=F",
    "bakır": "HG=F", "copper": "HG=F", "bakir": "HG=F",
    "platin": "PL=F", "platinum": "PL=F",
    "paladyum": "PA=F", "palladium": "PA=F",
    
    # Kripto / Crypto
    "bitcoin": "BTC-USD", "btc": "BTC-USD",
    "ethereum": "ETH-USD", "eth": "ETH-USD",
    "solana": "SOL-USD", "sol": "SOL-USD",
    "ripple": "XRP-USD", "xrp": "XRP-USD",
    "dogecoin": "DOGE-USD", "doge": "DOGE-USD",
    "cardano": "ADA-USD", "ada": "ADA-USD",
    
    # Popüler ABD Hisseleri / US Stocks
    "nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "amazon": "AMZN",
    "tesla": "TSLA", "meta": "META", "facebook": "META",
    "netflix": "NFLX", "amd": "AMD", "intel": "INTC",
    
    # Türk Hisseleri / Turkish Stocks (otomatik .IS eklenir)
    "sabancı": "SAHOL.IS", "sabanci": "SAHOL.IS", "sahol": "SAHOL.IS",
    "koç": "KCHOL.IS", "koc": "KCHOL.IS", "kchol": "KCHOL.IS",
    "garanti": "GARAN.IS", "garan": "GARAN.IS",
    "akbank": "AKBNK.IS", "akbnk": "AKBNK.IS",
    "yapı kredi": "YKBNK.IS", "yapi kredi": "YKBNK.IS", "ykbnk": "YKBNK.IS",
    "thy": "THYAO.IS", "türk hava yolları": "THYAO.IS", "thyao": "THYAO.IS",
    "turkcell": "TCELL.IS", "tcell": "TCELL.IS",
    "bim": "BIMAS.IS", "bimas": "BIMAS.IS",
    "migros": "MGROS.IS", "mgros": "MGROS.IS",
    "tüpraş": "TUPRS.IS", "tupras": "TUPRS.IS", "tuprs": "TUPRS.IS",
    "aselsan": "ASELS.IS", "asels": "ASELS.IS",
    "ford otosan": "FROTO.IS", "froto": "FROTO.IS",
    "tofaş": "TOASO.IS", "tofas": "TOASO.IS", "toaso": "TOASO.IS",
    
    # Endeksler / Indices
    "bist100": "XU100.IS", "bist 100": "XU100.IS", "borsa istanbul": "XU100.IS",
    "s&p500": "^GSPC", "sp500": "^GSPC", "s&p 500": "^GSPC",
    "nasdaq": "^IXIC", "dow jones": "^DJI", "dow": "^DJI",
    "dax": "^GDAXI", "ftse": "^FTSE",
}


def resolve_symbol(query: str) -> str:
    """
    Verilen sorguyu yfinance sembolüne çevirir.
    1. Önce eşleme tablosuna bakar
    2. Bulamazsa direkt yfinance'ı dener
    3. O da başarısız olursa web_search ile arar
    """
    import re
    query_lower = query.lower().strip()
    
    # Direkt eşleşme
    if query_lower in SYMBOL_MAP:
        resolved = SYMBOL_MAP[query_lower]
        print(f"[Symbol Resolver] '{query}' → '{resolved}' (tablo)")
        return resolved
    
    # Kısmi eşleşme (kelime içeriyorsa)
    for key, symbol in SYMBOL_MAP.items():
        if key in query_lower or query_lower in key:
            print(f"[Symbol Resolver] '{query}' ~ '{key}' → '{symbol}' (kısmi)")
            return symbol
    
    # Zaten geçerli bir sembol formatı mı? (.IS, -USD, =F içeriyor veya tamamen büyük harf)
    if "." in query or "-" in query or "=" in query:
        print(f"[Symbol Resolver] '{query}' (format geçerli, direkt kullan)")
        return query
    
    if query.isupper() and len(query) <= 6:
        print(f"[Symbol Resolver] '{query}' (zaten ticker formatında)")
        return query
    
    # Web search ile sembol ara
    print(f"[Symbol Resolver] '{query}' tabloda yok, web_search deneniyor...")
    try:
        from ddgs import DDGS
        search_query = f"{query} hisse senedi yfinance sembol ticker"
        
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, region='tr-tr', max_results=3))
        
        if results:
            # Sonuçlardan sembol bulmaya çalış
            combined_text = " ".join([r.get("body", "") + " " + r.get("title", "") for r in results])
            
            # BIST sembolleri (.IS ile biter) ara
            bist_match = re.search(r'\b([A-Z]{3,6})\.IS\b', combined_text.upper())
            if bist_match:
                found_symbol = bist_match.group(0)
                print(f"[Symbol Resolver] Web'den bulundu: '{query}' → '{found_symbol}'")
                # Tabloya ekle ki bir dahaki sefere hızlı olsun
                SYMBOL_MAP[query_lower] = found_symbol
                return found_symbol
            
            # Genel ticker sembolleri (3-5 büyük harf)
            ticker_match = re.search(r'\b([A-Z]{3,5})\b', combined_text.upper())
            if ticker_match:
                found_symbol = ticker_match.group(1)
                # Yaygın kelimeler değilse
                if found_symbol not in ["THE", "AND", "FOR", "USD", "TRY", "EUR"]:
                    print(f"[Symbol Resolver] Web'den tahmin: '{query}' → '{found_symbol}'")
                    return found_symbol
    
    except Exception as e:
        print(f"[Symbol Resolver] Web search hatası: {e}")
    
    # Hiçbir şey bulunamadı - büyük harfe çevir ve dene
    fallback = query.upper().replace(" ", "")[:6]
    print(f"[Symbol Resolver] Fallback: '{query}' → '{fallback}'")
    return fallback


# =============================================================================
# TOOL 1: analyze_stock (Complete stock analysis in ONE call)
# =============================================================================
@tool
def analyze_stock(symbol: str) -> Dict[str, Any]:
    """
    Complete stock analysis: price, technicals, and summary.
    Use this as your PRIMARY tool for any stock question.
    Accepts both ticker symbols (NVDA) and names (Nvidia, Bitcoin, Altın).
    
    Args:
        symbol: Stock ticker or asset name (e.g., "NVDA", "Nvidia", "Bitcoin", "Altın", "SAHOL.IS")
    """
    import yfinance as yf
    
    # Sembolü çözümle (Nvidia → NVDA, Altın → GC=F vb.)
    original_input = symbol
    symbol = resolve_symbol(symbol)
    print(f"[analyze_stock] {original_input} → {symbol}")
    
    # Farklı zaman periyotları ile fallback dene
    periods_to_try = ["1mo", "5d", "1d"]
    h = None
    used_period = None
    
    # İlk deneme: verilen sembol
    for period in periods_to_try:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period=period)
            if not h.empty:
                used_period = period
                break
        except Exception:
            continue
    
    # İkinci deneme: .IS suffix ekle (BIST hisseleri için)
    if (h is None or h.empty) and symbol.isupper() and "." not in symbol and "-" not in symbol:
        bist_symbol = f"{symbol}.IS"
        print(f"[analyze_stock] {symbol} bulunamadı, BIST denemesi: {bist_symbol}")
        for period in periods_to_try:
            try:
                t = yf.Ticker(bist_symbol)
                h = t.history(period=period)
                if not h.empty:
                    symbol = bist_symbol  # Başarılı, sembolü güncelle
                    used_period = period
                    break
            except Exception:
                continue
    
    if h is None or h.empty:
        return {
            "err": f"Veri bulunamadı: '{original_input}' (sembol: {symbol}). "
                   f"Lütfen geçerli bir hisse/emtia/kripto adı veya sembolü deneyin.",
            "tried_symbol": symbol,
            "suggestion": "web_search ile doğru sembolü arayın"
        }
    
    try:
        t = yf.Ticker(symbol)
        info = t.info
        
        p = float(h['Close'].iloc[-1])
        p_start = float(h['Close'].iloc[0])
        chg = ((p - p_start) / p_start) * 100
        vol = h['Close'].std() / h['Close'].mean() * 100
        
        # Simple RSI
        gains = [max(0, h['Close'].iloc[i] - h['Close'].iloc[i-1]) for i in range(1, min(15, len(h)))]
        losses = [max(0, h['Close'].iloc[i-1] - h['Close'].iloc[i]) for i in range(1, min(15, len(h)))]
        rsi = 100 - (100 / (1 + (sum(gains)/(sum(losses)+0.001))))
        
        # Sinyal hesaplama
        sig = "AL" if rsi < 30 or chg > 5 else "SAT" if rsi > 70 or chg < -5 else "TUT"
        
        # Sonuç
        result = {
            "sembol": symbol.replace(".IS", "").replace("-USD", "").replace("=F", ""),
            "fiyat": round(p, 2),
            "degisim": f"{chg:+.1f}%",
            "volatilite": f"{vol:.1f}%",
            "rsi": round(rsi, 0),
            "sinyal": sig,
            "periyot": used_period
        }
        
        # Opsiyonel alanlar (varsa ekle)
        if info.get("currency"):
            result["para_birimi"] = info["currency"]
        if info.get("trailingPE"):
            result["pe"] = round(info["trailingPE"], 1)
        if info.get("marketCap"):
            result["piyasa_degeri"] = f"{info['marketCap']/1e9:.1f}B"
        if info.get("shortName"):
            result["isim"] = info["shortName"]
        
        return result
        
    except Exception as e:
        return {
            "err": f"Analiz hatası: {str(e)[:80]}",
            "sembol": symbol,
            "fiyat_son": round(float(h['Close'].iloc[-1]), 2) if not h.empty else None
        }




# =============================================================================
# TOOL 2: scan_sector (Analyze entire sector, return best 3)
# =============================================================================
@tool
def scan_sector(sector: str) -> Dict[str, Any]:
    """
    Scan all stocks in a sector, return top 3 picks.
    Sectors: banka, holding, havacılık, enerji, perakende, teknoloji, otomotiv
    
    Args:
        sector: Sector name (Turkish)
    """
    import yfinance as yf
    print(f"[scan_sector] {sector}")
    
    SECTORS = {
        "banka": ["GARAN.IS", "AKBNK.IS", "YKBNK.IS", "ISCTR.IS"],
        "holding": ["SAHOL.IS", "KCHOL.IS", "SISE.IS"],
        "havacılık": ["THYAO.IS", "PGSUS.IS", "TAVHL.IS"],
        "enerji": ["TUPRS.IS", "PETKM.IS", "AKSEN.IS"],
        "perakende": ["BIMAS.IS", "MGROS.IS", "SOKM.IS"],
        "teknoloji": ["ASELS.IS", "LOGO.IS"],
        "otomotiv": ["TOASO.IS", "FROTO.IS", "DOAS.IS"]
    }
    
    key = sector.lower().replace("ı", "i")
    symbols = next((v for k, v in SECTORS.items() if k in key or key in k), None)
    
    if not symbols:
        return {"err": f"Unknown sector. Available: {list(SECTORS.keys())}"}
    
    results = []
    for sym in symbols:
        try:
            h = yf.Ticker(sym).history(period="1mo")
            if h.empty: continue
            chg = ((h['Close'].iloc[-1] - h['Close'].iloc[0]) / h['Close'].iloc[0]) * 100
            results.append({"s": sym.replace(".IS",""), "p": round(float(h['Close'].iloc[-1]),1), "chg": f"{chg:+.1f}%"})
        except Exception as e:
            print(f"[scan_sector] {sym} hatası: {e}")
            continue
    
    results.sort(key=lambda x: float(x["chg"].replace("%","").replace("+","")), reverse=True)
    return {"sector": sector, "top3": results[:3], "best": results[0]["s"] if results else "-"}


# =============================================================================
# TOOL 3: compare (Compare 2-3 stocks)
# =============================================================================
@tool
def compare(symbols: List[str]) -> Dict[str, Any]:
    """
    Compare 2-3 stocks side by side.
    
    Args:
        symbols: List of 2-3 stock symbols (e.g., ["SAHOL.IS", "KCHOL.IS"])
    """
    import yfinance as yf
    print(f"[compare] {symbols}")
    
    results = []
    for sym in symbols[:3]:
        try:
            t = yf.Ticker(sym)
            h = t.history(period="1mo")
            info = t.info
            if h.empty: continue
            chg = ((h['Close'].iloc[-1] - h['Close'].iloc[0]) / h['Close'].iloc[0]) * 100
            results.append({
                "s": sym.replace(".IS",""),
                "p": round(float(h['Close'].iloc[-1]),1),
                "chg": f"{chg:+.1f}%",
                "pe": round(info.get("trailingPE",0),1) or "-"
            })
        except Exception as e:
            print(f"[compare] {sym} hatası: {e}")
            continue
    
    if not results:
        return {"err": "No data"}
    
    best = max(results, key=lambda x: float(x["chg"].replace("%","").replace("+","")))
    return {"stocks": results, "winner": best["s"]}


# =============================================================================
# TOOL 4: get_news (Company news headlines)
# =============================================================================
@tool
def get_news(company: str) -> Dict[str, Any]:
    """
    Get recent news headlines for a company.
    
    Args:
        company: Company name (e.g., "Sabancı Holding", "THY")
    """
    import feedparser
    print(f"[get_news] {company}")
    
    url = f"https://news.google.com/rss/search?q={company.replace(' ','+')}&hl=tr&gl=TR"
    feed = feedparser.parse(url)
    
    headlines = [e.get("title", "")[:80] for e in feed.entries[:5]]
    
    # Simple sentiment
    pos = ["kâr", "artış", "büyüme", "rekor", "yükseliş"]
    neg = ["zarar", "düşüş", "kriz", "risk", "satış"]
    
    score = sum(1 for h in headlines for w in pos if w in h.lower())
    score -= sum(1 for h in headlines for w in neg if w in h.lower())
    sent = "+" if score > 0 else "-" if score < 0 else "0"
    
    return {"news": headlines[:3], "sent": sent}


# =============================================================================
# TOOL 5: build_portfolio (Allocate money to stocks)
# =============================================================================
@tool
def build_portfolio(amount: float, symbols: List[str]) -> Dict[str, Any]:
    """
    Allocate investment amount across stocks equally.
    
    Args:
        amount: Investment amount in TL (e.g., 100000)
        symbols: List of stock symbols (e.g., ["SAHOL.IS", "GARAN.IS", "THYAO.IS"])
    """
    import yfinance as yf
    print(f"[build_portfolio] {amount} TL -> {symbols}")
    
    n = len(symbols)
    if n == 0:
        return {"err": "No symbols"}
    
    per_stock = amount / n
    positions = []
    total = 0
    
    for sym in symbols:
        try:
            h = yf.Ticker(sym).history(period="1d")
            p = float(h['Close'].iloc[-1]) if not h.empty else 0
            shares = int(per_stock / p) if p > 0 else 0
            val = shares * p
            positions.append({"s": sym.replace(".IS",""), "qty": shares, "val": round(val,0)})
            total += val
        except Exception as e:
            print(f"[build_portfolio] {sym} hatası: {e}")
            continue
    
    return {"positions": positions, "invested": round(total,0), "cash": round(amount-total,0)}


# =============================================================================
# TOOL 6: get_forex (Currency rates)
# =============================================================================
@tool
def get_forex(pair: str = "USDTRY") -> Dict[str, Any]:
    """
    Get currency exchange rate.
    
    Args:
        pair: Currency pair (e.g., "USDTRY", "EURTRY", "GBPTRY")
    """
    import yfinance as yf
    print(f"[get_forex] {pair}")
    
    symbol = f"{pair}=X"
    h = yf.Ticker(symbol).history(period="5d")
    
    if h.empty:
        return {"err": f"No data for {pair}"}
    
    rate = float(h['Close'].iloc[-1])
    chg = ((rate - h['Close'].iloc[0]) / h['Close'].iloc[0]) * 100
    
    return {"pair": pair, "rate": round(rate, 2), "chg": f"{chg:+.2f}%"}


# =============================================================================
# TOOL 7: get_fundamentals (P/E, P/B, ROE for valuation)
# =============================================================================
@tool
def get_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Get fundamental ratios for valuation.
    
    Args:
        symbol: Stock ticker (e.g., "SAHOL.IS")
    """
    import yfinance as yf
    print(f"[get_fundamentals] {symbol}")
    
    info = yf.Ticker(symbol).info
    
    return {
        "s": symbol.replace(".IS",""),
        "pe": round(info.get("trailingPE",0),1) or "-",
        "pb": round(info.get("priceToBook",0),1) or "-",
        "roe": f"{info.get('returnOnEquity',0)*100:.0f}%" if info.get('returnOnEquity') else "-",
        "div": f"{info.get('dividendYield',0)*100:.1f}%" if info.get('dividendYield') else "-",
        "mcap": f"{info.get('marketCap',0)/1e9:.0f}B" if info.get('marketCap') else "-"
    }


# =============================================================================
# TOOL 8: quick_answer (For simple questions without data)
# =============================================================================
@tool
def quick_answer(question: str) -> Dict[str, Any]:
    """
    For general finance questions that don't need live data.
    Just returns the question for LLM to answer from knowledge.
    
    Args:
        question: The user's question
    """
    print(f"[quick_answer] {question}")
    return {"q": question, "note": "Answer from your knowledge, no live data needed."}


# =============================================================================
# TOOL 9: web_search (Search the internet)
# =============================================================================
@tool
def web_search(query: str) -> Dict[str, Any]:
    """
    Search the internet and extract actual content from top results.
    Use this when you need to find stock symbols, company info, historical data, or any data not available in other tools.
    
    Args:
        query: Search query (e.g., "2024 en çok kazandıran hisseler", "BIST100 performans")
    """
    print(f"[web_search] {query}")
    
    try:
        from ddgs import DDGS
        import requests
        from bs4 import BeautifulSoup
        
        # 1. Arama sonuçlarını al
        search_results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, region='tr-tr', max_results=3):
                search_results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
        
        # 2. İlk sonucun içeriğini çek
        extracted_content = ""
        if search_results and search_results[0].get("url"):
            try:
                url = search_results[0]["url"]
                print(f"[web_search] Fetching content from: {url[:50]}...")
                
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Script ve style etiketlerini kaldır
                    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                        tag.decompose()
                    
                    # Ana içeriği bul
                    article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
                    if article:
                        text = article.get_text(separator=' ', strip=True)
                    else:
                        text = soup.get_text(separator=' ', strip=True)
                    
                    # Temizle ve kısalt
                    text = ' '.join(text.split())  # Fazla boşlukları temizle
                    extracted_content = text[:1500]  # İlk 1500 karakter
                    
                    print(f"[web_search] Extracted {len(extracted_content)} chars of content")
                    
            except Exception as fetch_error:
                print(f"[web_search] Content fetch error: {fetch_error}")
                extracted_content = search_results[0].get("snippet", "")
        
        return {
            "query": query,
            "results": [
                {"title": r["title"][:80], "snippet": r["snippet"][:200]} 
                for r in search_results[:3]
            ],
            "full_content": extracted_content if extracted_content else "İçerik çekilemedi",
            "source_url": search_results[0]["url"] if search_results else ""
        }
    
    except Exception as e:
        return {"err": str(e)[:100]}


# =============================================================================
# EXPORT
# =============================================================================
ALL_TOOLS = [
    analyze_stock,      # 1. Primary stock analysis
    scan_sector,        # 2. Sector scanning
    compare,            # 3. Stock comparison
    get_news,           # 4. News & sentiment
    build_portfolio,    # 5. Portfolio allocation
    get_forex,          # 6. Currency rates
    get_fundamentals,   # 7. Valuation ratios
    quick_answer,       # 8. General questions
    web_search          # 9. Internet search
]
