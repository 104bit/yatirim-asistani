"""Edge case tests for symbol resolution"""
from tools.market_tools import analyze_stock

tests = [
    # Uç durumlar
    ('', 'Boş string'),
    ('asdfghjkl', 'Tamamen saçma'),
    ('12345', 'Sadece sayı'),
    ('apple pie', 'Alakasız kelime'),
    ('AAPL', 'Zaten ticker'),
    ('petkim', 'Tabloda yok ama gerçek BIST'),
    ('türkiye petrol', 'Çok kelimeli belirsiz'),
    ('XYZ123', 'Geçersiz format'),
]

for symbol, desc in tests:
    print(f'\n=== {desc}: "{symbol}" ===')
    try:
        result = analyze_stock.invoke({'symbol': symbol})
        if 'err' in result:
            print(f'❌ HATA: {str(result.get("err", ""))[:80]}')
        else:
            print(f'✅ {result.get("sembol", "?")} = {result.get("fiyat", "?")} ({result.get("sinyal", "?")})')
    except Exception as e:
        print(f'💥 EXCEPTION: {e}')
