import pandas as pd
import re
import json

# --- Yapılandırma ---
INPUT_FILE = 'docs/v1_f_IT_Department_Sorunlar_.xlsx'
OUTPUT_FILE = 'docs/classified_output.xlsx'

# --- LLM Prompt Şablonu ---
LLM_PROMPT_TEMPLATE = """
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
{{
  "kategori": "kategori_adı",
  "guven_skoru": 0.95,
  "neden": "kısa açıklama"
}}

ÖRNEKLER:
Talep: "VPN bağlantı problemi"
Çıktı: {{"kategori": "Bağlantı", "guven_skoru": 0.98, "neden": "VPN bağlantı sorunu ağ problemidir"}}

Talep: "VPN erişim isteği"
Çıktı: {{"kategori": "Erişim", "guven_skoru": 0.95, "neden": "VPN erişim yetkisi talebidir"}}

Talep: "Yeni kullanıcı isteği"
Çıktı: {{"kategori": "Kullanıcı Yönetimi", "guven_skoru": 0.99, "neden": "Hesap oluşturma talebidir"}}

ŞİMDİ SINIFLANDIR:
Talep: "{text}"
"""

# --- 1. Aşama: Regex ile Katı Ön Sınıflandırma ---
def regex_classifier(text):
    """
    Metni analiz eder ve HATA, ISTEK veya BELIRSIZ olarak sınıflandırır.
    
    Kurallar:
    - Sadece Hata kelimeleri varsa -> HATA
    - Sadece İstek kelimeleri varsa -> İSTEK
    - Her ikisi de varsa veya hiçbiri yoksa -> BELIRSIZ
    """
    if not isinstance(text, str):
        return "BELIRSIZ"
        
    text_lower = text.lower()
    
    # HATA desenleri (kök kelime araması)
    error_patterns = [
        r'sorun', r'hata', r'çalışmıyor', r'ulaşılamıyor', 
        r'problem', r'arızalı', r'bozuk', r'açılmıyor',
        r'bağlanamıyorum', r'düştü', r'yavaş'
    ]
    
    # İSTEK desenleri (kök kelime araması + Türkçe ses yumuşamaları)
    request_patterns = [
        r'talep', r'taleb',  # p→b yumuşaması (talebi, talebim)
        r'istek', r'isteg',  # k→ğ yumuşaması (isteği)
        r'ekleme', r'ekle', 
        r'kurulum', r'yetki', r'yeni', 
        r'sipariş', r'erişim', r'lisans', r'şifre',
        r'rapor', r'donanım'  # ek kategoriler
    ]
    
    has_error = any(re.search(p, text_lower) for p in error_patterns)
    has_request = any(re.search(p, text_lower) for p in request_patterns)
    
    if has_error and has_request:
        return "BELIRSIZ" # Çelişki
    elif has_error:
        return "HATA"
    elif has_request:
        return "İSTEK"
    else:
        return "BELIRSIZ" # Hiçbir şey bulunamadı

# --- 2. Aşama: Mock LLM (Simüle Edilmiş Yapay Zeka - JSON Çıktı) ---
def get_llm_prompt(text):
    """
    Gerçek LLM API'sine gönderilecek prompt'u döndürür.
    """
    return LLM_PROMPT_TEMPLATE.format(text=text)

def mock_llm_classifier(text):
    """
    Sadece BELIRSIZ vakalar için çalışır.
    Gerçek bir LLM bağlantısı yerine keyword matching ile simülasyon yapar.
    Gerçek kullanımda get_llm_prompt() ile prompt alınıp LLM API'sine gönderilir.
    """
    if not isinstance(text, str):
        return {
            "kategori": "DİĞER",
            "guven_skoru": 0.0,
            "neden": "Metin girdisi yok"
        }
    
    text_lower = text.lower()
    
    # Detaylı Kategoriler ve Anahtar Kelimeler
    categories = {
        "Bağlantı": ["internet", "wifi", "kablosuz", "ağ", "network", "kopuyor", "yavaş", "vpn", "ip"],
        "Donanım": ["bilgisayar", "laptop", "yazıcı", "ekran", "monitör", "fare", "klavye", "telefon", "kulaklık", "şarj", "bozuk", "kırık"],
        "Erişim": ["şifre", "parola", "giriş", "login", "hesap", "kilit", "yetki", "erişim", "imza"],
        "Yazılım": ["office", "excel", "outlook", "teams", "adobe", "program", "uygulama", "lisans", "kurulum", "güncelleme", "açılmıyor"],
        "Kullanıcı Yönetimi": ["yeni kullanıcı", "işe giriş", "işten çıkış", "personel", "grup", "mail grubu"],
        "Raporlama": ["rapor", "analiz", "data", "veri çekme", "dashboard", "bütçe"]
    }
    
    best_category = "DİĞER"
    max_matches = 0
    matched_keywords = []
    
    for category, keywords in categories.items():
        current_matches = [k for k in keywords if k in text_lower]
        match_count = len(current_matches)
        
        if match_count > max_matches:
            max_matches = match_count
            best_category = category
            matched_keywords = current_matches
            
    # Güven Skoru Hesaplama (Basit bir heuristic)
    confidence = 0.5 + (min(max_matches, 5) * 0.1)  # Her eşleşme için 0.1 puan, max 1.0
    if max_matches == 0:
        confidence = 0.3 # Eşleşme yoksa düşük güven
        
    return {
        "kategori": best_category,
        "guven_skoru": confidence,
        "neden": f"Anahtar kelimeler bulundu: {', '.join(matched_keywords)}" if matched_keywords else "Yetersiz bilgi"
    }

# --- 3. Aşama: Gerçek LLM API Entegrasyonu (OpenAI) ---
def openai_llm_classifier(text, api_key=None, model="gpt-4o-mini"):
    """
    OpenAI API kullanarak gerçek LLM sınıflandırması yapar.
    
    NOT: Bu fonksiyon şu an kullanılmıyor, sadece hazır bekliyor.
    Kullanmak için:
    1. openai paketini yükleyin: pip install openai
    2. OPENAI_API_KEY environment variable'ı ayarlayın veya api_key parametresi verin
    
    Args:
        text: Sınıflandırılacak metin
        api_key: OpenAI API anahtarı (opsiyonel, yoksa env'den alınır)
        model: Kullanılacak model (varsayılan: gpt-4o-mini)
        
    Returns:
        dict: {"kategori": str, "guven_skoru": float, "neden": str}
    """
    import os
    
    try:
        from openai import OpenAI
    except ImportError:
        return {
            "kategori": "HATA",
            "guven_skoru": 0.0,
            "neden": "openai paketi yüklü değil. Yüklemek için: pip install openai"
        }
    
    # API anahtarını al
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        return {
            "kategori": "HATA",
            "guven_skoru": 0.0,
            "neden": "OPENAI_API_KEY environment variable tanımlı değil"
        }
    
    try:
        client = OpenAI(api_key=key)
        
        # Prompt oluştur
        prompt = get_llm_prompt(text)
        
        # API isteği yap
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": "Sen bir IT Help Desk sınıflandırma uzmanısın. Sadece JSON formatında yanıt ver."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Düşük temperature = daha tutarlı sonuçlar
            max_tokens=150
        )
        
        # Yanıtı parse et
        response_text = response.choices[0].message.content.strip()
        
        # JSON parse etmeyi dene
        import json
        try:
            result = json.loads(response_text)
            return {
                "kategori": result.get("kategori", "DİĞER"),
                "guven_skoru": result.get("guven_skoru", 0.8),
                "neden": result.get("neden", "LLM tarafından sınıflandırıldı")
            }
        except json.JSONDecodeError:
            # JSON parse edilemezse ham yanıtı döndür
            return {
                "kategori": "DİĞER",
                "guven_skoru": 0.5,
                "neden": f"JSON parse hatası: {response_text[:100]}"
            }
            
    except Exception as e:
        return {
            "kategori": "HATA",
            "guven_skoru": 0.0,
            "neden": f"API hatası: {str(e)}"
        }

# --- Ana Akış ---
def main():
    print(f"Reading from {INPUT_FILE}...")
    try:
        df = pd.read_excel(INPUT_FILE)
    except FileNotFoundError:
        print("Dosya bulunamadı!")
        return

    print("Processing with Synthesized Pipeline...")
    
    results = []
    
    for _, row in df.iterrows():
        original_text = row.get('subject', '')
        if pd.isna(original_text):
            original_text = row.get('body', '')
            
        # 1. Adım: Strict Regex
        regex_label = regex_classifier(original_text)
        
        final_category = regex_label
        confidence = 1.0
        reason = "Regex ile kesin eşleşme"
        
        # 2. Adım: Router (Yönlendirme)
        if regex_label == "BELIRSIZ":
            # LLM'e git
            llm_response = mock_llm_classifier(original_text)
            final_category = llm_response["kategori"]
            confidence = llm_response["guven_skoru"]
            reason = f"LLM Analizi: {llm_response['neden']}"
        
        results.append({
            'id': row.get('id'),
            'subject': original_text,
            'router_label': regex_label,
            'final_category': final_category,
            'confidence': confidence,
            'reason': reason
        })
        
    # Sonuçları kaydet
    result_df = pd.DataFrame(results)
    result_df.to_excel(OUTPUT_FILE, index=False)
    print(f"Sınıflandırma tamamlandı. Sonuçlar {OUTPUT_FILE} dosyasına kaydedildi.")
    
    # Örnek sonuçları göster
    print("\nÖrnek Sonuçlar:")
    print(result_df[['subject', 'router_label', 'final_category', 'confidence']].head(10))

if __name__ == "__main__":
    main()
