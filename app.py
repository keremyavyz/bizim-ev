import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import time
import plotly.express as px
import re
import random

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

# --- 2. TEMA VE CSS YÖNETİMİ ---
if "theme" not in st.session_state:
    st.session_state.theme = "Dark Luxury"

# CSS: ORTAK AYARLAR & FONTLAR
common_css = """
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@200;300;400;500;600&display=swap');
    
    body { font-family: 'Montserrat', sans-serif; }
    h1, h2, h3, h4 { font-family: 'Playfair Display', serif !important; }
    
    /* Kart Yapısı */
    .grand-card {
        border-radius: 16px; 
        overflow: hidden; 
        margin-bottom: 30px; 
        transition: transform 0.3s ease;
        position: relative;
    }
    .grand-card:hover { transform: translateY(-5px); }
    
    .img-area {
        width: 100%; height: 350px; 
        background-color: white;
        display: flex; align-items: center; justify-content: center;
        position: relative;
    }
    .img-area img { max-width: 100%; max-height: 100%; object-fit: contain; }
    .content-area { padding: 20px; }
    
    .badge-corner {
        position: absolute; top: 15px; left: 15px;
        padding: 6px 12px; border-radius: 8px; 
        font-size: 0.75rem; font-weight: bold; text-transform: uppercase;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    /* Ekstra Gider Kartı */
    .expense-row {
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
        border-left: 5px solid #d4af37;
    }
    
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
"""

# CSS: DARK MODE
css_dark = f"""
    <style>
        {common_css}
        .stApp {{
            background-color: #050505;
            background-image: radial-gradient(circle at 50% 0%, #1a1a1a 0%, #050505 80%);
            color: #e0e0e0;
        }}
        .grand-card {{ background: #111; border: 1px solid #333; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        .grand-card:hover {{ border-color: #d4af37; box-shadow: 0 15px 40px rgba(212, 175, 55, 0.15); }}
        h1, h2, h3, h4, .big-font {{ color: #d4af37 !important; text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.2); }}
        .expense-row {{ background: rgba(255,255,255,0.05); }}
        
        .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {{
            background-color: #1a1a1a !important; color: #d4af37 !important; border: 1px solid #444 !important;
        }}
        .stButton>button {{ background-color: #222; color: #ccc; border: 1px solid #444; }}
        .stButton>button:hover {{ border-color: #d4af37; color: #d4af37; }}
    </style>
"""

# CSS: LIGHT MODE
css_light = f"""
    <style>
        {common_css}
        .stApp {{ background-color: #f8f9fa; color: #2c3e50; }}
        .grand-card {{ background: #fff; border: 1px solid #e0e0e0; box-shadow: 0 5px 20px rgba(0,0,0,0.05); }}
        .grand-card:hover {{ border-color: #2c3e50; box-shadow: 0 15px 30px rgba(0,0,0,0.1); }}
        h1, h2, h3, h4, .big-font {{ color: #2c3e50 !important; }}
        .expense-row {{ background: #fff; border: 1px solid #eee; border-left: 5px solid #2c3e50; }}
        
        .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {{
            background-color: #fff !important; color: #333 !important; border: 1px solid #ccc !important;
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

def delete_data(item_id):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    df['id'] = df['id'].astype(str)
    updated_df = df[df['id'] != str(item_id)]
    conn.update(worksheet="Sayfa1", data=updated_df)

@st.cache_data(ttl=600)
def scrape_product_info(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else soup.title.string
        og_image = soup.find("meta", property="og:image")
        img = og_image["content"] if og_image else "https://via.placeholder.com/400x300/111111/444444?text=Gorsel+Yok"
        price_meta = soup.find("meta", property="product:price:amount")
        price = float(price_meta["content"]) if price_meta else 0
        return title.strip(), img, price
    except:
        return "Manuel Giriş", "https://via.placeholder.com/400x300/111111/444444?text=Hata", 0

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
    cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum']
    for col in cols:
        if col not in df.columns: df[col] = ""
    if 'id' in df.columns: df['id'] = df['id'].astype(str)
    df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
    df['ilk_fiyat'] = pd.to_numeric(df['ilk_fiyat'], errors='coerce').fillna(0)
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
    if st.button("🔄 Fiyatları Güncelle"):
        with st.spinner("Taranıyor..."): time.sleep(1)
        st.success("Veriler Güncel")

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

tabs = st.tabs(["🛍️ KOLEKSİYON", "📋 PLANLAYICI", "📊 ANALİZ", "🎉 KEYİF & ROTA"])

# --- TAB 1: KOLEKSİYON ---
with tabs[0]:
    with st.expander("➕ YENİ EŞYA EKLE"):
        with st.form("add_item"):
            c1, c2 = st.columns([3, 1])
            url = c1.text_input("Link Yapıştır")
            cat = c2.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            c3, c4, c5 = st.columns([1, 1, 2])
            pri = c3.selectbox("Öncelik", ["Yüksek", "Orta", "Düşük"])
            manual_price = c4.number_input("Fiyat", min_value=0.0)
            note = c5.text_input("Not")
            
            if st.form_submit_button("KAYDET", use_container_width=True):
                with st.spinner("Ekleniyor..."):
                    title, img, s_price = scrape_product_info(url)
                    final_price = s_price if s_price > 0 else manual_price
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "Alisveris",
                        "kategori": cat, "baslik": title if title else "Ürün", 
                        "fiyat": final_price, "ilk_fiyat": final_price,
                        "url": url, "img": img, "oncelik": pri, "notlar": note, "durum": "Alınacak"
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    update_all_data(df); st.rerun()

    filter_cat = st.multiselect("Kategoriler:", df['kategori'].unique(), default=df['kategori'].unique())
    view_df = df[(df['kategori'].isin(filter_cat)) & (df['tur'] == 'Alisveris')]
    
    if not view_df.empty:
        view_df = view_df.iloc[::-1]
        cols = st.columns(2) 
        for i, (idx, row) in enumerate(view_df.iterrows()):
            with cols[i % 2]:
                is_done = row['durum'] == "Alındı"
                opacity = "0.5" if is_done else "1"
                status_badge = "✅ ALINDI" if is_done else ""
                
                curr = float(row['fiyat'])
                first = float(row['ilk_fiyat'])
                trend_html = ""
                if first > 0 and (curr < first):
                    trend_html = f"<span style='color:#2ecc71; font-weight:bold; margin-left:10px;'>🔻 İNDİRİMDE!</span>"
                
                st.markdown(f"""
                <div class="grand-card" style="opacity:{opacity};">
                    <div class="img-area">
                        <img src="{row['img']}">
                        <div class="badge-corner" style="background:#000; color:#fff;">{row['ekleyen']}</div>
                        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:#2ecc71; font-size:2rem; font-weight:bold; text-shadow:0 0 10px black;">{status_badge}</div>
                    </div>
                    <div class="content-area">
                        <div style="display:flex; justify-content:space-between; color:#888; font-size:0.8rem; margin-bottom:5px;">
                            <span>{row['kategori'].upper()}</span>
                            <span>{row['oncelik']} ÖNCELİK</span>
                        </div>
                        <h3 style="margin:5px 0; font-size:1.3rem; line-height:1.4;">{row['baslik']}</h3>
                        <p style="font-style:italic; color:#aaa; font-size:0.9rem;">{row['notlar']}</p>
                        <div style="margin-top:15px; font-size:1.4rem; font-weight:bold;">
                            {curr:,.0f} TL {trend_html}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c_act1, c_act2, c_act3 = st.columns([2, 2, 1])
                with c_act1:
                    if not is_done:
                        if st.button("✅ Satın Aldık", key=f"buy_{row['id']}", use_container_width=True):
                            df.at[df[df['id'] == row['id']].index[0], 'durum'] = "Alındı"
                            update_all_data(df); st.rerun()
                    else:
                        if st.button("↩️ Geri Al", key=f"ret_{row['id']}", use_container_width=True):
                            df.at[df[df['id'] == row['id']].index[0], 'durum'] = "Alınacak"
                            update_all_data(df); st.rerun()
                with c_act2: st.link_button("🔗 Siteye Git", row['url'], use_container_width=True)
                with c_act3:
                    if st.button("🗑️", key=f"del_{row['id']}", use_container_width=True):
                        delete_data(row['id']); st.rerun()
                st.write("")

# --- TAB 2: PLANLAYICI & GİDERLER ---
with tabs[1]:
    col_p1, col_p2 = st.columns([1, 1])
    
    # 1. EKSTRA GİDERLER (YENİ)
    with col_p1:
        st.subheader("💸 Ekstra Giderler (Hizmet & Diğer)")
        with st.form("add_expense", clear_on_submit=True):
            ec1, ec2, ec3 = st.columns([2, 1, 1])
            exp_name = ec1.text_input("Gider Adı", placeholder="Kuaför, Çekim vb.")
            exp_cost = ec2.number_input("Tutar (TL)", min_value=0)
            exp_cat = ec3.selectbox("Kategori", ["Düğün", "Balayı", "Kına", "Diğer"])
            if st.form_submit_button("GİDER EKLE", use_container_width=True):
                if exp_name:
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "Ekstra",
                        "baslik": exp_name, "fiyat": exp_cost, "kategori": exp_cat,
                        "ilk_fiyat": exp_cost, "url":"", "img":"", "oncelik":"", "notlar":"", "durum":""
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    update_all_data(df); st.rerun()
        
        # Ekstra Gider Listesi
        expenses = df[df['tur'] == 'Ekstra']
        if not expenses.empty:
            for i, (idx, row) in enumerate(expenses.iterrows()):
                st.markdown(f"""
                <div class="expense-row">
                    <div>
                        <div style="font-weight:bold;">{row['baslik']}</div>
                        <div style="font-size:0.8rem; color:#888;">{row['kategori']} • {row['ekleyen']}</div>
                    </div>
                    <div style="font-size:1.1rem; font-weight:bold;">{row['fiyat']:,.0f} TL</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Sil 🗑️", key=f"del_exp_{row['id']}"):
                    delete_data(row['id']); st.rerun()
        else:
            st.info("Henüz ekstra gider eklenmedi.")

    # 2. TO-DO & DAVETLİ
    with col_p2:
        st.subheader("📝 Yapılacaklar (To-Do)")
        with st.form("new_todo", clear_on_submit=True):
            c_td1, c_td2 = st.columns([3, 1])
            task = c_td1.text_input("Görev Ekle", placeholder="Gelin arabası süslemesi...")
            if c_td2.form_submit_button("EKLE"):
                if task:
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "ToDo",
                        "baslik": task, "durum": "Yapılacak",
                        "kategori":"", "fiyat":0, "ilk_fiyat":0, "url":"", "img":"", "oncelik":"", "notlar":""
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
                    <div>
                        <span style="font-size:0.7rem; color:#888;">{row['ekleyen']}</span>
                    </div>
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
        
        st.divider()
        st.subheader("👥 Davetli Taslağı")
        guests = df[df['tur'] == 'Davetli']
        with st.form("add_guest", clear_on_submit=True):
            g_name = st.text_input("Davetli Adı")
            if st.form_submit_button("Ekle"):
                if g_name:
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "Davetli", "baslik": g_name, "durum": "?",
                        "kategori":"", "fiyat":0, "ilk_fiyat":0, "url":"", "img":"", "oncelik":"", "notlar":""
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    update_all_data(df); st.rerun()
        if not guests.empty:
            st.dataframe(guests[['baslik']], use_container_width=True)

# --- TAB 3: ANALİZ ---
with tabs[2]:
    c1, c2, c3 = st.columns(3)
    
    # Hesaplamalar
    items_cost = df[df['tur'] == 'Alisveris']['fiyat'].sum()
    extra_cost = df[df['tur'] == 'Ekstra']['fiyat'].sum()
    total_cost = items_cost + extra_cost
    
    realized_items = df[(df['tur'] == 'Alisveris') & (df['durum'] == 'Alındı')]['fiyat'].sum()
    
    c1.metric("TOPLAM BÜTÇE (Eşya + Ekstra)", f"{total_cost:,.0f} TL")
    c2.metric("Sadece Eşyalar", f"{items_cost:,.0f} TL")
    c3.metric("Ekstra Giderler", f"{extra_cost:,.0f} TL")
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Kategori Bazlı (Eşyalar)")
        if not df[df['tur']=='Alisveris'].empty:
            fig = px.pie(df[df['tur']=='Alisveris'], values='fiyat', names='kategori', 
                         color_discrete_sequence=px.colors.sequential.RdBu, hole=0.5)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="gray")
            st.plotly_chart(fig, use_container_width=True)
            
    with col_chart2:
        st.subheader("Harcama Türü Dağılımı")
        summary_df = pd.DataFrame({
            "Tip": ["Eşyalar", "Ekstra Giderler"],
            "Tutar": [items_cost, extra_cost]
        })
        if total_cost > 0:
            fig2 = px.pie(summary_df, values='Tutar', names='Tip', 
                          color_discrete_sequence=["#d4af37", "#2c3e50"], hole=0.5)
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="gray")
            st.plotly_chart(fig2, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Excel/CSV Olarak İndir", csv, "Yuva_Listesi.csv", "text/csv", type="primary")

# --- TAB 4: KEYİF & ROTA ---
with tabs[3]:
    c_fun1, c_fun2 = st.columns(2)
    with c_fun1:
        st.subheader("🎵 Müzik Önerileri")
        st.text_input("Giriş Müziği", "https://...")
        st.text_input("İlk Dans", "https://...")
        st.video("https://www.youtube.com/watch?v=kYgGwWYOd9Y")
    with c_fun2:
        st.subheader("✈️ Balayı & Rota")
        st.map(pd.DataFrame({'lat': [41.0082], 'lon': [28.9784]}), zoom=4)
        st.markdown("""
        <div style="background: linear-gradient(135deg, #6dd5ed, #2193b0); padding:20px; border-radius:15px; color:white; text-align:center;">
            <h3>Maldivler</h3>
            <div style="font-size:3rem; font-weight:bold;">29°C</div>
            <div>☀️ Güneşli</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📊 Anket: Hangisi?")
    col_vote1, col_vote2 = st.columns(2)
    with col_vote1:
        st.image("https://via.placeholder.com/200?text=Model+A", use_container_width=True)
        if st.button("Model A Olsun"): st.balloons()
    with col_vote2:
        st.image("https://via.placeholder.com/200?text=Model+B", use_container_width=True)
        if st.button("Model B Olsun"): st.balloons()
