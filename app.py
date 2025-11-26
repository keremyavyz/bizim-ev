import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 1. AYARLAR VE STİL (Görselliği Burası Düzeltecek) ---
st.set_page_config(page_title="Yuva & Co.", page_icon="🏠", layout="wide")

# Modern CSS Tasarımı
st.markdown("""
<style>
    /* Genel Arka Plan */
    .stApp {background-color: #f0f2f6;}
    
    /* Kart Tasarımı */
    .product-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    
    /* Resim Çerçevesi - Resmi Sığdırma Ayarı */
    .img-container {
        width: 100%;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #fff;
        border-radius: 8px;
        margin-bottom: 10px;
        overflow: hidden;
    }
    
    .product-img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain; /* Resmi kesmeden sığdırır */
    }

    /* Yazı Tipleri */
    h4 {font-size: 1rem; margin-bottom: 5px; color: #333;}
    .price {color: #27ae60; font-weight: bold; font-size: 1.1rem;}
    .date {color: #95a5a6; font-size: 0.8rem;}
    
    /* Sekme Tasarımı */
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {height: 50px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- 2. FONKSİYONLAR ---

@st.cache_data
def get_link_preview(url):
    """Linkten resim ve başlık çeker"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Görseli en iyi şekilde bulmaya çalış
        og_image = soup.find("meta", property="og:image")
        if og_image:
            img_url = og_image["content"]
        else:
            # Alternatif resim bulma
            img_tag = soup.find("img")
            img_url = img_tag['src'] if img_tag else "https://via.placeholder.com/300?text=Resim+Yok"

        # Başlık
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else soup.title.string
        
        return title.strip(), img_url
    except:
        return "Ürün Bilgisi Alınamadı", "https://via.placeholder.com/300?text=Hata"

# Şifre Kontrolü (Büşra & Kerem)
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        st.write("### 🔒 Giriş")
        pwd = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap"):
            if pwd == "2024": # Şifreniz
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Hatalı şifre!")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. VERİ YÖNETİMİ ---
if 'urunler' not in st.session_state:
    st.session_state.urunler = []

# Kategori Listesi
KATEGORILER = ["Salon", "Mutfak", "Yatak Odası", "Banyo", "Elektronik", "Ortak", "Bohça"]

# --- 4. ARAYÜZ ---

# Başlık Alanı
c_logo, c_title = st.columns([1, 8])
with c_title:
    st.title("Büşra & Kerem Home 🏠")

# --- ÜRÜN EKLEME ALANI (Genişletilebilir Menü) ---
with st.expander("➕ Yeni Ürün Ekle", expanded=False):
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    
    url_input = c1.text_input("Link", placeholder="https://...")
    cat_input = c2.selectbox("Bölüm", KATEGORILER)
    price_input = c3.number_input("Fiyat", min_value=0, step=100)
    
    if c4.button("Ekle", type="primary", use_container_width=True):
        if url_input:
            with st.spinner("Bilgiler çekiliyor..."):
                title, img = get_link_preview(url_input)
                st.session_state.urunler.append({
                    "id": datetime.now().timestamp(), # Silmek için benzersiz ID
                    "title": title,
                    "url": url_input,
                    "img": img,
                    "price": price_input,
                    "category": cat_input,
                    "date": datetime.now().strftime("%d.%m.%Y")
                })
            st.success("Listeye eklendi!")
            st.rerun()

st.divider()

# --- VİTRİN VE SEKMELER ---

# Sekmeleri Oluştur
tabs = st.tabs(["Tümü"] + KATEGORILER)

# Her sekme için içeriği doldur
for i, tab_name in enumerate(["Tümü"] + KATEGORILER):
    with tabs[i]:
        # Odaya göre filtrele
        if tab_name == "Tümü":
            gosterilecekler = st.session_state.urunler
        else:
            gosterilecekler = [u for u in st.session_state.urunler if u["category"] == tab_name]
        
        if not gosterilecekler:
            st.info(f"{tab_name} için henüz bir şey eklenmemiş.")
        else:
            # Grid Sistemi (3'lü kolon)
            cols = st.columns(3)
            for index, urun in enumerate(reversed(gosterilecekler)):
                col = cols[index % 3]
                with col:
                    # HTML Kart Yapısı
                    st.markdown(f"""
                    <div class="product-card">
                        <div class="img-container">
                            <img src="{urun['img']}" class="product-img">
                        </div>
                        <h4>{urun['title'][:40]}...</h4>
                        <p class="price">{urun['price']} TL</p>
                        <p class="date">📅 {urun['date']}</p>
                        <a href="{urun['url']}" target="_blank" style="text-decoration:none; color:#3498db; font-weight:bold; font-size:0.9rem;">Ürüne Git 🔗</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Silme Butonu (HTML içinde çalışmaz, Streamlit butonu olmak zorunda)
                    if st.button("🗑️ Sil", key=f"del_{urun['id']}"):
                        st.session_state.urunler = [u for u in st.session_state.urunler if u['id'] != urun['id']]
                        st.rerun()
