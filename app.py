import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import time
import plotly.express as px

# --- 1. AYARLAR & ELITE DARK THEME ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@200;300;400;500&display=swap');

    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #1a1a1a 0%, #050505 70%);
        font-family: 'Montserrat', sans-serif;
        color: #e0e0e0;
    }

    h1, h2, h3, h4, .big-font {
        font-family: 'Playfair Display', serif !important;
        color: #d4af37 !important;
        text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.3);
    }

    /* LÜKS GERİ SAYIM KUTUSU */
    .countdown-box {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(0,0,0,0.4) 100%);
        border: 1px solid #d4af37;
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 0 0 40px rgba(212, 175, 55, 0.15);
        position: relative;
        overflow: hidden;
    }
    
    .luxury-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .luxury-card:hover {
        transform: translateY(-5px);
        border-color: #d4af37;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }

    .badge {
        position: absolute; top: 15px; right: 15px;
        padding: 5px 10px; border-radius: 30px; font-size: 0.7rem; font-weight: bold;
    }
    .badge-Kerem { background: #2980b9; color: white; }
    .badge-Büşra { background: #c0392b; color: white; }

    /* FORM ELEMANLARI */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
        background-color: #111 !important;
        color: #d4af37 !important; 
        border: 1px solid #444 !important;
    }
    
    /* SCROLLBAR */
    ::-webkit-scrollbar { width: 10px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. FONKSİYONLAR ---

def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ttl=0 means no cache, instant updates
    return conn.read(ttl=0)

def add_data(new_row_df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    updated_df = pd.concat([df, new_row_df], ignore_index=True)
    conn.update(worksheet="Sayfa1", data=updated_df)

@st.cache_data(ttl=3600)
def scrape_product_info(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else "Ürün"
        og_image = soup.find("meta", property="og:image")
        img = og_image["content"] if og_image else "https://via.placeholder.com/400x300/000000/FFFFFF?text=Yuva+Co"
        return title.strip(), img
    except:
        return "Manuel Giriş", "https://via.placeholder.com/400x300/000000/FFFFFF?text=Hata"

# --- 3. LOGIN ---
if "user_name" not in st.session_state: st.session_state.user_name = None
if not st.session_state.user_name:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center;'>Yuva & Co.</h1>", unsafe_allow_html=True)
        pwd = st.text_input("Şifre", type="password", placeholder="Access Code")
        if st.button("GİRİŞ", use_container_width=True):
            if pwd == "2024": st.session_state.auth = True
            else: st.error("Hatalı Şifre")
        if getattr(st.session_state, 'auth', False):
            col_k, col_b = st.columns(2)
            if col_k.button("KEREM"): st.session_state.user_name = "Kerem"; st.rerun()
            if col_b.button("BÜŞRA"): st.session_state.user_name = "Büşra"; st.rerun()
    st.stop()

# --- 4. DATA HAZIRLIK ---
try: 
    df = get_data()
    # Eksik kolon kontrolü
    for col in ['oncelik', 'notlar', 'durum', 'tur']:
        if col not in df.columns: df[col] = ""
except: 
    df = pd.DataFrame(columns=['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum'])

# --- 5. ÜST BİLGİ VE GERİ SAYIM ---
st.markdown(f"<div style='text-align:right; color:#777; font-size:0.8rem;'>Kullanıcı: {st.session_state.user_name}</div>", unsafe_allow_html=True)

# SABİTLENMİŞ TARİH: 25 NİSAN 2026
TARGET_DATE = date(2026, 4, 25)
days_left = (TARGET_DATE - date.today()).days

st.markdown(f"""
<div class="countdown-box">
    <div style="font-size:1rem; letter-spacing:4px; color:#d4af37; margin-bottom:10px;">BÜŞRA & KEREM WEDDING</div>
    <div style="font-size:5rem; font-family:'Playfair Display'; font-weight:bold; color:#fff; line-height:1;">{days_left}</div>
    <div style="font-size:1.2rem; color:#888;">GÜN KALDI</div>
    <div style="margin-top:15px; font-size:0.9rem; color:#555;">Target: 25 Nisan 2026</div>
</div>
""", unsafe_allow_html=True)

# --- 6. İÇERİK SEKMELERİ ---
tabs = st.tabs(["🛍️ LİSTEMİZ", "📊 DURUM ANALİZİ", "📋 PLANLAYICI", "✈️ ROTA", "🤖 ASİSTAN"])

# TAB 1: ALIŞVERİŞ LİSTESİ
with tabs[0]:
    with st.expander("➕ YENİ ÜRÜN EKLE", expanded=False):
        with st.form("add_item"):
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
            url = c1.text_input("Link")
            cat = c2.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            pri = c3.selectbox("Öncelik", ["Yüksek", "Orta", "Düşük"])
            price = c4.number_input("Fiyat", min_value=0)
            note = st.text_area("Not", height=50, placeholder="Renk, Beden vb.")
            
            if st.form_submit_button("LİSTEYE KAYDET"):
                title, img = scrape_product_info(url)
                new_row = pd.DataFrame([{
                    "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                    "ekleyen": st.session_state.user_name, "tur": "Alisveris",
                    "kategori": cat, "baslik": title, "fiyat": price,
                    "url": url, "img": img, "oncelik": pri, "notlar": note, "durum": "Alınacak"
                }])
                add_data(new_row)
                st.success("Kaydedildi!")
                time.sleep(1)
                st.rerun()

    # Listeleme
    filter_cat = st.multiselect("Kategori Filtrele", df['kategori'].unique(), default=df['kategori'].unique())
    view_df = df[(df['kategori'].isin(filter_cat)) & (df['tur'] == 'Alisveris')]
    
    cols = st.columns(3)
    for i, row in view_df.iterrows():
        with cols[i % 3]:
            # Rozet Rengi
            badge_cls = f"badge-{row['ekleyen']}" if row['ekleyen'] in ['Kerem', 'Büşra'] else "badge-Kerem"
            opacity = "0.4" if row['durum'] == "Alındı" else "1"
            
            st.markdown(f"""
            <div class="luxury-card" style="opacity:{opacity};">
                <span class="badge {badge_cls}">{row['ekleyen']}</span>
                <div style="height:200px; display:flex; align-items:center; justify-content:center; background:#fff; border-radius:8px; overflow:hidden;">
                    <img src="{row['img']}" style="height:100%; object-fit:contain;">
                </div>
                <div style="margin-top:15px;">
                    <small style="color:#d4af37;">{row['kategori'].upper()} • {row['oncelik']} ÖNCELİK</small>
                    <div style="font-family:'Playfair Display'; font-size:1.1rem; height:50px; overflow:hidden; margin:5px 0;">{row['baslik']}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:1.3rem; font-weight:bold; color:#fff;">{row['fiyat']:,.0f} TL</span>
                        <a href="{row['url']}" target="_blank" style="color:#d4af37; border:1px solid #d4af37; padding:5px 10px; border-radius:10px; text-decoration:none; font-size:0.8rem;">İNCELE</a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# TAB 2: ANALİZ
with tabs[1]:
    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("Bütçe Dağılımı")
        if not df.empty:
            fig = px.pie(df[df['tur']=='Alisveris'], values='fiyat', names='kategori', hole=0.5, 
                         color_discrete_sequence=px.colors.sequential.RdBu)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        total = df[df['tur']=='Alisveris']['fiyat'].sum()
        st.metric("TOPLAM HARCAMA", f"{total:,.0f} TL")
        st.info("Döviz Kuru (Demo): 1 USD = 34.20 TL")

# TAB 3: PLANLAYICI (To-Do & Davetli)
with tabs[2]:
    c_todo, c_davet = st.columns(2)
    with c_todo:
        st.markdown("### ✅ Yapılacaklar")
        st.checkbox("Gelinlik Provası")
        st.checkbox("Damaklık Seçimi")
        st.checkbox("Balayı Biletleri")
        st.text_input("Yeni Görev Ekle")
    with c_davet:
        st.markdown("### 👥 Davetli Taslağı")
        st.data_editor(pd.DataFrame({"İsim": ["Ahmet", "Mehmet"], "Durum": ["Davetiye Gitti", "Bekleniyor"]}), num_rows="dynamic")

# TAB 4: ROTA
with tabs[3]:
    st.markdown("### ✈️ Balayı Rotası")
    st.map(pd.DataFrame({'lat': [41.0082], 'lon': [28.9784]}), zoom=4) # Harita

# TAB 5: ASİSTAN
with tabs[4]:
    st.markdown("### 🤖 Yuva & Co. Asistan")
    if st.button("Listemizi Analiz Et"):
        st.success("Şu ana kadar 'Salon' kategorisine çok ağırlık vermişsiniz. 'Mutfak' biraz eksik kalmış gibi. Airfryer alındı mı?")
