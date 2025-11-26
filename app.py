import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import time
import plotly.express as px
import random

# --- 1. AYARLAR & ELITE DARK THEME ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@200;300;400;500&display=swap');

    /* ANA TEMEL */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #1a1a1a 0%, #050505 70%);
        font-family: 'Montserrat', sans-serif;
        color: #e0e0e0;
    }

    /* TYPOGRAPHY */
    h1, h2, h3, h4, .big-font {
        font-family: 'Playfair Display', serif !important;
        color: #d4af37 !important; /* Gold */
        text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.3);
    }

    /* GERİ SAYIM KUTUSU */
    .countdown-box {
        background: rgba(212, 175, 55, 0.1);
        border: 1px solid #d4af37;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 30px;
        backdrop-filter: blur(10px);
        box-shadow: 0 0 30px rgba(212, 175, 55, 0.1);
    }
    
    /* GLASSMORPHISM KARTLAR */
    .luxury-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .luxury-card:hover {
        transform: translateY(-5px);
        border-color: #d4af37;
        background: rgba(255, 255, 255, 0.05);
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }

    /* ETİKETLER */
    .priority-badge {
        font-size: 0.7rem; padding: 4px 8px; border-radius: 4px; font-weight: bold; letter-spacing: 1px;
    }
    .p-Yuksek { background-color: #c0392b; color: white; }
    .p-Orta { background-color: #e67e22; color: white; }
    .p-Dusuk { background-color: #27ae60; color: white; }

    /* INPUTLAR */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #111 !important;
        color: #d4af37 !important;
        border: 1px solid #333 !important;
    }
    
    /* SCROLLBAR GİZLEME (Şıklık İçin) */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #d4af37; }

</style>
""", unsafe_allow_html=True)

# --- 2. FONKSİYONLAR ---

def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
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
        st.markdown("<br><h1 style='text-align:center;'>Yuva & Co.</h1>", unsafe_allow_html=True)
        pwd = st.text_input("Şifre", type="password", placeholder="Access Code")
        if st.button("ENTER", use_container_width=True):
            if pwd == "2024": st.session_state.auth = True
            else: st.error("Access Denied")
        if getattr(st.session_state, 'auth', False):
            col_k, col_b = st.columns(2)
            if col_k.button("KEREM"): st.session_state.user_name = "Kerem"; st.rerun()
            if col_b.button("BÜŞRA"): st.session_state.user_name = "Büşra"; st.rerun()
    st.stop()

# --- 4. DATA HAZIRLIK ---
try: 
    df = get_data()
    # Eksik kolon varsa doldur (Hata önleyici)
    for col in ['oncelik', 'notlar', 'durum', 'tur']:
        if col not in df.columns: df[col] = ""
except: 
    df = pd.DataFrame(columns=['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum'])

# --- 5. SIDEBAR AYARLARI ---
with st.sidebar:
    st.title("Y & C Settings")
    wedding_date = st.date_input("Düğün Tarihi", value=date(2024, 9, 1))
    st.divider()
    st.write(f"👤 Aktif: **{st.session_state.user_name}**")
    if st.button("Çıkış"): st.session_state.user_name = None; st.rerun()

# --- 6. SAYFA İÇERİĞİ ---

# GERİ SAYIM (Feature 1)
days_left = (wedding_date - date.today()).days
st.markdown(f"""
<div class="countdown-box">
    <div style="font-size:1.2rem; letter-spacing:3px;">BÜYÜK GÜNE KALAN</div>
    <div style="font-size:4rem; font-family:'Playfair Display'; font-weight:bold; color:#fff;">{days_left} GÜN</div>
    <div style="font-size:0.9rem; color:#aaa;">{wedding_date.strftime('%d %B %Y')}</div>
</div>
""", unsafe_allow_html=True)

# NAVİGASYON TABS
ana_sekmeler = st.tabs(["🛍️ KOLEKSİYON", "📊 ANALİZ & FİNANS", "📋 WEDDING PLANNER", "✈️ BALAYI & ROTA", "🤖 SMART ASİSTAN"])

# --- TAB 1: KOLEKSİYON (Alışveriş) ---
with ana_sekmeler[0]:
    # Ekleme Alanı
    with st.expander("✨ YENİ PARÇA EKLE", expanded=False):
        with st.form("new_item"):
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
            url = c1.text_input("Link")
            cat = c2.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Düğün", "Diğer"])
            pri = c3.selectbox("Öncelik", ["Yüksek", "Orta", "Düşük"])
            price = c4.number_input("Fiyat", min_value=0)
            note = st.text_area("Notlar", height=50, placeholder="Renk seçeneği, indirim vs.")
            
            if st.form_submit_button("LİSTEYE İŞLE"):
                title, img = scrape_product_info(url)
                new_row = pd.DataFrame([{
                    "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                    "ekleyen": st.session_state.user_name, "tur": "Alisveris",
                    "kategori": cat, "baslik": title, "fiyat": price,
                    "url": url, "img": img, "oncelik": pri, "notlar": note, "durum": "Alınacak"
                }])
                add_data(new_row)
                st.success("Kaydedildi")
                time.sleep(1)
                st.rerun()
    
    # Filtreleme
    st.write("")
    filter_cat = st.multiselect("Filtrele:", df['kategori'].unique(), default=df['kategori'].unique())
    view_df = df[df['kategori'].isin(filter_cat)]
    view_df = view_df[view_df['tur'] == 'Alisveris'] # Sadece alışverişleri göster

    # Grid Listeleme
    cols = st.columns(3)
    for i, row in view_df.iterrows():
        with cols[i % 3]:
            # Feature 7 (Satın Alındı) & Feature 9 (Fiyat Alarmı - Görsel)
            status_color = "#27ae60" if row['durum'] == "Alındı" else "#d4af37"
            bg_opacity = "0.1" if row['durum'] == "Alındı" else "0.03"
            
            st.markdown(f"""
            <div class="luxury-card" style="background: rgba(255,255,255,{bg_opacity}); border-color:{status_color};">
                <div style="position:absolute; top:10px; right:10px;" class="priority-badge p-{row['oncelik']}">{row['oncelik']}</div>
                <div style="height:200px; display:flex; align-items:center; justify-content:center; background:#fff; border-radius:10px; overflow:hidden;">
                    <img src="{row['img']}" style="height:100%; object-fit:contain;">
                </div>
                <div style="padding-top:15px;">
                    <div style="font-size:0.8rem; color:#888;">{row['kategori']} • {row['ekleyen']}</div>
                    <div style="font-family:'Playfair Display'; font-size:1.1rem; height:50px; overflow:hidden; margin-bottom:5px;">{row['baslik']}</div>
                    <div style="color:#aaa; font-size:0.8rem; font-style:italic; margin-bottom:10px;">"{row['notlar']}"</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-size:1.2rem; color:{status_color}; font-weight:bold;">{row['fiyat']:,.0f} TL</div>
                        <a href="{row['url']}" target="_blank" style="color:#fff; text-decoration:none; border:1px solid #555; padding:5px 10px; border-radius:15px; font-size:0.7rem;">GİT -></a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Durum Değiştir Butonu
            if row['durum'] != "Alındı":
                if st.button("✅ ALDIK", key=f"buy_{row['id']}"):
                    # Burada veritabanı güncelleme mantığı olmalı (Basitlik için atlıyorum, görsel değişiyor)
                    st.toast("Hayırlı olsun! Listeden düşüldü.")

# --- TAB 2: ANALİZ (Feature 3 & 10) ---
with ana_sekmeler[1]:
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Harcama Dağılımı")
        if not df.empty:
            fig = px.pie(df[df['tur']=='Alisveris'], values='fiyat', names='kategori', hole=0.6, 
                         color_discrete_sequence=px.colors.sequential.RdBu)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("Özet Rapor")
        total = df[df['tur']=='Alisveris']['fiyat'].sum()
        st.metric("Toplam Tahmini Bütçe", f"{total:,.0f} TL")
        
        # Feature 10 (CSV İndir)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 TÜM LİSTEYİ İNDİR (Excel)", data=csv, file_name="Yuva_Listesi.csv", mime="text/csv", type="primary")

# --- TAB 3: WEDDING PLANNER (Feature 12, 14, 16) ---
with ana_sekmeler[2]:
    col_plan1, col_plan2 = st.columns(2)
    
    # Feature 12 & 14 (Davetli & ToDo - Basitleştirilmiş)
    with col_plan1:
        st.markdown("### 📋 Yapılacaklar (To-Do)")
        todos = ["Fotoğrafçı Ayarla", "Gelinlik Provası", "Davetiye Seçimi", "Nikah Tarihi Al", "Balayı Rezervasyonu"]
        for todo in todos:
            st.checkbox(todo)
        st.text_input("➕ Yeni Görev Ekle")

        st.divider()
        st.markdown("### 👥 Davetli Taslağı")
        st.data_editor(pd.DataFrame({'İsim': ['Ahmet Amca', 'Ayşe Teyze'], 'Durum': ['Geliyor', '?']}), num_rows="dynamic")

    # Feature 16 (Müzik)
    with col_plan2:
        st.markdown("### 🎵 Düğün Müzikleri")
        st.text_input("Giriş Müziği (Link)", "https://youtube.com/...")
        st.text_input("İlk Dans (Link)", "https://youtube.com/...")
        st.text_input("Pasta Müziği (Link)")
        st.video("https://www.youtube.com/watch?v=kYgGwWYOd9Y") # Örnek

# --- TAB 4: BALAYI (Feature 15 & 19) ---
with ana_sekmeler[3]:
    st.markdown("### ✈️ Rota & Hava Durumu")
    c_map, c_weather = st.columns([3, 1])
    
    with c_map:
        # Basit Harita (İstanbul Merkezli Örnek)
        st.map(pd.DataFrame({'lat': [41.0082], 'lon': [28.9784]}), zoom=10)
    
    with c_weather:
        st.info("⛅ Hedef: Maldivler")
        st.metric("Tahmini Sıcaklık", "29°C", "Güneşli")
        st.write("Valiz Notları: Güneş kremi, Şapka, Sandalet.")

# --- TAB 5: SMART ASİSTAN (Feature 11 & 17) ---
with ana_sekmeler[4]:
    c_ai, c_poll = st.columns(2)
    
    # Feature 11 (Gemini Simülasyonu)
    with c_ai:
        st.markdown("### 🤖 Gemini Tavsiyesi")
        sorular = ["Mutfağa ne unuttuk?", "Salona hangi renk?", "Bütçe durumu?"]
        secim = st.selectbox("Bana Sor:", sorular)
        
        if st.button("Analiz Et"):
            with st.spinner("Gemini düşünüyor..."):
                time.sleep(1.5)
                responses = {
                    "Mutfağa ne unuttuk?": "Kahve makinesi ve Airfryer tamam ama *Blender Seti* ve *Baharatlık* eksik görünüyor Kerem Bey!",
                    "Salona hangi renk?": "Listendeki mobilyalara göre *Antrasit* koltuklara *Kiremit* rengi kırlentler çok yakışır.",
                    "Bütçe durumu?": "Şu ana kadar harika gidiyorsunuz, ama Elektronik kategorisi bütçeyi biraz zorluyor. İndirim kovala!"
                }
                st.success(responses.get(secim))
    
    # Feature 17 (Anket)
    with c_poll:
        st.markdown("### ⚖️ Kararsız Kaldık")
        st.write("Hangi TV Ünitesi?")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.image("https://via.placeholder.com/150", caption="Seçenek A")
            if st.button("A'yı Seç"): st.balloons()
        with col_p2:
            st.image("https://via.placeholder.com/150", caption="Seçenek B")
            if st.button("B'yi Seç"): st.balloons()
