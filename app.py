import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# --- 1. AYARLAR & TASARIM ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lato:wght@300;400;700&display=swap');
    .stApp { background-color: #f8f9fa; font-family: 'Lato', sans-serif; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: #2c3e50; }
    
    .product-card {
        background-color: white; padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 1px solid #eee; transition: transform 0.2s; position: relative;
    }
    .product-card:hover { transform: translateY(-5px); border-color: #d4af37; }
    
    .owner-badge {
        position: absolute; top: 10px; right: 10px;
        padding: 4px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase;
    }
    .badge-Kerem { background-color: #e3f2fd; color: #1565c0; }
    .badge-Büşra { background-color: #fce4ec; color: #c2185b; }
    
    .price-tag { color: #27ae60; font-weight: bold; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# --- 2. FONKSİYONLAR ---

def get_data():
    """Google Sheets'ten verileri çeker"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Cache süresini kısa tutuyoruz ki Büşra ekleyince hemen gör
    return conn.read(ttl=5) 

def add_data(new_row_df):
    """Google Sheets'e yeni satır ekler"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0) # Güncel veriyi al
    updated_df = pd.concat([df, new_row_df], ignore_index=True)
    conn.update(worksheet="Sayfa1", data=updated_df)

@st.cache_data(ttl=3600)
def scrape_product_info(url):
    """Linkten bilgi çeker"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else "Yeni Ürün"
        
        og_image = soup.find("meta", property="og:image")
        img = og_image["content"] if og_image else "https://via.placeholder.com/300"
        
        return title.strip(), img
    except:
        return "Bilinmeyen Ürün", "https://via.placeholder.com/300"

# --- 3. GİRİŞ VE KİMLİK SEÇİMİ ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if not st.session_state.user_name:
    st.markdown("<h1 style='text-align:center;'>Hoşgeldiniz</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        pwd = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if pwd == "2024": # Şifre
                st.session_state.auth = True
            else:
                st.error("Şifre Yanlış")
                st.stop()
        
        if getattr(st.session_state, 'auth', False):
            st.success("Giriş Başarılı! Peki sen kimsin?")
            col_k, col_b = st.columns(2)
            if col_k.button("🤵🏻‍♂️ Ben Kerem"):
                st.session_state.user_name = "Kerem"
                st.rerun()
            if col_b.button("👰🏻‍♀️ Ben Büşra"):
                st.session_state.user_name = "Büşra"
                st.rerun()
    st.stop()

# --- 4. ANA UYGULAMA ---

# Kullanıcı Karşılama
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding:10px;">
    <h3>Yuva & Co.</h3>
    <div>
        <span style="background:#eee; padding:5px 10px; border-radius:15px;">👤 {st.session_state.user_name}</span>
        <button onclick="window.location.reload()" style="border:none; background:none; cursor:pointer;">🔄 Yenile</button>
    </div>
</div>
""", unsafe_allow_html=True)

# Veriyi Çek
try:
    df = get_data()
except Exception as e:
    st.error("Veritabanına bağlanamadım. 'Secrets' ayarlarını kontrol et.")
    st.stop()

# Dashboard
total_spent = df['fiyat'].sum() if not df.empty else 0
c1, c2, c3 = st.columns(3)
c1.metric("Toplam Tutar", f"{total_spent:,.0f} TL")
c2.metric("Toplam Parça", len(df))
c3.metric("Son Ekleyen", df.iloc[-1]['ekleyen'] if not df.empty else "-")

st.divider()

# Ekleme Alanı
with st.expander("➕ Yeni Ekle (Ortak Listeye Gider)"):
    with st.form("add_form"):
        c1, c2, c3 = st.columns([3, 2, 2])
        url = c1.text_input("Link")
        kategori = c2.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Banyo", "Elektronik", "Düğün", "Diğer"])
        fiyat = c3.number_input("Fiyat", min_value=0)
        
        if st.form_submit_button("Listeye İşle"):
            with st.spinner("Kaydediliyor..."):
                title, img = scrape_product_info(url)
                
                new_data = pd.DataFrame([{
                    "id": str(int(time.time())),
                    "tarih": datetime.now().strftime("%d.%m.%Y"),
                    "ekleyen": st.session_state.user_name,
                    "tur": "Ev" if kategori != "Düğün" else "Düğün",
                    "kategori": kategori,
                    "baslik": title,
                    "fiyat": fiyat,
                    "url": url,
                    "img": img
                }])
                
                add_data(new_data)
                st.success("Kaydedildi! Büşra da artık bunu görebilir.")
                time.sleep(1)
                st.rerun()

# Listeleme
tabs = st.tabs(["TÜM LİSTE", "BENİM EKLEDİKLERİM", "ONUN EKLEDİKLERİ"])

def show_grid(dataframe):
    if dataframe.empty:
        st.info("Burada henüz bir şey yok.")
        return
    
    cols = st.columns(3)
    for i, row in dataframe.iterrows():
        with cols[i % 3]:
            # Kim Ekledi Rozeti
            badge_class = f"badge-{row['ekleyen']}" if row['ekleyen'] in ['Kerem', 'Büşra'] else "badge-Kerem"
            
            st.markdown(f"""
            <div class="product-card">
                <span class="owner-badge {badge_class}">{row['ekleyen']}</span>
                <div style="height:180px; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                    <img src="{row['img']}" style="max-height:100%; max-width:100%;">
                </div>
                <div style="margin-top:10px;">
                    <small style="color:#888;">{row['kategori']} • {row['tarih']}</small>
                    <h4 style="margin:5px 0; font-size:1rem; height:40px; overflow:hidden;">{row['baslik']}</h4>
                    <div class="price-tag">{row['fiyat']:,.0f} TL</div>
                    <a href="{row['url']}" target="_blank" style="display:block; margin-top:10px; text-decoration:none; color:#333; font-weight:bold; font-size:0.8rem;">ÜRÜNE GİT →</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tabs[0]:
    show_grid(df.iloc[::-1]) # En son eklenen en başta
with tabs[1]:
    show_grid(df[df['ekleyen'] == st.session_state.user_name].iloc[::-1])
with tabs[2]:
    other_user = "Büşra" if st.session_state.user_name == "Kerem" else "Kerem"
    show_grid(df[df['ekleyen'] == other_user].iloc[::-1])
