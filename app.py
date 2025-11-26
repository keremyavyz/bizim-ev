import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import time
import plotly.express as px
import re

# --- 1. AYARLAR & ELITE GOLD TASARIM ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@200;300;400;500;600&display=swap');

    /* ARKA PLAN */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(180deg, #111 0%, #000 100%);
        font-family: 'Montserrat', sans-serif;
        color: #f0f0f0;
    }

    /* BAŞLIKLAR (Altın Sarısı) */
    h1, h2, h3, h4, .big-font {
        font-family: 'Playfair Display', serif !important;
        color: #d4af37 !important;
        text-shadow: 0px 2px 10px rgba(212, 175, 55, 0.2);
    }

    /* LÜKS KART TASARIMI (Revize Edildi) */
    .luxury-card {
        background-color: #1a1a1a; /* Daha belirgin gri/siyah */
        border: 1px solid #333;
        border-radius: 12px;
        padding: 0; /* İç boşluğu kaldırdık, görsel tam otursun */
        margin-bottom: 15px;
        overflow: hidden;
        transition: transform 0.3s ease, border-color 0.3s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    
    .luxury-card:hover {
        transform: translateY(-5px);
        border-color: #d4af37; /* Hoverda altın çerçeve */
        box-shadow: 0 10px 30px rgba(212, 175, 55, 0.15);
    }

    /* KART İÇİ DETAYLAR */
    .card-content {
        padding: 15px;
    }

    .price-badge {
        background: linear-gradient(45deg, #d4af37, #f1c40f);
        color: #000;
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 5px;
    }

    /* BUTON STİLLERİ (Streamlit Butonlarını Özelleştirme) */
    .stButton>button {
        border-radius: 6px;
        border: 1px solid #444;
        background-color: #222;
        color: #ccc;
        font-size: 0.8rem;
        padding: 5px 10px;
        transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        border-color: #d4af37;
        color: #d4af37;
        background-color: #111;
    }

    /* INPUT ALANLARI */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #111 !important;
        color: #fff !important; 
        border: 1px solid #333 !important;
        border-radius: 8px;
    }

    /* SCROLLBAR */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- 2. FONKSİYONLAR ---

def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn.read(ttl=0)

def update_all_data(df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="Sayfa1", data=df)

def delete_data(item_id):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    df['id'] = df['id'].astype(str)
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
        img = og_image["content"] if og_image else "https://via.placeholder.com/400x300/111111/444444?text=Resim+Yok"
        
        price = 0
        price_meta = soup.find("meta", property="product:price:amount")
        if price_meta: price = float(price_meta["content"])
        
        return title.strip(), img, price
    except:
        return "Manuel Giriş", "https://via.placeholder.com/400x300/111111/444444?text=Hata", 0

# --- 3. GİRİŞ ---
if "user_name" not in st.session_state: st.session_state.user_name = None
if not st.session_state.user_name:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center;'>Yuva & Co.</h1>", unsafe_allow_html=True)
        pwd = st.text_input("Giriş Şifresi", type="password")
        if st.button("GİRİŞ YAP", use_container_width=True):
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
    cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum']
    for col in cols:
        if col not in df.columns: df[col] = ""
    if 'id' in df.columns: df['id'] = df['id'].astype(str)
    df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
    df['ilk_fiyat'] = pd.to_numeric(df['ilk_fiyat'], errors='coerce').fillna(0)
except: 
    df = pd.DataFrame(columns=cols)

# --- 5. ANA EKRAN ---
# Geri Sayım
TARGET_DATE = date(2026, 4, 25)
days_left = (TARGET_DATE - date.today()).days

c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.markdown(f"<h2>Hoşgeldin, {st.session_state.user_name}</h2>", unsafe_allow_html=True)
with c_head2:
    st.markdown(f"""
    <div style="text-align:right; border:1px solid #333; padding:10px; border-radius:10px; background:#111;">
        <span style="color:#888; font-size:0.8rem;">DÜĞÜNE KALAN</span><br>
        <span style="color:#d4af37; font-size:1.5rem; font-weight:bold;">{days_left} GÜN</span>
    </div>
    """, unsafe_allow_html=True)

st.write("") # Boşluk

tabs = st.tabs(["🛍️ ALIŞVERİŞ LİSTESİ", "📊 BÜTÇE ANALİZİ", "📋 NOTLAR & PLAN"])

# TAB 1: LİSTE
with tabs[0]:
    # EKLEME FORMU
    with st.expander("➕ YENİ BİR ŞEY EKLE", expanded=False):
        with st.form("add_item"):
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
            url = c1.text_input("Link (Varsa)")
            cat = c2.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            pri = c3.selectbox("Öncelik", ["Yüksek", "Orta", "Düşük"])
            manual_price = c4.number_input("Fiyat", min_value=0.0)
            note = st.text_area("Not")
            
            if st.form_submit_button("LİSTEYE KAYDET"):
                with st.spinner("İşleniyor..."):
                    title, img, s_price = scrape_product_info(url)
                    final_price = s_price if s_price > 0 else manual_price
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "Alisveris",
                        "kategori": cat, "baslik": title if title else "İsimsiz Ürün", 
                        "fiyat": final_price, "ilk_fiyat": final_price,
                        "url": url, "img": img, "oncelik": pri, "notlar": note, "durum": "Alınacak"
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    update_all_data(df)
                    st.success("Eklendi!"); time.sleep(0.5); st.rerun()

    # LİSTELEME
    filter_cat = st.multiselect("Filtrele:", df['kategori'].unique(), default=df['kategori'].unique())
    view_df = df[(df['kategori'].isin(filter_cat)) & (df['tur'] == 'Alisveris')]

    if not view_df.empty:
        view_df = view_df.iloc[::-1] # En yeni en üstte
        cols = st.columns(3)
        for i, (idx, row) in enumerate(view_df.iterrows()):
            with cols[i % 3]:
                # Fiyat Değişim Hesabı
                curr_p = float(row['fiyat'])
                first_p = float(row['ilk_fiyat'])
                diff = curr_p - first_p
                trend_arrow = "➖"
                trend_color = "#888"
                if first_p > 0 and diff < 0: 
                    trend_arrow = "🔻 İndirim"; trend_color = "#2ecc71"
                elif first_p > 0 and diff > 0: 
                    trend_arrow = "🔺 Zam"; trend_color = "#e74c3c"

                # Kartın Opaklığı (Alındıysa soluk)
                opacity = "0.5" if row['durum'] == "Alındı" else "1"
                border_style = "1px solid #2ecc71" if row['durum'] == "Alındı" else "1px solid #333"
                status_badge = "✅ ALINDI" if row['durum'] == "Alındı" else ""

                # HTML KART YAPISI
                st.markdown(f"""
                <div class="luxury-card" style="opacity:{opacity}; border:{border_style};">
                    <div style="position:relative; height:200px; background:#fff;">
                        <img src="{row['img']}" style="width:100%; height:100%; object-fit:contain;">
                        <div style="position:absolute; top:10px; right:10px; background:#000; color:#fff; padding:3px 8px; border-radius:10px; font-size:0.7rem;">{row['ekleyen']}</div>
                        <div style="position:absolute; bottom:10px; left:10px; background:{trend_color}; color:#fff; padding:2px 6px; border-radius:4px; font-size:0.7rem;">{trend_arrow}</div>
                         <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:#2ecc71; font-weight:bold; font-size:1.5rem; text-shadow:1px 1px 5px black;">{status_badge}</div>
                    </div>
                    <div class="card-content">
                        <div style="color:#d4af37; font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">{row['kategori'].upper()}</div>
                        <div style="font-family:'Playfair Display'; font-size:1.1rem; height:50px; overflow:hidden; line-height:1.3; margin-bottom:10px;">{row['baslik']}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span class="price-badge">{curr_p:,.0f} TL</span>
                            <a href="{row['url']}" target="_blank" style="color:#aaa; text-decoration:none; font-size:0.8rem; border-bottom:1px solid #555;">Linke Git ↗</a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # BUTONLAR (Kibarlık İçin Yan Yana)
                btn_col1, btn_col2 = st.columns([1, 1])
                with btn_col1:
                    if row['durum'] != "Alındı":
                        if st.button("✅ Aldık", key=f"buy_{row['id']}"):
                            original_idx = df[df['id'] == row['id']].index[0]
                            df.at[original_idx, 'durum'] = "Alındı"
                            update_all_data(df); st.rerun()
                    else:
                        if st.button("↩️ Geri Al", key=f"unbuy_{row['id']}"):
                            original_idx = df[df['id'] == row['id']].index[0]
                            df.at[original_idx, 'durum'] = "Alınacak"
                            update_all_data(df); st.rerun()
                with btn_col2:
                    if st.button("🗑️ Sil", key=f"del_{row['id']}"):
                        delete_data(row['id']); st.toast("Silindi"); time.sleep(0.5); st.rerun()

# TAB 2: ANALİZ
with tabs[1]:
    st.subheader("Finansal Durum")
    c1, c2 = st.columns(2)
    spent = df[df['tur']=='Alisveris']['fiyat'].sum()
    c1.metric("Toplam Planlanan", f"{spent:,.0f} TL")
    
    # Kalan Bütçe Hesaplama (Örnek)
    realized = df[(df['tur']=='Alisveris') & (df['durum']=='Alındı')]['fiyat'].sum()
    c2.metric("Harcanan (Alınanlar)", f"{realized:,.0f} TL")

    if not df.empty:
        fig = px.pie(df[df['tur']=='Alisveris'], values='fiyat', names='kategori', 
                     color_discrete_sequence=px.colors.sequential.RdBu, hole=0.6)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

# TAB 3: NOTLAR
with tabs[2]:
    st.write("Yapılacaklar listesi ve notlarınız...")
