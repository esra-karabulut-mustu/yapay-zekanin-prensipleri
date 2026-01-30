# IT Help Desk Sınıflandırma Sistemi

Yapay Zekanın Prensipleri - IT Help Desk taleplerini otomatik sınıflandıran hibrit pipeline.

## Kurulum

```bash
# uv ile bağımlılıkları yükle
uv sync

# OpenAI API anahtarını ayarla (opsiyonel - gerçek LLM kullanımı için)
export OPENAI_API_KEY=sk-...
```

## Kullanım

### Temel Kullanım (Mock LLM ile)

```bash
uv run python classifier.py
```

Bu komut:
1. `docs/v1_f_IT_Department_Sorunlar_.xlsx` dosyasını okur
2. Regex ile HATA/İSTEK/BELİRSİZ olarak ön sınıflandırma yapar
3. Belirsiz vakaları Mock LLM ile sınıflandırır
4. Sonuçları `docs/classified_output.xlsx` dosyasına yazar

### OpenAI API ile Gerçek LLM Kullanımı

```python
from classifier import openai_llm_classifier

# Yöntem 1: Environment variable
# export OPENAI_API_KEY=sk-...
result = openai_llm_classifier("VPN bağlantı problemi")

# Yöntem 2: Direkt API key
result = openai_llm_classifier(
    "Yazılım kurulumu talebi",
    api_key="sk-...",
    model="gpt-4o-mini"  # veya "gpt-4o", "gpt-3.5-turbo"
)

print(result)
# {'kategori': 'Yazılım', 'guven_skoru': 0.95, 'neden': 'Program kurulumu talebidir'}
```

## Mimari

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   VERİ GİRİŞİ   │────▶│  REGEX KONTROL  │────▶│  HATA / İSTEK   │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼ BELİRSİZ
                        ┌─────────────────┐
                        │   LLM (OpenAI)  │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  6 KATEGORİ     │
                        │  • Bağlantı     │
                        │  • Donanım      │
                        │  • Erişim       │
                        │  • Yazılım      │
                        │  • Kullanıcı Y. │
                        │  • Raporlama    │
                        └─────────────────┘
```

## Dosya Yapısı

```
├── classifier.py              # Ana sınıflandırma sistemi
├── pyproject.toml             # uv proje yapılandırması
├── docs/
│   ├── solution_documentation.md  # Teknik dokümantasyon
│   ├── v1_f_IT_Department_Sorunlar_.xlsx  # Girdi verisi
│   └── classified_output.xlsx # Çıktı verisi
└── README.md
```

## API Referansı

### `regex_classifier(text) -> str`
Metni regex ile HATA, İSTEK veya BELİRSİZ olarak sınıflandırır.

### `mock_llm_classifier(text) -> dict`
Keyword matching ile LLM simülasyonu yapar.

### `openai_llm_classifier(text, api_key=None, model="gpt-4o-mini") -> dict`
OpenAI API kullanarak gerçek LLM sınıflandırması yapar.

### `get_llm_prompt(text) -> str`
LLM'e gönderilecek prompt'u döndürür.

## Lisans

MIT
