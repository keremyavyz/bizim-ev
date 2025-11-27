import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import time
from datetime import datetime, date
import plotly.express as px
import urllib.parse
from io import BytesIO

# --- 1. AYARLAR & YAPILANDIRMA ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

# Sabitler
TARGET_DATE = date(2026, 4, 25) # Düğün Tarihi
PASSWORD = "2024"

# --- 2. SESSION STATE (OTURUM) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "theme" not in st.session_state:
    st.session_state.theme = "Dark Luxury"

# --- 3. CSS VE ANİMASYON MOTORU ---
def load_css():
    # Tema Renkleri
    if st.session_state.theme == "Dark Luxury":
        bg_color = "#000000"
        text_color = "#f5f5f7"
        card_bg = "#1c1c1e"
        card_border = "#2c2c2e"
        accent = "#d4af37" # Gold
        input_bg = "#1c1c1e"
        menu_bg = "#2c2c2e"
        btn_bg = "#2c2c2e"
        btn_txt = "#fff"
        shadow = "rgba(0,0,0,0.5)"
        todo_bg = "#1c1c1e"
        todo_done_text = "#636366"
    else: # Light Elegance
        bg_color = "#f5f5f7"
        text_color = "#1d1d1f"
        card_bg = "#ffffff"
        card_border = "#d1d1d6"
        accent = "#d4af37" 
        input_bg = "#ffffff"
        menu_bg = "#ffffff"
        btn_bg = "#ffffff"
        btn_txt = "#1d1d1f"
        shadow = "rgba(0,0,0,0.05)"
        todo_bg = "#ffffff"
        todo_done_text = "#aeaeb2"

    common_css = f"""
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&family=Playfair+Display:wght@400;600;700&display=swap');
        
        /* --- ANİMASYONLAR --- */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Tüm Ana İçerik Animasyonlu Girsin */
        .stApp, .block-container {{
            animation: fadeIn 0.8s ease-out forwards;
        }}
        
        /* Kartlar sırayla gelsin (basit gecikme efekti gibi davranır) */
        .grand-card, .expense-card, div[data-testid="stVerticalBlockBorderWrapper"] {{
            animation: fadeIn 0.6s ease-out forwards;
        }}

        /* GENEL YAZI TİPİ */
        html, body, [class*="css"], .stMarkdown, div, span, p, label {{
            font-family: 'Montserrat', sans-serif !important;
            color: {text_color};
        }}
        
        h1, h2, h3, h4 {{ 
            font-family: 'Playfair Display', serif !important; 
            color: {accent} !important; 
        }}
        
        .stApp {{ background-color: {bg_color}; }}
        
        /* --- GİRİŞ EKRANI (LOGIN) ÖZEL --- */
        .login-title {{
            font-size: 3rem;
            text-align: center;
            margin-bottom: 10px;
            color: {accent};
        }}
        .login-subtitle {{
            text-align: center;
            font-size: 1rem;
            opacity: 0.7;
            margin-bottom: 40px;
        }}
        
        /* --- KART TASARIMLARI --- */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {todo_bg};
            border: 1px solid {card_border};
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px {shadow};
        }}
        
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            border-color: {accent};
            transform: translateY(-2px);
            box-shadow: 0 8px 15px {shadow};
        }}
        
        .stCheckbox label {{ font-size: 1.1rem !important; font-weight: 500 !important; padding-left: 10px; }}
        
        .task-done {{ text-decoration: line-through; color: {todo_done_text} !important; font-style: italic; transition: all 0.5s ease; }}
        .task-active {{ color: {text_color} !important; font-weight: 500; font-size: 1.05rem; }}
        
        .badge-done {{
            background-color: rgba(46, 204, 113, 0.15); color: #2ecc71; padding: 4px 10px;
            border-radius: 12px; font-size: 0.75rem; font-weight: bold; border: 1px solid rgba(46, 204, 113, 0.3); margin-left: 10px;
        }}

        .grand-card {{
            border-radius: 16px; overflow: hidden; margin-bottom: 20px; 
            position: relative; height: 100%; display: flex; flex-direction: column;
            transition: transform 0.3s ease;
            background: {card_bg} !important; border: 1px solid {card_border}; box-shadow: 0 4px 10px {shadow};
        }}
        
        .img-area {{ width: 100%; height: 220px; background: #fff; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid {card_border}; }}
        .img-area img {{ width: 100%; height: 100%; object-fit: contain; padding: 15px; }}
        .content-area {{ padding: 20px; color: {text_color}; }}
        
        .expense-card {{
            padding: 20px; border-radius: 18px; margin-bottom: 15px;
            border-left: 5px solid {accent}; background: {card_bg} !important; 
            border: 1px solid {card_border}; color: {text_color}; box-shadow: 0 2px 8px {shadow};
        }}
        
        .stTextInput input, .stNumberInput input, .stSelectbox, .stTextArea textarea {{
            background-color: {input_bg} !important; color: {text_color} !important;
            border-radius: 12px !important; border: 1px solid {card_border} !important;
        }}
        
        .stButton>button {{
            border-radius: 12px !important; background-color: {btn_bg} !important;
            color: {btn_txt} !important; border: 1px solid {card_border} !important; font-weight: 600;
        }}
        
        .sticky-footer {{
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            background: {card_bg}; border: 1px solid {card_border};
            padding: 10px 30px; border-radius: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            display: flex; gap: 20px; align-items: center; z-index: 9999;
        }}
        
        .hero-counter {{ text-align: center; padding: 50px 20px; }}
        .hero-days {{ font-size: 4.5rem; font-weight: 700; color: {accent}; font-family: 'Playfair Display', serif; line-height: 1; }}
        .hero-label {{ letter-spacing: 3px; text-transform: uppercase; font-size: 0.9rem; opacity: 0.7; margin-bottom: 10px; }}
        
        a.phone-link {{ color: #34c759 !important; text-decoration: none; font-weight: bold; }}
    """
    st.markdown(f"<style>{common_css}</style>", unsafe_allow_html=True)

# --- 4. VERİ YÖNETİMİ ---
def get_data():
    required_cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum', 'adet', 'odenen']
    conn = st.connection("gsheets", type=GSheetsConnection)
    for attempt in range(3):
        try:
            df = conn.read(ttl=0)
            if df is None or df.empty: return pd.DataFrame(columns=required_cols)
            for col in required_cols:
                if col not in df.columns: df[col] = ""
            df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
            df['odenen'] = pd.to_numeric(df['odenen'], errors='coerce').fillna(0)
            df['adet'] = pd.to_numeric(df['adet'], errors='coerce').fillna(1)
            return df.fillna("")
        except Exception as e: time.sleep(1 + attempt)
    return pd.DataFrame(columns=required_cols)

def save_data(df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    for attempt in range(3):
        try:
            conn.update(worksheet="Sayfa1", data=df)
            st.cache_data.clear()
            return
        except: time.sleep(1 + attempt)

def scrape_metadata(url):
    fallback = "https://cdn-icons-png.flaticon.com/512/3081/3081840.png"
    if not url or len(url) < 5: return "Yeni Ürün", fallback
    try:
        encoded = urllib.parse.quote(url)
        resp = requests.get(f"https://api.microlink.io?url={encoded}&meta=true", timeout=5)
        data = resp.json()
        if data['status'] == 'success':
            d = data['data']
            return d.get('title', 'Yeni Ürün'), d.get('image', {}).get('url', fallback)
    except: pass
    return "Manuel Giriş", fallback

def clean_phone(phone_val):
    s = str(phone_val).replace('.0', '').replace(',', '').replace('.', '')
    digits = ''.join(filter(str.isdigit, s))
    if len(digits) == 10: return "0" + digits
    return digits

# --- 5. UYGULAMA MANTIĞI ---

# 5.1 GİRİŞ EKRANI (LOGIN)
if not st.session_state.authenticated:
    load_css() # Sadece CSS yükle, sidebar yok
    
    # Dikey Ortalamak için boşluklar
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        # Animasyonlu Giriş Kutusu
        with st.container(border=True):
            st.markdown('<div class="login-title">Yuva & Co.</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-subtitle">Hayatınızın en güzel planı için giriş yapın.</div>', unsafe_allow_html=True)
            
            pwd_input = st.text_input("Şifre", type="password", placeholder="Giriş anahtarı...")
            
            if st.button("Giriş Yap", use_container_width=True):
                if pwd_input == PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Hatalı şifre.")
    st.stop() # Giriş yapılmadıysa aşağıyı okuma

# 5.2 ANA UYGULAMA (GİRİŞ YAPILDI)
load_css()
df = get_data()

# Sidebar
with st.sidebar:
    st.markdown("### 💍 Yuva & Co.")
    st.caption("Planlayıcı v3.0")
    st.divider()
    theme_choice = st.radio("Tema", ["Dark Luxury", "Light Elegance"], index=0 if st.session_state.theme == "Dark Luxury" else 1)
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()
    st.divider()
    if st.button("Çıkış Yap"):
        st.session_state.authenticated = False
        st.rerun()
    
    # Geri Al ve Yedek
    if "last_undo" not in st.session_state: st.session_state.last_undo = None
    st.divider()
    if st.button("♻️ Geri Al", disabled=st.session_state.last_undo is None):
        if st.session_state.last_undo is not None:
            df = pd.concat([df, st.session_state.last_undo], ignore_index=True)
            save_data(df); st.session_state.last_undo = None; st.rerun()
    if st.button("📥 Yedek İndir"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("Excel Al", output.getvalue(), f"Yuva_Yedek.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# HERO ALANI
days_left = (TARGET_DATE - date.today()).days
st.markdown(f"""<div class="hero-counter"><div class="hero-label">BÜYÜK GÜNE KALAN</div><div class="hero-days">{days_left} Gün</div><div class="hero-date">25 Nisan 2026</div></div>""", unsafe_allow_html=True)

c_hero1, c_hero2 = st.columns([3,1])
with c_hero1: search = st.text_input("🔍 Hızlı Ara", placeholder="Ne aramıştınız?")

if df.empty: filtered_df = df
else:
    mask = df.apply(lambda x: search.lower() in str(x).lower(), axis=1) if search else [True] * len(df)
    filtered_df = df[mask]

tabs = st.tabs(["🛍️ KOLEKSİYON", "💸 GİDERLER", "✅ YAPILACAKLAR", "👥 REHBER", "📊 DURUM"])

# TAB 1: KOLEKSİYON
with tabs[0]:
    with st.container():
        c_filt1, c_filt2 = st.columns(2)
        filter_status = c_filt1.selectbox("Filtre", ["Tümü", "Sadece Alınacaklar", "Sadece Alınanlar"])
        sort_option = c_filt2.selectbox("Sıralama", ["En Yeni", "Fiyat Artan", "Fiyat Azalan"])
    st.write("") 
    with st.popover("➕ ÜRÜN EKLE", use_container_width=True):
        with st.form("add_item", clear_on_submit=True):
            u_url = st.text_input("Link")
            u_cat = st.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            u_prc = st.number_input("Fiyat", min_value=0.0)
            u_qty = st.number_input("Adet", min_value=1, value=1)
            if st.form_submit_button("EKLE"):
                tit, img = scrape_metadata(u_url)
                new_row = {"id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"), "ekleyen": "Biz", "tur": "Alisveris", "kategori": u_cat, "baslik": tit, "fiyat": u_prc * u_qty, "ilk_fiyat": u_prc * u_qty, "url": u_url, "img": img, "durum": "Alınacak", "adet": u_qty, "odenen": 0, "notlar": ""}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()

    items = filtered_df[filtered_df['tur'] == 'Alisveris']
    if filter_status == "Sadece Alınacaklar": items = items[items['durum'] != 'Alındı']
    elif filter_status == "Sadece Alınanlar": items = items[items['durum'] == 'Alındı']
    if sort_option == "En Yeni": items = items.sort_values('id', ascending=False)
    elif sort_option == "Fiyat Azalan": items = items.sort_values('fiyat', ascending=False)
    elif sort_option == "Fiyat Artan": items = items.sort_values('fiyat', ascending=True)

    if items.empty: st.info("Liste boş.")
    else:
        cols = st.columns(3)
        for i, (idx, row) in enumerate(items.iterrows()):
            with cols[i % 3]:
                is_done = row['durum'] == "Alındı"
                overlay = '<div style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:2;pointer-events:none;"><span style="font-size:3rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));">✅</span></div>' if is_done else ""
                img_src = row['img'] if row['img'] else "https://cdn-icons-png.flaticon.com/512/3081/3081840.png"
                st.markdown(f'<div class="grand-card">{overlay}<div class="img-area"><img src="{img_src}"></div><div class="content-area"><div style="opacity:0.7; font-size:0.8rem; text-transform:uppercase;">{row["kategori"]}</div><h4 style="margin:5px 0; font-size:1.1rem;">{row["baslik"]}</h4><div style="font-size:1.3rem; color:#d4af37; font-weight:700; margin-top:auto;">{float(row["fiyat"]):,.0f} TL</div></div></div>', unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("ALDIK" if not is_done else "İPTAL", key=f"st_{row['id']}", use_container_width=True):
                    df.at[idx, 'durum'] = "Alındı" if not is_done else "Alınacak"; save_data(df); st.rerun()
                if b2.button("SİL", key=f"dl_{row['id']}", use_container_width=True):
                    st.session_state.last_undo = df.loc[[idx]]; df = df.drop(idx); save_data(df); st.rerun()

# TAB 2: GİDER
with tabs[1]:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📌 Gider Ekle")
        with st.form("add_expense", clear_on_submit=True):
            e_ad = st.text_input("Gider Adı")
            e_top = st.number_input("Toplam Tutar", min_value=0.0)
            e_kap = st.number_input("Ödenen (Kapora)", min_value=0.0)
            e_kat = st.selectbox("Kategori", ["Düğün", "Balayı", "Ev Tadilat", "Diğer"])
            if st.form_submit_button("KAYDET"):
                new_row = {"id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"), "tur": "Ekstra", "baslik": e_ad, "fiyat": e_top, "odenen": e_kap, "kategori": e_kat, "durum": "Bekliyor", "adet": 1, "url":"", "img":"", "notlar":""}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()
    with c2:
        st.subheader("💸 Durum")
        expenses = filtered_df[filtered_df['tur'] == 'Ekstra']
        for i, r in expenses.iterrows():
            kalan = float(r['fiyat']) - float(r['odenen'])
            pct = float(r['odenen']) / float(r['fiyat']) if float(r['fiyat']) > 0 else 0
            st.markdown(f'<div class="expense-card"><div style="display:flex; justify-content:space-between; font-weight:700; font-size:1.1rem;"><span>{r["baslik"]}</span><span>{float(r["fiyat"]):,.0f} TL</span></div><div style="margin:10px 0; height:8px; background:rgba(128,128,128,0.2); border-radius:4px;"><div style="width:{min(pct*100, 100)}%; height:100%; background:#d4af37; border-radius:4px;"></div></div><div style="display:flex; justify-content:space-between; font-size:0.9rem; margin-top:5px;"><span style="color:#4ade80;">Ödenen: {float(r["odenen"]):,.0f} TL</span><span style="color:#ff6b6b;">Kalan: {kalan:,.0f} TL</span></div></div>', unsafe_allow_html=True)
            with st.expander("Düzenle"):
                c_up1, c_up2 = st.columns([3,1])
                new_pay = c_up1.number_input("Ödenen", value=float(r['odenen']), key=f"np_{r['id']}")
                if c_up1.button("Güncelle", key=f"up_{r['id']}"):
                    df.at[df[df['id']==r['id']].index[0], 'odenen'] = new_pay; save_data(df); st.rerun()
                if c_up2.button("Sil", key=f"del_ex_{r['id']}"):
                    df = df[df['id'] != r['id']]; save_data(df); st.rerun()

# TAB 3: YAPILACAKLAR
with tabs[2]:
    col_add, col_spc = st.columns([2, 1])
    with col_add:
        st.subheader("📝 Görevler")
        with st.form("todo_add", clear_on_submit=True, border=False):
            c_inp, c_btn = st.columns([4, 1])
            t_txt = c_inp.text_input("Yeni görev...", label_visibility="collapsed")
            if c_btn.form_submit_button("Ekle", use_container_width=True):
                new_row = {"id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"), "tur": "ToDo", "baslik": t_txt, "durum": "Yapılacak", "fiyat":0, "odenen":0, "adet":1, "url":"", "img":"", "kategori":"", "notlar":""}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()
    
    st.write("")
    todos = filtered_df[filtered_df['tur'] == 'ToDo'].sort_values('id', ascending=False)
    if todos.empty: st.info("Yapılacak bir şey yok.")
    else:
        for i, r in todos.iterrows():
            is_checked = r['durum'] == "Yapıldı"
            with st.container(border=True):
                c_chk, c_txt, c_del = st.columns([1, 15, 1])
                if c_chk.checkbox("", value=is_checked, key=f"chk_{r['id']}"):
                    new_status = "Yapılacak" if is_checked else "Yapıldı"
                    df.at[df[df['id']==r['id']].index[0], 'durum'] = new_status; save_data(df); st.rerun()
                
                html_content = f'<div class="task-done">{r["baslik"]} <span class="badge-done">✔ TAMAMLANDI</span></div>' if is_checked else f'<div class="task-active">{r["baslik"]}</div>'
                c_txt.markdown(html_content, unsafe_allow_html=True)
                
                if c_del.button("✕", key=f"del_td_{r['id']}", help="Sil"):
                    df = df[df['id'] != r['id']]; save_data(df); st.rerun()

# TAB 4: REHBER
with tabs[3]:
    c_u1, c_u2 = st.columns(2)
    with c_u1:
        st.subheader("📞 Kişi Ekle")
        with st.form("usta_add", clear_on_submit=True):
            nm = st.text_input("Ad / Firma")
            cat = st.selectbox("Hizmet", ["Nakliye", "Mobilya", "Perde", "Beyaz Eşya", "Fotoğraf", "Organizasyon", "Tadilat", "Diğer"])
            tel = st.text_input("Tel (Başında 0 olmadan)")
            if st.form_submit_button("Kaydet"):
                tel_cleaned = clean_phone(tel)
                new_row = {"id": str(int(time.time())), "tur": "Usta", "baslik": nm, "notlar": tel_cleaned, "fiyat":0, "odenen":0, "adet":1, "url":"", "img":"", "durum":"", "kategori": cat}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()
    with c_u2:
        st.subheader("👥 Davetli Ekle")
        with st.form("guest_add", clear_on_submit=True):
            g_nm = st.text_input("Ad Soyad")
            g_masa = st.number_input("Masa No", min_value=1)
            if st.form_submit_button("Ekle"):
                new_row = {"id": str(int(time.time())), "tur": "Davetli", "baslik": g_nm, "adet": g_masa, "durum":"LCV Bekliyor", "fiyat":0, "odenen":0, "url":"", "img":"", "kategori":"", "notlar":""}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()
    
    st.divider()
    ustalar = df[df['tur'] == 'Usta']
    if not ustalar.empty:
        st.markdown("### 📋 Rehber")
        for i, u in ustalar.iterrows():
            with st.container(border=True):
                col_info, col_call, col_del = st.columns([3, 2, 1])
                with col_info: st.write(f"**{u['baslik']}** ({u['kategori']})")
                with col_call:
                    tel_display = clean_phone(u['notlar'])
                    if tel_display: st.markdown(f'<a href="tel:{tel_display}" class="phone-link">📞 {tel_display}</a>', unsafe_allow_html=True)
                    else: st.write("-")
                with col_del:
                    if st.button("Sil", key=f"del_usta_{u['id']}"):
                        df = df[df['id'] != u['id']]; save_data(df); st.rerun()

# TAB 5: ANALİZ
with tabs[4]:
    alisveris = df[df['tur'] == 'Alisveris']
    ekstra = df[df['tur'] == 'Ekstra']
    grand_total = alisveris['fiyat'].sum() + ekstra['fiyat'].sum()
    grand_paid = alisveris[alisveris['durum']=='Alındı']['fiyat'].sum() + ekstra['odenen'].sum()
    grand_debt = grand_total - grand_paid
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Plan", f"{grand_total:,.0f} TL")
    m2.metric("Ödenen", f"{grand_paid:,.0f} TL")
    m3.metric("Kalan", f"{grand_debt:,.0f} TL")
    if not alisveris.empty:
        fig = px.pie(alisveris, values='fiyat', names='kategori', title="Harcama Dağılımı", hole=0.5, template="plotly_dark" if st.session_state.theme=="Dark Luxury" else "plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# Footer
text_color_footer = "#000000" if st.session_state.theme == "Light Elegance" else "#ffffff"
st.markdown(f'<div class="sticky-footer"><div style="font-weight:bold; color:{text_color_footer}">Toplam: {grand_total:,.0f} TL</div><div style="opacity:0.7; color:{text_color_footer}">Yuva & Co.</div></div>', unsafe_allow_html=True)
