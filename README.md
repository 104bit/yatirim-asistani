# Yatırım Asistanı

LangGraph ve ReAct pattern kullanarak geliştirilmiş, yapay zeka destekli finansal analiz sistemi. Türkiye ve global piyasalar için kapsamlı yatırım araştırması yapar.

## Proje Hakkında

Bu proje, kullanıcıların finansal sorularına veri odaklı cevaplar veren akıllı bir ajan sistemidir. Sistem şu temel prensiplerle çalışır:

- **Veri Odaklı**: Her raporda somut fiyat, değişim yüzdesi ve teknik göstergeler bulunur.
- **Araştırmacı**: Bilmediği konularda tahmin yapmaz, araştırır veya açıkça belirtir.
- **Proaktif**: Belirsiz sorularda bile en uygun araçları kullanarak analiz yapar.
- **Öz-Düzeltmeli**: Reflection mekanizması ile kendi cevaplarını değerlendirir ve gerekirse düzeltir.

## Özellikler

### ReAct Agent
Reasoning + Acting pattern'i ile çalışan ajan, önce düşünür sonra harekete geçer. LangGraph'ın `bind_tools` özelliği sayesinde native tool calling kullanır.

### Telegram Bot Entegrasyonu
Sistem artık Telegram üzerinden de hizmet vermektedir. Kullanıcılar bot ile sohbet ederek analiz raporu alabilirler.

### 8 Finansal Araç

| Araç | Açıklama | Örnek Kullanım |
|------|----------|----------------|
| `analyze_stock` | Hisse/emtia/kripto analizi | Fiyat, RSI, volatilite, sinyal |
| `get_news` | Haber çekme (Tavily + RSS) | Şirket haberlerini topla (Öncelikli) |
| `scan_sector` | Sektör taraması | Banka, holding, enerji, teknoloji |
| `compare` | Varlık karşılaştırması | 2-3 hisseyi yan yana değerlendir |
| `build_portfolio` | Portföy oluşturma | Belirli bütçeyi dağıt |
| `get_forex` | Döviz kurları | USD/TRY, EUR/TRY |
| `get_fundamentals` | Temel analiz | P/E, P/B, ROE oranları |
| `web_search` | Web araması | Geçmiş veriler, trendler |

### Türkçe Dil Desteği
Sistem Türkçe varlık isimlerini tanır:
- "altın" -> GC=F (Gold Futures)
- "bitcoin" -> BTC-USD
- "thy" -> THYAO.IS
- "garanti" -> GARAN.IS

## Kurulum

### Gereksinimler
- Python 3.10+
- API Anahtarları (OpenRouter, Tavily, Telegram)

### Adımlar

1. Projeyi klonlayın:
   ```bash
   git clone https://github.com/104bit/yatirim-asistani.git
   cd yatirim-asistani
   ```

2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. Ortam değişkenlerini ayarlayın:
   ```bash
   cp .env.example .env
   ```

4. `.env` dosyasını düzenleyin:
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   TAVILY_API_KEY=tvly-...
   TELEGRAM_BOT_TOKEN=...
   RENDER_EXTERNAL_URL=https://sizin-app.onrender.com (Webhook için)
   ```

## Kullanım

### CLI (Komut Satırı)
```bash
py research.py "Altın alınır mı?"
```

### İnteraktif Mod
```bash
py research.py --interactive
```

### Telegram Botunu Çalıştırma (Yerel)
```bash
python -m bot.bot
```
(Not: Webhook modu için Render veya ngrok gereklidir. Yerelde polling için `bot.py` içinde mod değişikliği yapılabilir.)

## Proje Yapısı

```
yatirim-asistani/
├── react_agent.py      # Ana ReAct agent (Logic)
├── research.py         # CLI giriş noktası
├── bot/
│   ├── bot.py          # Telegram bot kodu (Flask + Webhook)
│   └── __init__.py
├── tools/
│   └── market_tools.py # Finansal araç tanımları
├── scout/              # (Legacy) Eski ajan modülleri
├── tests/              # Test dosyaları
├── requirements.txt    # Bağımlılıklar
├── Procfile            # Render deployment komutu
└── render.yaml         # Render konfigürasyonu
```

## Dağıtım (Deployment)

Proje Render üzerinde çalışmaya hazırdır.
1. GitHub reponuzu Render'a bağlayın.
2. `render.yaml` dosyasını blueprint olarak kullanın veya manuel Web Service oluşturun.
3. Environment Variable'ları Render paneline ekleyin.

## Yasal Uyarı

Bu araç sadece eğitim ve araştırma amaçlıdır. Yatırım tavsiyesi niteliği taşımaz. Yatırım kararlarınızı vermeden önce mutlaka kendi araştırmanızı yapın.

## Lisans

MIT License
