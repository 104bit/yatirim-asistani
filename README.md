# Yatırım Asistanı

LangGraph ve ReAct pattern kullanarak geliştirilmiş, yapay zeka destekli finansal analiz sistemi. Türkiye ve global piyasalar için kapsamlı yatırım araştırması yapar.

## Proje Hakkında

Bu proje, kullanıcıların finansal sorularına veri odaklı cevaplar veren akıllı bir ajan sistemidir. Sistem şu temel prensiplerle çalışır:

- **Veri Odaklı**: Her raporda somut fiyat, değişim yüzdesi ve teknik göstergeler bulunur
- **Araştırmacı**: Bilmediği konularda tahmin yapmaz, araştırır veya açıkça belirtir
- **Proaktif**: Belirsiz sorularda bile en uygun araçları kullanarak analiz yapar
- **Öz-Düzeltmeli**: Reflection mekanizması ile kendi cevaplarını değerlendirir ve gerekirse düzeltir

## Özellikler

### ReAct Agent
Reasoning + Acting pattern'i ile çalışan ajan, önce düşünür sonra harekete geçer. LangGraph'ın `bind_tools` özelliği sayesinde native tool calling kullanır.

### 8 Finansal Araç

| Araç | Açıklama | Örnek Kullanım |
|------|----------|----------------|
| `analyze_stock` | Hisse/emtia/kripto analizi | Fiyat, RSI, volatilite, sinyal |
| `scan_sector` | Sektör taraması | Banka, holding, enerji, teknoloji |
| `compare` | Varlık karşılaştırması | 2-3 hisseyi yan yana değerlendir |
| `get_news` | Haber çekme | Şirket haberlerini topla |
| `build_portfolio` | Portföy oluşturma | Belirli bütçeyi dağıt |
| `get_forex` | Döviz kurları | USD/TRY, EUR/TRY |
| `get_fundamentals` | Temel analiz | P/E, P/B, ROE oranları |
| `web_search` | Web araması | Geçmiş veriler, trendler |

### Scout Agent
Piyasa verisi ve haber toplama için ayrı bir ajan modülü. Otomatik veri toplama ve temizleme işlevi görür.

### Türkçe Dil Desteği
Sistem Türkçe varlık isimlerini tanır:
- "altın" → GC=F (Gold Futures)
- "bitcoin" → BTC-USD
- "thy" → THYAO.IS
- "garanti" → GARAN.IS

## Kurulum

### Gereksinimler
- Python 3.10+
- API anahtarı (Google Gemini veya OpenRouter)

### Adımlar

```bash
# Projeyi klonlayın
git clone https://github.com/104bit/yatirim-asistani.git
cd yatirim-asistani

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Ortam değişkenlerini ayarlayın
cp .env.example .env
```

`.env` dosyasını düzenleyip en az bir API anahtarı ekleyin:
```
GOOGLE_API_KEY=sizin_google_api_anahtariniz
OPENROUTER_API_KEY=sizin_openrouter_api_anahtariniz
```

## Kullanım

### Tek Sorgu
```bash
py research.py "Altın alınır mı?"
```

### İnteraktif Mod
```bash
py research.py --interactive
```

Örnek sorular:
- "Bitcoin alınır mı?"
- "Banka sektörü nasıl?"
- "THYAO vs SAHOL karşılaştır"
- "100.000 TL ile portföy oluştur"
- "2024'te en çok kazandıran hisseler"
- "Dolar kuru nedir?"

## Proje Yapısı

```
yatirim-asistani/
├── react_agent.py      # Ana ReAct agent (bind_tools ile)
├── llm_client.py       # LLM client wrapper
├── research.py         # CLI giriş noktası
├── tools/
│   └── market_tools.py # 8 finansal araç tanımları
├── scout/
│   ├── agent.py        # Scout agent
│   ├── market.py       # Piyasa verisi çekme
│   ├── news.py         # Haber çekme (RSS)
│   └── scrubber.py     # Veri temizleme
├── tests/              # Pytest test dosyaları
├── requirements.txt    # Bağımlılıklar
└── .env.example        # Örnek ortam değişkenleri
```

## Teknik Detaylar

### Ajan Akışı
1. **Query Rewriter**: Kullanıcı sorusunu analiz eder ve optimize eder
2. **Agent Node**: LLM ile düşünür, gerekirse tool çağırır
3. **Tool Node**: Tool'ları çalıştırır, sonuçları döner
4. **Reflection Node**: Cevap kalitesini değerlendirir
5. **Final Report**: Onaylanan raporu kullanıcıya sunar

### LLM Desteği
- Google Gemini (gemini-2.5-flash)
- OpenRouter (GPT-4o-mini)

Sistem önce OpenRouter'ı, bulamazsa Google Gemini'yi kullanır.

## Testler

```bash
# Tüm testleri çalıştır
pytest

# Detaylı çıktı ile
pytest -v

# Sadece unit testler
pytest -m unit

# Sadece integration testler (API gerektirir)
pytest -m integration
```

## Kısıtlamalar

- Gerçek zamanlı veri için yfinance kullanılır, bazen gecikmeli olabilir
- Bazı BIST hisseleri için veri bulunamayabilir
- API rate limit'lerine dikkat edilmelidir

## Yasal Uyarı

Bu araç sadece eğitim ve araştırma amaçlıdır. Yatırım tavsiyesi niteliği taşımaz. Yatırım kararlarınızı vermeden önce mutlaka kendi araştırmanızı yapın.

## Lisans

MIT License
