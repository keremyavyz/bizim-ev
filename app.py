import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 1. GÜVENLİK VE AYARLAR ---
st.set_page_config(page_title="Yuva & Co.", page_icon="🏠", layout="wide")

# ŞİFREYİ BURADAN DEĞİŞTİREBİLİRSİN
GIRIS_SIFRESI = "2024" 

def check_password():
    """Basit şifre kontrolü"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        st.title("🔒 Büşra & Kerem'in Evi")
        pwd = st.text_input("Giriş Şifresi", type="password")
        if st.button("Giriş Yap"):
            if pwd == GIRIS_SIFRESI:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Şifre yanlış!")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. GÖRSEL TASARIM (CSS) ---
st.markdown("""
<style>
    .stApp {background-color: #f8f9fa;}
    .product-card {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .product-card:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 15px rgba(0,0,0,0.15);
    }
    .price-tag {color: #2e7d32; font-weight: bold; font-size: 1.1em;}
    .status-badge {background-color: #e3f2fd; color: #1565c0; padding: 4px 8px; border-radius: 10px; font-size: 0.7em;}
</style>
""", unsafe_allow_html=True)

# --- 3. LİNKTEN BİLGİ ÇEKME FONKSİYONU ---
@st.cache_data
def get_link_preview(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Görsel bul
        og_image = soup.find("meta", property="og:image")
        img_url = og_image["content"] if og_image else "https://via.placeholder.com/300x200?text=Gorsel+Yok"
        
        # Başlık bul
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else "Yeni Ürün"
        
        return title, img_url
    except:
        return "Bilinmeyen Ürün", "https://via.placeholder.com/300x200?text=Hata"

# --- 4. ARAYÜZ ---
st.title("🏠 Yuva & Co. - Alınacaklar Listesi")
st.caption("Link yapıştır, gerisini bana bırak.")

# Veri Saklama (Geçici Hafıza)
if 'urunler' not in st.session_state:
    st.session_state.urunler = []

# Yeni Ürün Ekleme Paneli
with st.container():
    c1, c2, c3 = st.columns([3, 1, 1])
    link = c1.text_input("Ürün Linki", placeholder="https://...")
    fiyat = c2.number_input("Fiyat (TL)", min_value=0, step=100)
    
    if c3.button("Ekle ✨", type="primary", use_container_width=True):
        if link:
            with st.spinner("Ürün taranıyor..."):
                baslik, gorsel = get_link_preview(link)
                st.session_state.urunler.append({
                    "baslik": baslik, "fiyat": fiyat, 
                    "link": link, "img": gorsel,
                    "tarih": datetime.now().strftime("%d-%m-%Y")
                })
            st.success("Eklendi!")

st.divider()

# Ürünleri Listeleme (Kart Görünümü)
if st.session_state.urunler:
    cols = st.columns(3)
    for i, urun in enumerate(reversed(st.session_state.urunler)):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="product-card">
                <img src="{urun['img']}" style="width:100%; height:180px; object-fit:cover; border-radius:10px;">
                <h5 style="margin:10px 0; height:40px; overflow:hidden;">{urun['baslik'][:50]}...</h5>
                <div style="display:flex; justify-content:space-between;">
                    <span class="price-tag">{urun['fiyat']} TL</span>
                    <span class="status-badge">{urun['tarih']}</span>
                </div>
                <a href="{urun['link']}" target="_blank" style="display:block; margin-top:10px; text-decoration:none; color:#1565c0; font-weight:bold;">Ürüne Git →</a>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Henüz listen boş. Yukarıdan ilk ürününü ekle!")
