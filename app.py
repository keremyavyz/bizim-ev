import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import plotly.express as px
import urllib.parse
import random

# --- 1. AYARLAR ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

# --- 2. CSS (GÖRÜNTÜ MOTORU) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@200;300;400;500;600&display=swap');
    
    /* GENEL */
    .stApp {
        background-color: #09090b;
        font-family: 'Montserrat', sans-serif;
        color: #e4e4e7;
    }
    
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #d4af37 !important; }

    /* KART KUTUSU */
    .grand-card {
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
    }
    .grand-card:hover {
        border-color: #d4af37;
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(212, 175, 55, 0.1);
    }

    /* RESİM ALANI */
    .img-container {
        position: relative;
        width: 100%;
        height: 350px; /* Resim boyutu sabit */
        background-color: #000;
        border-bottom: 1px solid #27272a;
    }
    
    .product-img {
        width: 100%;
        height: 100%;
        object-fit: cover; /* Resmi kutuya tam doldur */
        object-position: center;
        opacity: 0.9;
        transition: opacity 0.3s;
    }
    .grand-card:hover .product-img { opacity: 1; }

    /* ÜZERİNDEKİ ETİKETLER */
    .badge-owner {
        position: absolute; top: 10px; left: 10px;
        background: rgba(0,0,0,0.7); color: #fff;
        padding: 4px 10px; border-radius: 6px;
        font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
        backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.1);
    }

    .badge-qty {
        position: absolute; bottom: 15px; right: 15px;
        width: 42px; height: 42px;
        background: #d4af37; color: #000;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        border: 2px solid #fff;
        z-index: 2;
    }

    /* ALT BİLGİLER */
    .card-content { padding: 15px; }
    
    .card-meta {
        display: flex; justify-content: space-between;
        color: #a1a1aa; font-size: 0.8rem; margin-bottom: 8px;
        text-transform: uppercase; letter-spacing: 1px;
    }
    
    .card-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.2rem; line-height: 1.3;
        color: #fafafa; margin-bottom: 10px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    
    .card-price {
        font-size: 1.4rem; font-weight: 700; color: #d4af37;
        letter-spacing: -0.5px;
    }

    /* ALINDI PERDESİ */
    .overlay-sold {
        position: absolute; inset: 0;
        background: rgba(0,0,0,0.7);
        display: flex; align-items: center; justify-content: center;
        z-index: 5; pointer-events: none;
    }
    .sold-text {
        color: #4ade80; font-size: 1.8rem; font-weight: 800;
        border: 3px solid #4ade80; padding: 10px 30px;
        border-radius: 12px; transform: rotate(-10deg);
        background: rgba(0,0,0,0.8);
        box-shadow: 0 0 20px rgba(74, 222, 128, 0.3);
    }

    /* INPUTLAR */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #18181b !important; border: 1px solid #3f3f46 !important; color: white !important;
    }
    .stButton>button {
        width: 100%; border-radius: 8px; border: 1px solid #3f3f46;
        background: #27272a; color: #e4e4e7;
    }
    .stButton>button:hover { border-color: #d4af37; color: #d4af37; }

</style>
""", unsafe_allow_html=True)

# --- 3. FONKSİYONLAR ---
def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn.read(ttl=0)

def update_data(df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="Sayfa1", data=df)
    st.cache_data.clear()

def delete_item(item_id):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    df['id'] = df['id'].astype(str)
    df = df[df['id'] != str(item_id)]
    conn.update(worksheet="Sayfa1", data=df)
    st.cache_data.clear()

# --- SCRAPER (YEDEK RESİM GARANTİLİ) ---
@st.cache_data(ttl=600)
def get_info(url):
    # Her zaman güzel bir placeholder döndür, asla boş dönme
    fallback = "https://placehold.co/600x600/111/444?text=Resim+Yok"
    title = "Yeni Ürün"
    
    if not url or "http" not in url: return title, fallback, 0
    
    try:
        # Microlink API (En güçlü yöntem)
        safe_url = urllib.parse.quote(url)
        api = f"https://api.microlink.io?url={safe_url}&screenshot=false&meta=true"
        r = requests.get(api, timeout=5).json()
        
        if r.get("status") == "success":
            data = r.get("data", {})
            title = data.get("title", title)
            img = data.get("image", {}).get("url", fallback)
            return title, img, 0
    except:
        pass
    
    return title, fallback, 0

# --- 4. GİRİŞ VE KONTROLLER ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if not st.session_state.user_name:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center'>Yuva & Co.</h1>", unsafe_allow_html=True)
        if st.button("KEREM OLARAK GİR", use_container_width=True):
            st.session_state.user_name = "Kerem"
            st.rerun()
        if st.button("BÜŞRA OLARAK GİR", use_container_width=True):
            st.session_state.user_name = "Büşra"
            st.rerun()
    st.stop()

# Veri Hazırlığı
try:
    df = get_data()
    cols = ['id','tarih','ekleyen','kategori','baslik','fiyat','url','img','oncelik','durum','adet']
    for c in cols: 
        if c not in df.columns: df[c] = ""
    
    df['id'] = df['id'].astype(str)
    df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
    df['adet'] = pd.to_numeric(df['adet'], errors='coerce').fillna(1).astype(int)
except:
    df = pd.DataFrame(columns=cols)

# --- 5. ANA EKRAN ---
st.markdown(f"<div style='text-align:right; color:#666;'>Kullanıcı: {st.session_state.user_name}</div>", unsafe_allow_html=True)

# TABS
tabs = st.tabs(["🛍️ KOLEKSİYON", "📋 LİSTE DETAY", "📊 BÜTÇE"])

# --- TAB 1: VİTRİN ---
with tabs[0]:
    # EKLEME MODÜLÜ
    with st.expander("➕ ÜRÜN EKLE", expanded=True):
        with st.form("add"):
            c1, c2 = st.columns([2, 1])
            url = c1.text_input("Ürün Linki")
            img_link = c2.text_input("Resim Linki (Sağ Tıkla Kopyala)")
            
            c3, c4, c5 = st.columns([2, 1, 1])
            cat = c3.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            price = c4.number_input("Birim Fiyat", min_value=0.0)
            qty = c5.number_input("Adet", min_value=1, value=1)
            
            if st.form_submit_button("KAYDET", use_container_width=True):
                title, auto_img, _ = get_info(url)
                final_img = img_link if img_link else auto_img
                
                new_row = pd.DataFrame([{
                    "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                    "ekleyen": st.session_state.user_name, "kategori": cat, 
                    "baslik": title, "fiyat": price * qty, "url": url, "img": final_img, 
                    "oncelik": "Yüksek", "durum": "Alınacak", "adet": qty
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                update_data(df)
                st.rerun()

    # LİSTELEME (2 KOLONLU)
    if not df.empty:
        df_rev = df.iloc[::-1]
        cols = st.columns(2)
        
        for i, (idx, row) in enumerate(df_rev.iterrows()):
            with cols[i % 2]:
                # Değişkenler
                is_bought = row['durum'] == "Alındı"
                price_fmt = f"{float(row['fiyat']):,.0f}"
                count = int(row['adet']) if row['adet'] else 1
                
                # HTML OLUŞTURMA (DİKKAT: f-string içine tırnaklara dikkat edildi)
                html_card = f"""
                <div class="grand-card">
                    {'<div class="overlay-sold"><div class="sold-text">ALINDI</div></div>' if is_bought else ''}
                    
                    <div class="img-container">
                        <img src="{row['img']}" class="product-img" onerror="this.src='https://placehold.co/600x600/111/444?text=Gorsel+Yok'">
                        <div class="badge-owner">{row['ekleyen']}</div>
                        {'<div class="badge-qty">x'+str(count)+'</div>' if count > 1 else ''}
                    </div>
                    
                    <div class="card-content">
                        <div class="card-meta">
                            <span>{row['kategori']}</span>
                            <span>{row['tarih']}</span>
                        </div>
                        <div class="card-title">{row['baslik']}</div>
                        <div class="card-price">{price_fmt} TL</div>
                    </div>
                </div>
                """
                # HTML Çizimi
                st.markdown(html_card, unsafe_allow_html=True)
                
                # Aksiyon Butonları
                b1, b2, b3 = st.columns([2, 2, 1])
                
                key_base = row['id']
                
                with b1:
                    if not is_bought:
                        if st.button("✅ ALDIK", key=f"buy_{key_base}", use_container_width=True):
                            df.at[idx, 'durum'] = "Alındı"
                            update_data(df); st.rerun()
                    else:
                        if st.button("↩️ İPTAL", key=f"ret_{key_base}", use_container_width=True):
                            df.at[idx, 'durum'] = "Alınacak"
                            update_data(df); st.rerun()
                
                with b2:
                    if row['url'] and "http" in str(row['url']):
                        st.link_button("🔗 GİT", row['url'], use_container_width=True)
                    else:
                        st.button("🚫 LİNK YOK", disabled=True, key=f"nolink_{key_base}", use_container_width=True)
                
                with b3:
                    if st.button("🗑️", key=f"del_{key_base}", use_container_width=True):
                        delete_item(key_base); st.rerun()
                
                # DÜZENLEME MODÜLÜ (RESMİ DÜZELTMEK İÇİN)
                with st.expander("✏️ Düzenle"):
                    with st.form(f"edit_{key_base}"):
                        new_img = st.text_input("Yeni Resim Linki", value=row['img'])
                        new_price = st.number_input("Yeni Fiyat", value=float(row['fiyat']))
                        if st.form_submit_button("GÜNCELLE"):
                            df.at[idx, 'img'] = new_img
                            df.at[idx, 'fiyat'] = new_price
                            update_data(df); st.rerun()

# --- TAB 2 & 3 (BASİT TUTTUM) ---
with tabs[1]:
    st.dataframe(df, use_container_width=True)

with tabs[2]:
    total = df['fiyat'].sum()
    st.metric("TOPLAM BÜTÇE", f"{total:,.0f} TL")
