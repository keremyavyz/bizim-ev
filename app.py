import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import random
import time

# --- 1. AYARLAR & TASARIM ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

# Özel CSS (Elit Tasarım)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lato:wght@300;400;700&display=swap');
    
    .stApp { background-color: #f8f9fa; font-family: 'Lato', sans-serif; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: #2c3e50; }
    
    /* İstatistik Kutuları */
    .metric-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); text-align: center;
        border-left: 5px solid #d4af37;
    }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #2c3e50; }
    .metric-label { font-size: 0.9rem; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Ürün Kartı */
    .product-card {
        background-color: white; padding: 15px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 1px solid #eee; transition: transform 0.2s;
    }
    .product-card:hover { transform: translateY(-5px); border-color: #d4af37; }
    
    .price-tag { color: #27ae60; font-weight: bold; font-size: 1.2rem; }
    .price-up { color: #c0392b; font-size: 0.9rem; } /* Fiyat arttı rengi */
    .price-down { color: #27ae60; font-size: 0.9rem; } /* Fiyat düştü rengi */
    
    .category-badge {
        background-color: #f0f2f6; padding: 4px 10px; border-radius: 20px;
        font-size: 0.75rem; color: #555; display: inline-block; margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. AKILLI FONKSİYONLAR ---

@st.cache_data(ttl=3600) # 1 saatlik önbellek
def scrape_product_info(url):
    """Linkten İsim, Resim ve FİYAT çekmeye çalışır"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Başlık
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else soup.title.string
        
        # 2. Resim
        og_image = soup.find("meta", property="og:image")
        img_url = og_image["content"] if og_image else "https://via.placeholder.com/300?text=Görsel+Yok"
        
        # 3. Fiyat (Zor kısım - Genelleştirilmiş Arama)
        price = 0
        # Çeşitli fiyat meta etiketlerini dene
        price_meta = soup.find("meta", property="product:price:amount")
        if price_meta:
            price = float(price_meta["content"])
        else:
            # Yaygın class isimlerini ara (prc-dsc, product-price, price vb.)
            # Bu kısım her site için tutmayabilir, manuel düzeltme gerekir.
            pass 
            
        return title.strip(), img_url, price
    except:
        return "Ürün", "https://via.placeholder.com/300?text=Hata", 0

def check_password():
    if "auth" not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.title("🔒 Giriş")
            pwd = st.text_input("Şifre", type="password")
            if st.button("Devam Et", use_container_width=True):
                if pwd == "2024": # ŞİFRE
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Hatalı şifre")
        return False
    return True

if not check_password(): st.stop()

# --- 3. VERİ YÖNETİMİ ---
if 'data' not in st.session_state:
    st.session_state.data = [] # Tüm harcamalar burada

# Kategoriler
CAT_EV = ["Salon", "Mutfak", "Yatak Odası", "Banyo", "Elektronik", "Beyaz Eşya"]
CAT_DUGUN = ["Organizasyon", "Gelinlik/Damatlık", "Fotoğraf", "Balayı", "Diğer"]

# --- 4. ARAYÜZ ---

# Üst Bilgi Paneli (Dashboard)
total_spent = sum(item['fiyat'] for item in st.session_state.data)
total_items = len(st.session_state.data)

st.markdown(f"""
<div style="text-align:center; padding: 20px;">
    <h1>Büşra & Kerem Wedding Planner</h1>
    <p style="color:#7f8c8d;">Büyük güne hazırlık...</p>
</div>
""", unsafe_allow_html=True)

# Özet Kartları
col1, col2, col3 = st.columns(3)
col1.markdown(f"""<div class="metric-card"><div class="metric-value">{total_spent:,.0f} TL</div><div class="metric-label">Toplam Harcama</div></div>""", unsafe_allow_html=True)
col2.markdown(f"""<div class="metric-card"><div class="metric-value">{total_items}</div><div class="metric-label">Alınan / Planlanan</div></div>""", unsafe_allow_html=True)
col3.markdown(f"""<div class="metric-card"><div class="metric-value">0 TL</div><div class="metric-label">Kalan Bütçe (Ayarla)</div></div>""", unsafe_allow_html=True)

st.divider()

# --- YENİ EKLEME MODÜLÜ (Sekmeli) ---
st.subheader("➕ Listeye Ekle")
add_tab1, add_tab2 = st.tabs(["🏡 Ev Eşyası (Linkli)", "💍 Düğün Masrafı (Manuel)"])

with add_tab1:
    with st.form("ev_form"):
        c1, c2, c3 = st.columns([3, 2, 2])
        url = c1.text_input("Ürün Linki")
        cat = c2.selectbox("Oda/Kategori", CAT_EV)
        manual_price = c3.number_input("Fiyat (Otomatik Çekemezse)", min_value=0)
        
        if st.form_submit_button("Eşyayı Ekle"):
            with st.spinner("Siteden bilgiler alınıyor..."):
                title, img, scraped_price = scrape_product_info(url)
                final_price = scraped_price if scraped_price > 0 else manual_price
                
                st.session_state.data.append({
                    "id": datetime.now().timestamp(),
                    "tur": "Ev",
                    "baslik": title,
                    "kategori": cat,
                    "fiyat": final_price,
                    "ilk_fiyat": final_price, # Değişimi görmek için
                    "img": img,
                    "url": url,
                    "tarih": datetime.now().strftime("%d.%m.%Y")
                })
            st.success("Eklendi!")
            st.rerun()

with add_tab2:
    with st.form("dugun_form"):
        c1, c2, c3 = st.columns([3, 2, 2])
        item_name = c1.text_input("Harcama Adı (Örn: Fotoğrafçı)")
        cat_d = c2.selectbox("Kategori", CAT_DUGUN)
        price_d = c3.number_input("Tutar", min_value=0)
        
        if st.form_submit_button("Masrafı Ekle"):
            st.session_state.data.append({
                "id": datetime.now().timestamp(),
                "tur": "Düğün",
                "baslik": item_name,
                "kategori": cat_d,
                "fiyat": price_d,
                "ilk_fiyat": price_d,
                "img": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&q=80&w=300", # Varsayılan düğün görseli
                "url": "#",
                "tarih": datetime.now().strftime("%d.%m.%Y")
            })
            st.success("Hayırlı olsun!")
            st.rerun()

st.divider()

# --- LİSTELEME VE FİYAT KONTROLÜ ---
col_head, col_btn = st.columns([4, 1])
with col_head: st.subheader("📋 Harcama Listesi")
with col_btn:
    if st.button("🔄 Fiyatları Güncelle"):
        with st.status("Fiyatlar kontrol ediliyor...", expanded=True) as status:
            updated_count = 0
            for item in st.session_state.data:
                if item["url"] and item["url"].startswith("http"):
                    # Burada tekrar scraping yapılır
                    # Demo amaçlı rastgele değişim simülasyonu yapıyorum
                    # Gerçekte: _, _, new_price = scrape_product_info(item['url'])
                    
                    # SİMÜLASYON (Bunu gerçekte kaldıracağız):
                    change = random.choice([0, 0, -100, 500]) 
                    if change != 0:
                        item['fiyat'] += change
                        updated_count += 1
                        st.write(f"{item['baslik']} fiyatı güncellendi!")
                        
            status.update(label=f"{updated_count} ürünün fiyatı güncellendi!", state="complete")
        time.sleep(1)
        st.rerun()

# Listeyi Göster
tabs = st.tabs(["HEPSİ", "🏡 EV EŞYALARI", "💍 DÜĞÜN GİDERLERİ"])

def draw_grid(items):
    if not items:
        st.info("Bu alanda henüz kayıt yok.")
        return
        
    cols = st.columns(3)
    for i, item in enumerate(reversed(items)):
        with cols[i % 3]:
            # Fiyat Değişimi Analizi
            diff = item['fiyat'] - item.get('ilk_fiyat', item['fiyat'])
            trend_html = ""
            if diff < 0:
                trend_html = f"<span class='price-down'>▼ {abs(diff)} TL düştü!</span>"
            elif diff > 0:
                trend_html = f"<span class='price-up'>▲ {diff} TL arttı</span>"
            
            st.markdown(f"""
            <div class="product-card">
                <div style="height:180px; overflow:hidden; border-radius:10px; display:flex; align-items:center; justify-content:center;">
                    <img src="{item['img']}" style="max-height:100%; max-width:100%;">
                </div>
                <div style="margin-top:10px;">
                    <span class="category-badge">{item['kategori']}</span>
                    <h4 style="margin:5px 0; height:45px; overflow:hidden;">{item['baslik']}</h4>
                    <div style="display:flex; justify-content:space-between; align-items:end;">
                        <div>
                            <div class="price-tag">{item['fiyat']:,.0f} TL</div>
                            {trend_html}
                        </div>
                        <div style="color:#aaa; font-size:0.8rem;">{item['tarih']}</div>
                    </div>
                    {'<a href="'+item['url']+'" target="_blank" style="display:block; text-align:center; margin-top:10px; text-decoration:none; border:1px solid #ddd; padding:5px; border-radius:5px; color:#555;">Ürüne Git</a>' if item['url'] != '#' else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Sil", key=f"del_{item['id']}"):
                st.session_state.data = [x for x in st.session_state.data if x['id'] != item['id']]
                st.rerun()

with tabs[0]: draw_grid(st.session_state.data)
with tabs[1]: draw_grid([x for x in st.session_state.data if x['tur'] == 'Ev'])
with tabs[2]: draw_grid([x for x in st.session_state.data if x['tur'] == 'Düğün'])
