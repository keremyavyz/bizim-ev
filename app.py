import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import time
import plotly.express as px
import re

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

    /* KART TASARIMI */
    .luxury-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 10px; /* Butonlar için boşluk azaldı */
        transition: all 0.3s ease;
        position: relative;
    }
    .luxury-card:hover {
        transform: translateY(-5px);
        border-color: #d4af37;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }

    /* BUTONLAR */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #333;
        background-color: #111;
        color: #aaa;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #d4af37;
        color: #d4af37;
    }

    /* FİYAT ETİKETLERİ */
    .trend-down { color: #2ecc71; font-weight: bold; font-size: 0.9rem; }
    .trend-up { color: #e74c3c; font-weight: bold; font-size: 0.9rem; }
    .trend-neutral { color: #7f8c8d; font-size: 0.8rem; }

    .badge {
        position: absolute; top: 15px; right: 15px;
        padding: 5px 10px; border-radius: 30px; font-size: 0.7rem; font-weight: bold;
    }
    .badge-Kerem { background: #2980b9; color: white; }
    .badge-Büşra { background: #c0392b; color: white; }

    /* INPUTLAR */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #111 !important;
        color: #d4af37 !important; 
        border: 1px solid #444 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FONKSİYONLAR ---

def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn.read(ttl=0)

def update_all_data(df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="Sayfa1", data=df)

# YENİ EKLENEN SİLME FONKSİYONU
def delete_data(item_id):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    # ID'leri string'e çevirerek karşılaştır (Hata önleyici)
    df['id'] = df['id'].astype(str)
    # Seçilen ID dışındakileri tut
    updated_df = df[df['id'] != str(item_id)]
    conn.update(worksheet="Sayfa1", data=updated_df)

def clean_price(price_str):
    if not price_str: return 0
    clean = re.sub(r'[^\d,]', '', str(price_str)) 
    clean = clean.replace(',', '.')
    try: return float(clean)
    except: return 0

@st.cache_data(ttl=600)
def scrape_product_info(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else soup.title.string
        
        og_image = soup.find("meta", property="og:image")
        img = og_image["content"] if og_image else "https://via.placeholder.com/400x300/000000/FFFFFF?text=Yuva+Co"
        
        price = 0
        price_meta = soup.find("meta", property="product:price:amount")
        if price_meta: price = float(price_meta["content"])
        
        if price == 0 and "trendyol" in url:
            prc_tag = soup.find("span", class_="prc-dsc")
            if prc_tag: price = clean_price(prc_tag.text)
            
        if price == 0 and "hepsiburada" in url:
            prc_tag = soup.find("span", itemprop="price")
            if prc_tag: 
                price = float(prc_tag.get("content")) if prc_tag.get("content") else clean_price(prc_tag.text)

        return title.strip(), img, price
    except:
        return "Manuel Giriş", "https://via.placeholder.com/400x300/000000/FFFFFF?text=Hata", 0

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
    required_cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum']
    for col in required_cols:
        if col not in df.columns: df[col] = ""
    
    # ID kolonunu string yap (Silme işlemi için önemli)
    if 'id' in df.columns:
        df['id'] = df['id'].astype(str)

    df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
    df['ilk_fiyat'] = pd.to_numeric(df['ilk_fiyat'], errors='coerce').fillna(0)
    
except: 
    df = pd.DataFrame(columns=required_cols)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Yönetim Paneli")
    st.write(f"Kullanıcı: **{st.session_state.user_name}**")
    st.divider()
    
    if st.button("🔄 Fiyatları Güncelle"):
        progress_bar = st.progress(0)
        status = st.empty()
        new_df = df.copy()
        count = 0
        total = len(df)
        
        for idx, row in new_df.iterrows():
            if row['url'] and str(row['url']).startswith('http') and row['durum'] != "Alındı":
                status.text(f"Taranıyor: {row['baslik'][:15]}...")
                _, _, curr_p = scrape_product_info(row['url'])
                if curr_p > 0:
                    new_df.at[idx, 'fiyat'] = curr_p
                    count += 1
            progress_bar.progress((idx + 1) / total)
            
        update_all_data(new_df)
        status.success(f"Bitti! {count} ürün güncellendi.")
        time.sleep(1)
        st.rerun()

# --- 6. ANA EKRAN ---
TARGET_DATE = date(2026, 4, 25)
days_left = (TARGET_DATE - date.today()).days
st.markdown(f"""
<div style="text-align:center; margin-bottom:20px;">
    <span style="font-size:3rem; font-family:'Playfair Display'; color:#d4af37;">{days_left}</span>
    <span style="color:#888;">GÜN KALDI</span>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🛍️ LİSTE & BORSA", "📊 ANALİZ", "📋 PLANLAYICI"])

with tabs[0]:
    # EKLEME
    with st.expander("➕ YENİ ÜRÜN EKLE", expanded=False):
        with st.form("add_item"):
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
            url = c1.text_input("Link")
            cat = c2.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            pri = c3.selectbox("Öncelik", ["Yüksek", "Orta", "Düşük"])
            manual_price = c4.number_input("Manuel Fiyat", min_value=0.0)
            note = st.text_area("Not")
            
            if st.form_submit_button("KAYDET"):
                with st.spinner("Ekleniyor..."):
                    title, img, s_price = scrape_product_info(url)
                    final_price = s_price if s_price > 0 else manual_price
                    
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "Alisveris",
                        "kategori": cat, "baslik": title, 
                        "fiyat": final_price, "ilk_fiyat": final_price,
                        "url": url, "img": img, "oncelik": pri, "notlar": note, "durum": "Alınacak"
                    }])
                    
                    df = pd.concat([df, new_row], ignore_index=True)
                    update_all_data(df)
                    st.success("Eklendi!")
                    time.sleep(1)
                    st.rerun()

    # LİSTELEME
    filter_cat = st.multiselect("Kategori", df['kategori'].unique(), default=df['kategori'].unique())
    view_df = df[(df['kategori'].isin(filter_cat)) & (df['tur'] == 'Alisveris')]
    
    if not view_df.empty:
        # En son eklenen en üstte olsun
        view_df = view_df.iloc[::-1]
        
        cols = st.columns(3)
        for i, (idx, row) in enumerate(view_df.iterrows()):
            with cols[i % 3]:
                # Hesaplamalar
                curr_p = float(row['fiyat'])
                first_p = float(row['ilk_fiyat'])
                diff = curr_p - first_p
                
                trend_html = ""
                if first_p > 0 and diff != 0:
                    if diff < 0: trend_html = f"<div class='trend-down'>▼ {abs(diff):,.0f} TL İNDİRİM</div>"
                    else: trend_html = f"<div class='trend-up'>▲ {diff:,.0f} TL ZAM</div>"
                else: trend_html = "<div class='trend-neutral'>Fiyat Değişmedi</div>"
                
                badge_cls = f"badge-{row['ekleyen']}" if row['ekleyen'] in ['Kerem', 'Büşra'] else "badge-Kerem"
                opacity = "0.4" if row['durum'] == "Alındı" else "1"
                
                st.markdown(f"""
                <div class="luxury-card" style="opacity:{opacity};">
                    <span class="badge {badge_cls}">{row['ekleyen']}</span>
                    <div style="height:200px; display:flex; align-items:center; justify-content:center; background:#fff; border-radius:8px; overflow:hidden;">
                        <img src="{row['img']}" style="height:100%; object-fit:contain;">
                    </div>
                    <div style="margin-top:15px;">
                        <small style="color:#d4af37;">{row['kategori'].upper()}</small>
                        <div style="font-family:'Playfair Display'; font-size:1.1rem; height:50px; overflow:hidden; margin:5px 0;">{row['baslik']}</div>
                        
                        <div style="background:rgba(0,0,0,0.3); padding:10px; border-radius:10px; margin-bottom:10px;">
                            <div style="font-size:1.4rem; font-weight:bold; color:#fff;">{curr_p:,.0f} TL</div>
                            {trend_html}
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                            <a href="{row['url']}" target="_blank" style="color:#d4af37; text-decoration:none; border:1px solid #d4af37; padding:5px 15px; border-radius:15px; font-size:0.8rem;">SİTEYE GİT</a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # BUTONLAR (KARTIN ALTINA)
                c_btn1, c_btn2 = st.columns(2)
                
                # Satın Al Butonu
                if row['durum'] != "Alındı":
                    if c_btn1.button("✅ ALDIK", key=f"buy_{row['id']}"):
                        # Ana dataframe'de bu ID'yi bul ve güncelle
                        # Indeksi bulmamız lazım çünkü view_df sadece filtrelenmiş hali
                        original_idx = df[df['id'] == row['id']].index[0]
                        df.at[original_idx, 'durum'] = "Alındı"
                        update_all_data(df)
                        st.rerun()
                else:
                    c_btn1.info("Alındı 🎉")

                # SİLME BUTONU
                if c_btn2.button("🗑️ SİL", key=f"del_{row['id']}"):
                    delete_data(row['id'])
                    st.toast("Ürün silindi!")
                    time.sleep(1)
                    st.rerun()

with tabs[1]:
    st.subheader("Harcama Özeti")
    c1, c2 = st.columns(2)
    total_spent = df[df['tur']=='Alisveris']['fiyat'].sum()
    c1.metric("Toplam Tutar", f"{total_spent:,.0f} TL")
    fig = px.pie(df[df['tur']=='Alisveris'], values='fiyat', names='kategori', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig)

with tabs[2]:
    st.write("Planlayıcı")
