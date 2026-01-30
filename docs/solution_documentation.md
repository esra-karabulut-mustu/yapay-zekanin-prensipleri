# IT Help Desk Sınıflandırma Sistemi Dokümantasyonu

Bu dokümantasyon, IT Help Desk taleplerini otomatik olarak sınıflandıran `classifier.py` sisteminin teknik detaylarını içerir.

---

## 1. Regex Desenleri

### HATA Desenleri

Aşağıdaki regex desenleri, bir talebin "HATA" kategorisine ait olduğunu belirlemek için kullanılır:

| Desen | Açıklama | Örnek Eşleşmeler |
|-------|----------|------------------|
| `\bsorun\w*` | "sorun" ile başlayan kelimeler | sorun, sorunlar, sorunlu |
| `\bhata\w*` | "hata" ile başlayan kelimeler | hata, hatası, hataları |
| `\bçalışmıyor\b` | Tam eşleşme | çalışmıyor |
| `\bulaşılamıyor\b` | Tam eşleşme | ulaşılamıyor |
| `\bproblem\w*` | "problem" ile başlayan kelimeler | problem, problemi, problemler |
| `\barızalı\b` | Tam eşleşme | arızalı |
| `\bbozuk\b` | Tam eşleşme | bozuk |
| `\baçılmıyor\b` | Tam eşleşme | açılmıyor |
| `\bbağlanamıyorum\b` | Tam eşleşme | bağlanamıyorum |
| `\bdüştü\b` | Tam eşleşme | düştü |
| `\byavaş\b` | Tam eşleşme | yavaş |

### İSTEK Desenleri

Aşağıdaki regex desenleri, bir talebin "İSTEK" kategorisine ait olduğunu belirlemek için kullanılır:

| Desen | Açıklama | Örnek Eşleşmeler |
|-------|----------|------------------|
| `talep` | Kök kelime | talep |
| `taleb` | p→b yumuşaması | talebi, talebim |
| `istek` | Kök kelime | istek |
| `isteg` | k→ğ yumuşaması | isteği |
| `ekleme` | Tam eşleşme | ekleme |
| `ekle` | Kök kelime | ekle, eklemek |
| `kurulum` | Kök kelime | kurulum, kurulumu |
| `yetki` | Kök kelime | yetki |
| `yeni` | Kök kelime | yeni |
| `sipariş` | Kök kelime | sipariş |
| `erişim` | Kök kelime | erişim |
| `lisans` | Kök kelime | lisans |
| `şifre` | Kök kelime | şifre |
| `rapor` | Kök kelime | rapor |
| `donanım` | Kök kelime | donanım |

### Türkçe Ses Yumuşaması Desteği

Türkçe'de kelime sonundaki sert ünsüzler (p, ç, t, k) ünlü ile başlayan ek aldığında yumuşar:
- **p → b**: talep → talebi
- **k → ğ**: istek → isteği
- **t → d**: kanat → kanadı
- **ç → c**: ağaç → ağacı

Bu nedenle regex desenlerinde hem kök hem yumuşamış hali aranmaktadır.

---

## 2. Workflow (Hibrit İş Akışı)

### Akış Diyagramı

```
┌─────────────────────────────────────┐
│  1. VERİ GİRİŞİ                     │
│  (IT Help Desk E-postaları)         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. REGEX KONTROLÜ                  │
│  • Hata kelimeleri kontrolü         │
│  • İstek kelimeleri kontrolü        │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────┴──────┐
        │             │
        ▼             ▼
┌──────────────┐  ┌──────────────┐     ┌──────────────┐
│    HATA      │  │    İSTEK     │     │   BELİRSİZ   │
│  Kategorisi  │  │  Kategorisi  │     │    Vakalar   │
└──────┬───────┘  └──────┬───────┘     └──────┬───────┘
       │                 │                    │
       │                 │                    ▼
       │                 │     ┌─────────────────────────────────────┐
       │                 │     │  3. YAPAY ZEKA MODELİNE GÖNDER      │
       │                 │     │  • Sadece belirsiz vakalar          │
       │                 │     │  • Optimize edilmiş prompt ile      │
       │                 │     │  (Maliyet: Sadece %X veri için)     │
       │                 │     └──────────────┬──────────────────────┘
       │                 │                    │
       │                 │                    ▼
       │                 │     ┌─────────────────────────────────────┐
       │                 │     │  LLM Kategorileri:                  │
       │                 │     │  • Bağlantı    • Yazılım            │
       │                 │     │  • Donanım     • Kullanıcı Yönetimi │
       │                 │     │  • Erişim      • Raporlama          │
       │                 │     └──────────────┬──────────────────────┘
       │                 │                    │
       ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    4. NİHAİ KATEGORİ ATAMA                          │
│  • Regex sonuçları + LLM sonuçları birleştirilir                    │
│  • İlgili ekibe otomatik yönlendirme yapılır                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Adım Adım Açıklama

| Adım | İşlem | Maliyet |
|------|-------|---------|
| 1 | **Veri Girişi**: E-posta konu başlıkları alınır | Düşük |
| 2 | **Regex Kontrolü**: HATA/İSTEK anahtar kelimeleri taranır | Düşük |
| 3 | **LLM Yönlendirme**: Sadece BELİRSİZ vakalar gönderilir | Orta |
| 4 | **Kategori Atama**: Tüm sonuçlar birleştirilir | Düşük |

### Maliyet Optimizasyonu

Bu hibrit yaklaşımın temel avantajı **maliyet tasarrufudur**:

- Regex ile çözülebilen vakalar direkt işlenir (API maliyeti: 0)
- Sadece belirsiz vakalar LLM'e gönderilir
- Tahmini tasarruf: **%60-80**

---

## 3. LLM Prompt

### Tam Prompt Şablonu

```
Sen bir IT Help Desk sınıflandırma uzmanısın. Görevin, kullanıcılardan gelen destek 
taleplerini analiz edip SADECE BİR kategoriye atamaktır.

KATEGORİLER:
1. Bağlantı - Ağ, internet, VPN, sunucu bağlantısı sorunları
2. Donanım - Fiziksel ekipman talepleri, bilgisayar, yazıcı, monitör vb.
3. Erişim - Sistem, uygulama, dosya erişim yetkileri ve erişim sorunları
4. Yazılım - Program kurulumu, güncelleme, yazılım hataları
5. Kullanıcı Yönetimi - Yeni kullanıcı oluşturma, mail grubu, hesap işlemleri
6. Raporlama - Rapor talepleri, veri çıktısı istekleri

SINIFLANDIRMA KURALLARI:
- Her talep SADECE 1 kategoriye ait olmalıdır
- VPN ifadesi varsa: erişim talebi ise "Erişim", bağlantı sorunu ise "Bağlantı"
- "Yetki" kelimesi varsa: "Erişim" kategorisi
- "Mail grubu" ifadesi varsa: "Kullanıcı Yönetimi"
- "Kurulum" ifadesi yazılımla ilgiliyse: "Yazılım"
- Belirsiz durumlarda en yakın kategoriyi seç

ÇIKTI FORMATI (JSON):
{
  "kategori": "kategori_adı",
  "guven_skoru": 0.95,
  "neden": "kısa açıklama"
}

ÖRNEKLER:
Talep: "VPN bağlantı problemi"
Çıktı: {"kategori": "Bağlantı", "guven_skoru": 0.98, "neden": "VPN bağlantı sorunu ağ problemidir"}

Talep: "VPN erişim isteği"
Çıktı: {"kategori": "Erişim", "guven_skoru": 0.95, "neden": "VPN erişim yetkisi talebidir"}

Talep: "Yeni kullanıcı isteği"
Çıktı: {"kategori": "Kullanıcı Yönetimi", "guven_skoru": 0.99, "neden": "Hesap oluşturma talebidir"}

ŞİMDİ SINIFLANDIR:
Talep: "{talep_metni}"
```

### Prompt Tasarım Prensipleri

| Prensip | Açıklama |
|---------|----------|
| **Rol Tanımı** | "Sen bir IT Help Desk sınıflandırma uzmanısın" |
| **Net Kategoriler** | 6 kategori açık tanımlarla |
| **Özel Kurallar** | VPN, Yetki gibi belirsiz durumlar için |
| **Yapısal Çıktı** | JSON formatı parsing kolaylığı için |
| **Few-shot Örnekler** | 3 örnek ile model yönlendirmesi |

### Python'da Kullanım

```python
from classifier import get_llm_prompt

# Prompt oluştur
prompt = get_llm_prompt("VPN bağlantı problemi")

# OpenAI API ile kullanım örneği
# response = openai.chat.completions.create(
#     model="gpt-4",
#     messages=[{"role": "user", "content": prompt}]
# )
```
