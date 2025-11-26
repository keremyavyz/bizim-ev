import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import time
import plotly.express as px
import random

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

# --- 2. TEMA VE CSS ---
if "theme" not in st.session_state:
    st.session_state.theme = "Dark Luxury"

# CSS: KARTLAR VE DÜZEN
common_css = """
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@200;300;400;500;600&display=swap');
    
    body { font-family: 'Montserrat', sans-serif; }
    h1, h2, h3, h4 { font-family: 'Playfair Display', serif !important; }
    
    /* KART YAPISI */
    .grand-card {
        border-radius: 16px; 
        overflow: hidden; 
        margin-bottom: 25px; 
        transition: transform 0.3s ease;
        position: relative;
        height: 100%;
        display: flex; flex-direction: column;
    }
    .grand-card:hover { transform: translateY(-5px); }
    
    /* RESİM ALANI */
    .img-area {
        width: 100%; height: 350px; 
        background-color: #fff;
        display: flex; align-items: center; justify-content: center;
        position: relative;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        overflow: hidden;
    }
    /* RESMİ KUTUYA ZORLA OTURT */
    .img-area img { 
        width: 100%; height: 100%; 
        object-fit: cover;
        object-position: center;
        display: block;
    }
    
    /* İÇERİK ALANI */
    .content-area { 
        padding: 15px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between;
    }
    
    .card-title {
        font-family: 'Playfair Display', serif; font-size: 1.1rem; line-height: 1.3;
        height: 2.8em; overflow: hidden; display: -webkit-box;
        -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 5px;
    }
    
    /* ETİKETLER */
    .badge-corner {
        position: absolute; top: 15px; left: 15px;
        padding: 6px 12px; border-radius: 8px; 
        font-size: 0.75rem; font-weight: bold; text-transform: uppercase;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        z-index: 5;
    }
    
    .badge-qty {
        position: absolute; bottom: 15px; right: 15px;
        width: 45px; height: 45px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        z-index: 10;
        border: 2px solid white;
    }

    .expense-row {
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
        border-left: 5px solid #d4af37;
    }
    
    .overlay-bought {
        position: absolute; top:0; left:0; width:100%; height:100%;
        background: rgba(0,0,0,0.7); z-index: 20;
        display: flex; align-items: center; justify-content: center;
        pointer-events: none;
    }
"""

css_dark = f"""
    <style>
        {common_css}
        .stApp {{ background-color: #050505; background-image: radial-gradient(circle at 50% 0%, #1a1a1a 0%, #050505 80%); color: #e0e0e0; }}
        .grand-card {{ background: #1a1a1a; border: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
        .grand-card:hover {{ border-color: #d4af37; box-shadow: 0 10px 30px rgba(212, 175, 55, 0.15); }}
        h1, h2, h3, h4, .big-font {{ color: #d4af37 !important; text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.2); }}
        .expense-row {{ background: rgba(255,255,255,0.05); }}
        .badge-qty {{ background: #d4af37; color: #000; }}
        
        .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {{
            background-color: #1a1a1a !important; color: #d4af37 !important; border: 1px solid #444 !important;
        }}
        .stButton>button {{ background-color: #222; color: #ccc; border: 1px solid #444; }}
        .stButton>button:hover {{ border-color: #d4af37; color: #d4af37; }}
    </style>
"""

css_light = f"""
    <style>
        {common_css}
        .stApp {{ background-color: #f8f9fa; color: #2c3e50; }}
        .grand-card {{ background: #fff; border: 1px solid #e0e0e0; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .grand-card:hover {{ border-color: #2c3e50; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
        h1, h2, h3, h4, .big-font {{ color: #2c3e50 !important; }}
        .expense-row {{ background: #fff; border: 1px solid #eee; border-left: 5px solid #2c3e50; }}
        .badge-qty {{ background: #2c3e50; color: #fff; }}
        
        .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {{
            background-color: #ffffff !important; color: #2c3e50 !important; border: 1px solid #ccc !important;
        }}
        .stButton>button {{ background-color: #fff; color: #555; border: 1px solid #ccc; }}
        .stButton>button:hover {{ border-color: #2c3e50; color: #2c3e50; }}
    </style>
"""

if st.session_state.theme == "Dark Luxury":
    st.markdown(css_dark, unsafe_allow_html=True)
else:
    st.markdown(css_light, unsafe_allow_html=True)


# --- 3. HELPER FONKSİYONLAR ---
def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn.read(ttl=0)

def update_all_data(df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="Sayfa1", data=df)
    st.cache_data.clear()

def delete_data(item_id):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    df['id'] = df['id'].astype(str)
    updated_df = df[df['id'] != str(item_id)]
    conn.update(worksheet="Sayfa1", data=updated_df)
    st.cache_data.clear()

def detect_category_from_title(title):
    title = str(title).lower()
    keywords = {
        "Mutfak": ["tencere", "tava", "tabak", "çatal", "kaşık", "bıçak", "bardak", "kupa", "airfryer", "robot", "blender", "tost", "çay", "kahve", "fırın", "sürahi", "saklama", "kek", "kalıp", "rende", "cezve"],
        "Salon": ["koltuk", "kanepe", "berjer", "masa", "sandalye", "sehpa", "ünite", "kitaplık", "konsol", "vitrin", "halı", "perde", "kırlent", "vazo", "avize", "lambader"],
        "Yatak Odası": ["nevresim", "yatak", "baza", "başlık", "yastık", "yorgan", "battaniye", "pike", "çarşaf", "gardırop", "şifonyer", "komodin", "hurç"],
        "Elektronik": ["tv", "televizyon", "süpürge", "ütü", "kurutma", "saç", "düzleştirici", "hoparlör", "kulaklık", "şarj", "robot"],
        "Banyo": ["havlu", "bornoz", "paspas", "sabunluk", "diş", "fırça", "sepet", "kirli", "banyo", "klozet"],
        "Düğün": ["gelinlik", "damatlık", "ayakkabı", "kına", "davetiye", "nikah", "fotoğraf"]
    }
    for cat, keys in keywords.items():
        if any(k in title for k in keys): return cat
    return "Diğer"

# --- SAF VE BASİT SCRAPER (MANUEL ÖNCELİKLİ) ---
@st.cache_data(ttl=600)
def scrape_product_info(url):
    # Gerçek tarayıcı gibi davranan header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    # Varsayılan Boş Resim (placeholder sitesinden)
    fallback_img = "https://placehold.co/400x300/111/444?text=Resim+Yok"
    
    if not url or len(url) < 5:
        return "Ürün", fallback_img, 0

    try:
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Başlık
        title = "Ürün"
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.title:
            title = soup.title.string.strip()
            
        # 2. Resim (En basit yöntem)
        img = fallback_img
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            img = og_image["content"]
            
        # 3. Fiyat
        price = 0
        try:
            price_meta = soup.find("meta", property="product:price:amount")
            if price_meta and price_meta.get("content"):
                price = float(price_meta["content"])
        except:
            price = 0
            
        return title, img, price
        
    except:
        # Hata olursa manuel girişe bırak, programı durdurma
        return "Ürün", fallback_img, 0

# --- 4. GİRİŞ ---
if "user_name" not in st.session_state: st.session_state.user_name = None
if not st.session_state.user_name:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center;'>Yuva & Co.</h1>", unsafe_allow_html=True)
        pwd = st.text_input("Giriş Şifresi", type="password")
        if st.button("GİRİŞ", use_container_width=True):
            if pwd == "2024": st.session_state.auth = True
            else: st.error("Hatalı")
        if getattr(st.session_state, 'auth', False):
            col_k, col_b = st.columns(2)
            if col_k.button("KEREM"): st.session_state.user_name = "Kerem"; st.rerun()
            if col_b.button("BÜŞRA"): st.session_state.user_name = "Büşra"; st.rerun()
    st.stop()

# --- 5. DATA HAZIRLIK ---
try: 
    df = get_data()
    cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum', 'adet']
    for col in cols:
        if col not in df.columns: df[col] = ""
    if 'id' in df.columns: df['id'] = df['id'].astype(str)
    
    df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
    df['ilk_fiyat'] = pd.to_numeric(df['ilk_fiyat'], errors='coerce').fillna(0)
    df['adet'] = pd.to_numeric(df['adet'], errors='coerce').fillna(1).astype(int)
except: 
    df = pd.DataFrame(columns=cols)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_name}")
    st.divider()
    mode = st.radio("Tema", ["Dark Luxury", "Light Elegance"], 
                    index=0 if st.session_state.theme=="Dark Luxury" else 1)
    if mode != st.session_state.theme:
        st.session_state.theme = mode
        st.rerun()
    st.divider()
    if st.button("🔄 Sayfayı Yenile"):
        st.cache_data.clear()
        st.rerun()

# --- 7. ANA EKRAN ---
TARGET_DATE = date(2026, 4, 25)
days_left = (TARGET_DATE - date.today()).days

c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.markdown(f"<h1>Merhaba, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
with c_head2:
    color = "#d4af37" if st.session_state.theme == "Dark Luxury" else "#2c3e50"
    st.markdown(f"""
    <div style="text-align:right; border-left:4px solid {color}; padding-left:15px;">
        <span style="font-size:0.8rem; letter-spacing:2px;">BÜYÜK GÜNE</span><br>
        <span style="font-size:2.5rem; font-family:'Playfair Display'; font-weight:bold; color:{color};">{days_left}</span>
        <span style="font-size:1rem;">GÜN</span>
    </div>
    """, unsafe_allow_html=True)

st.write("") 

# TABS
tabs = st.tabs(["🛍️ KOLEKSİYON", "📋 PLANLAYICI", "📊 ANALİZ", "🤖 AI ASİSTAN"])

# --- TAB 1: KOLEKSİYON ---
with tabs[0]:
    with st.expander("➕ HIZLI EKLE (MANUEL RESİM DESTEKLİ)", expanded=True):
        st.info("💡 **İPUCU:** Eğer Zara/Trendyol gibi sitelerden ekliyorsan, resme SAĞ TIKLA -> **'Resim Adresini Kopyala'** de ve aşağıdaki 2. kutuya yapıştır. Kesin çözüm budur.")
        
        with st.form("add_item"):
            c1, c2 = st.columns([1, 1])
            url = c1.text_input("1. Ürün Linki (Site)")
            img_manual = c2.text_input("2. Resim Linki (Buraya Yapıştırırsan Kesin Görünür)")
            
            c3, c4, c5, c6 = st.columns([2, 1, 1, 2])
            cat_options = ["Otomatik Algıla", "Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"]
            cat = c3.selectbox("Kategori", cat_options)
            manual_price = c4.number_input("Birim Fiyat", min_value=0.0)
            qty = c5.number_input("Adet", min_value=1, value=1)
            pri = c6.selectbox("Öncelik", ["Yüksek", "Orta", "Düşük"])
            
            if st.form_submit_button("KAYDET", use_container_width=True):
                if url or img_manual:
                    with st.spinner("Kaydediliyor..."):
                        # Varsayılanlar
                        title, img, s_price = "Yeni Ürün", "", 0
                        
                        # 1. Otomatik Çekmeyi Dene (Varsa)
                        if url:
                            title, img, s_price = scrape_product_info(url)
                        
                        # 2. MANUEL RESİM VARSA ONU KULLAN (BASKIN)
                        if img_manual and len(img_manual) > 5:
                            img = img_manual
                        
                        # Fiyat
                        unit_p = s_price if s_price > 0 else manual_price
                        final_total_price = unit_p * qty
                        
                        # Kategori
                        final_cat = cat
                        if cat == "Otomatik Algıla": final_cat = detect_category_from_title(title)
                        
                        new_row = pd.DataFrame([{
                            "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                            "ekleyen": st.session_state.user_name, "tur": "Alisveris",
                            "kategori": final_cat, "baslik": title, 
                            "fiyat": final_total_price, "ilk_fiyat": final_total_price,
                            "url": url, "img": img, "oncelik": pri, "notlar": "", "durum": "Alınacak",
                            "adet": qty
                        }])
                        df = pd.concat([df, new_row], ignore_index=True)
                        update_all_data(df)
                        st.success(f"Eklendi! {qty} adet.")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("En azından bir link girin.")

    # LİSTELEME
    all_cats = [c for c in df['kategori'].unique() if c]
    filter_cat = st.multiselect("Filtrele:", all_cats, default=all_cats)
    view_df = df[(df['kategori'].isin(filter_cat)) & (df['tur'] == 'Alisveris')]
    
    if not view_df.empty:
        view_df = view_df.iloc[::-1]
        cols = st.columns(2) 
        for i, (idx, row) in enumerate(view_df.iterrows()):
            with cols[i % 2]:
                is_done = row['durum'] == "Alındı"
                card_id = row['id']
                
                overlay_html = ""
                if is_done:
                    overlay_html = '<div class="overlay-bought"><span style="color:#2ecc71; font-size:2rem; font-weight:bold; border:3px solid #2ecc71; padding:10px 20px; border-radius:10px; background:rgba(0,0,0,0.8);">✅ ALINDI</span></div>'
                
                curr = float(row['fiyat'])
                first = float(row['ilk_fiyat'])
                piece_count = int(row['adet']) if row['adet'] else 1
                
                qty_badge_html = ""
                if piece_count > 1:
                    qty_badge_html = f'<div class="badge-qty">x{piece_count}</div>'
                
                trend_html = ""
                if first > 0 and (curr < first):
                    trend_html = f"<span style='color:#2ecc71; font-weight:bold; margin-left:10px;'>🔻 İNDİRİMDE!</span>"
                
                # Resim URL'sini al, yoksa placeholder koy
                img_url = row['img']
                if not img_url or len(str(img_url)) < 5:
                    img_url = "https://placehold.co/400x300/1a1a1a/d4af37?text=Resim+Yok"

                st.markdown(f"""
                <div class="grand-card">
                    {overlay_html}
                    <div class="img-area">
                        <img src="{img_url}" onerror="this.onerror=null;this.src='https://placehold.co/400x300/1a1a1a/d4af37?text=Resim+Yuklenemedi';">
                        <div class="badge-corner" style="background:#000; color:#fff;">{row['ekleyen']}</div>
                        {qty_badge_html}
                    </div>
                    <div class="content-area">
                        <div style="display:flex; justify-content:space-between; color:#888; font-size:0.8rem; margin-bottom:5px;">
                            <span>{str(row['kategori']).upper()}</span>
                            <span>{row['oncelik']}</span>
                        </div>
                        <div class="card-title">{row['baslik']}</div>
                        <div style="margin-top:15px; font-size:1.4rem; font-weight:bold;">
                            {curr:,.0f} TL {trend_html}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🖼️ Düzenle"):
                     with st.form(f"edit_{card_id}"):
                         e_img = st.text_input("Resim Linki", value=row['img'])
                         e_prc = st.number_input("Fiyat", value=float(row['fiyat']))
                         if st.form_submit_button("GÜNCELLE"):
                             idx_orig = df[df['id'] == card_id].index[0]
                             df.at[idx_orig, 'img'] = e_img
                             df.at[idx_orig, 'fiyat'] = e_prc
                             update_all_data(df); st.rerun()

                c_act1, c_act2, c_act3 = st.columns([2, 2, 1])
                with c_act1:
                    if not is_done:
                        if st.button("✅ Aldık", key=f"buy_{card_id}", use_container_width=True):
                            df.at[df[df['id'] == card_id].index[0], 'durum'] = "Alındı"
                            update_all_data(df); st.rerun()
                    else:
                        if st.button("↩️ Geri Al", key=f"ret_{card_id}", use_container_width=True):
                            df.at[df[df['id'] == card_id].index[0], 'durum'] = "Alınacak"
                            update_all_data(df); st.rerun()
                with c_act2: st.link_button("🔗 Site", row['url'], use_container_width=True)
                with c_act3:
                    if st.button("🗑️", key=f"del_{card_id}", use_container_width=True):
                        delete_data(card_id); st.rerun()
                st.write("")

# --- TAB 2: PLANLAYICI ---
with tabs[1]:
    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        st.subheader("💸 Ekstra Giderler")
        with st.form("add_expense", clear_on_submit=True):
            ec1, ec2, ec3 = st.columns([2, 1, 1])
            exp_name = ec1.text_input("Gider Adı")
            exp_cost = ec2.number_input("Tutar (TL)", min_value=0)
            exp_cat = ec3.selectbox("Kategori", ["Düğün", "Balayı", "Diğer"])
            if st.form_submit_button("EKLE", use_container_width=True):
                if exp_name:
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "Ekstra",
                        "baslik": exp_name, "fiyat": exp_cost, "kategori": exp_cat,
                        "ilk_fiyat": exp_cost, "url":"", "img":"", "oncelik":"", "notlar":"", "durum":"", "adet": 1
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    update_all_data(df); st.rerun()
        expenses = df[df['tur'] == 'Ekstra']
        if not expenses.empty:
            for i, (idx, row) in enumerate(expenses.iterrows()):
                st.markdown(f"""
                <div class="expense-row">
                    <div><b>{row['baslik']}</b> <small>({row['kategori']})</small></div>
                    <div style="font-weight:bold;">{row['fiyat']:,.0f} TL</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Sil 🗑️", key=f"del_exp_{row['id']}"):
                    delete_data(row['id']); st.rerun()

    with col_p2:
        st.subheader("📝 Yapılacaklar")
        with st.form("new_todo", clear_on_submit=True):
            c_td1, c_td2 = st.columns([3, 1])
            task = c_td1.text_input("Görev")
            if c_td2.form_submit_button("EKLE"):
                if task:
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "ToDo",
                        "baslik": task, "durum": "Yapılacak",
                        "kategori":"", "fiyat":0, "ilk_fiyat":0, "url":"", "img":"", "oncelik":"", "notlar":"", "adet": 1
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    update_all_data(df); st.rerun()
        todos = df[df['tur'] == 'ToDo']
        if not todos.empty:
            for i, (idx, row) in enumerate(todos.iloc[::-1].iterrows()):
                checked = row['durum'] == "Yapıldı"
                st.markdown(f"""
                <div style="padding:10px; background:rgba(255,255,255,0.05); margin-bottom:5px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="{'text-decoration:line-through; opacity:0.5;' if checked else ''} font-size:1rem;">{row['baslik']}</span>
                    <span style="font-size:0.7rem;">{row['ekleyen']}</span>
                </div>
                """, unsafe_allow_html=True)
                cb1, cb2 = st.columns([1, 4])
                with cb1:
                    if st.button("✅", key=f"chk_{row['id']}"):
                        df.at[df[df['id'] == row['id']].index[0], 'durum'] = "Yapılacak" if checked else "Yapıldı"
                        update_all_data(df); st.rerun()
                with cb2:
                     if st.button("🗑️", key=f"del_td_{row['id']}"):
                        delete_data(row['id']); st.rerun()

# --- TAB 3: ANALİZ ---
with tabs[2]:
    c1, c2, c3 = st.columns(3)
    items_cost = df[df['tur'] == 'Alisveris']['fiyat'].sum()
    extra_cost = df[df['tur'] == 'Ekstra']['fiyat'].sum()
    total_cost = items_cost + extra_cost
    c1.metric("TOPLAM BÜTÇE", f"{total_cost:,.0f} TL")
    c2.metric("Eşyalar", f"{items_cost:,.0f} TL")
    c3.metric("Ekstra Giderler", f"{extra_cost:,.0f} TL")
    st.divider()
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Kategori Bazlı")
        if not df[df['tur']=='Alisveris'].empty:
            fig = px.pie(df[df['tur']=='Alisveris'], values='fiyat', names='kategori', color_discrete_sequence=px.colors.sequential.RdBu, hole=0.5)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="gray")
            st.plotly_chart(fig, use_container_width=True)
    with col_chart2:
        st.subheader("Harcama Türü")
        summary_df = pd.DataFrame({"Tip": ["Eşyalar", "Ekstra"], "Tutar": [items_cost, extra_cost]})
        if total_cost > 0:
            fig2 = px.pie(summary_df, values='Tutar', names='Tip', color_discrete_sequence=["#d4af37", "#2c3e50"], hole=0.5)
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="gray")
            st.plotly_chart(fig2, use_container_width=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 İndir", csv, "Yuva_Listesi.csv", "text/csv", type="primary")

# --- TAB 4: AI ASİSTAN ---
with tabs[3]:
    st.subheader("🤖 Yuva & Co. Akıllı Asistan")
    ai_col1, ai_col2 = st.columns(2)
    with ai_col1:
        if st.button("🔍 Evi Analiz Et", use_container_width=True):
            with st.spinner("Liste taranıyor..."):
                time.sleep(1.5)
                cats = df[df['tur']=='Alisveris']['kategori'].unique()
                msg = "Analiz Tamamlandı. "
                if "Mutfak" not in cats: msg += "**Mutfak** eşyaları eksik görünüyor. "
                if "Elektronik" not in cats: msg += "**Elektronik** kategorisine bakmalısınız."
                st.info(f"💡 **Sonuç:** {msg}")
    with ai_col2:
        if st.button("✨ Bana Fikir Ver", use_container_width=True):
            suggestions = ["Dyson Gen5detect", "Smeg Kettle", "Nespresso Kahve Makinesi", "Marshall Hoparlör"]
            st.success(f"💎 **Önerim:** {random.choice(suggestions)}")
