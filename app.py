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

# --- 2. TEMA VE CSS MOTORU ---
if "theme" not in st.session_state:
    st.session_state.theme = "Dark Luxury"

def load_css():
    # Tema Değişkenleri
    if st.session_state.theme == "Dark Luxury":
        bg_color = "#000000" # Tam siyah arka plan (OLED dostu)
        text_color = "#f5f5f7" # Apple beyazı
        # Apple Dark Mode Card Rengi
        card_bg = "#1c1c1e" 
        card_border = "#2c2c2e"
        accent = "#d4af37" # Gold
        input_bg = "#1c1c1e"
        menu_bg = "#2c2c2e"
        btn_bg = "#2c2c2e"
        btn_txt = "#f5f5f7"
        shadow = "rgba(0,0,0,0.5)"
        
        # To-Do Özel Renkleri (Dark)
        todo_bg = "#1c1c1e"
        todo_border = "#2c2c2e"
        todo_hover = "#2c2c2e"
        
    else: # Light Elegance
        bg_color = "#f5f5f7" # Apple Light Gri Arka Plan
        text_color = "#1d1d1f" # Apple Siyahı
        card_bg = "#ffffff"
        card_border = "#e5e5ea" # Apple sınır grisi
        accent = "#d4af37" 
        input_bg = "#ffffff"
        menu_bg = "#ffffff"
        btn_bg = "#ffffff"
        btn_txt = "#1d1d1f"
        shadow = "rgba(0,0,0,0.05)"
        
        # To-Do Özel Renkleri (Light)
        todo_bg = "#ffffff"
        todo_border = "#e5e5ea"
        todo_hover = "#fbfbfd"

    common_css = f"""
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600&family=Playfair+Display:wght@400;600;700&family=Montserrat:wght@300;400;500;600&display=swap');
        
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        h1, h2, h3, h4 {{ font-family: 'Playfair Display', serif !important; color: {accent} !important; }}
        
        .stApp {{ background-color: {bg_color}; color: {text_color}; }}
        
        /* --- APPLE STYLE TO-DO KARTLARI --- */
        
        /* Streamlit Container (border=True) özelleştirme */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {todo_bg};
            border: 1px solid {todo_border};
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 2px 5px {shadow};
        }}
        
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            background-color: {todo_hover};
            transform: scale(1.005);
            box-shadow: 0 4px 12px {shadow};
            border-color: {accent};
        }}
        
        /* Checkbox Özelleştirme (Daha yuvarlak ve modern) */
        .stCheckbox label {{ color: {text_color} !important; font-size: 1rem; font-weight: 500; }}
        
        /* Yapıldı Durumu (Strikethrough Animasyonu) */
        .todo-done {{
            text-decoration: line-through;
            color: #86868b !important; /* Apple disabled gray */
            transition: color 0.3s ease;
        }}
        
        /* --- GENEL KART TASARIMI (KOLEKSİYON) --- */
        .grand-card {{
            border-radius: 18px; /* Apple tarzı daha yumuşak köşeler */
            overflow: hidden; margin-bottom: 20px; 
            position: relative; height: 100%; display: flex; flex-direction: column;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            background: {card_bg} !important; 
            border: 1px solid {card_border};
            box-shadow: 0 4px 10px {shadow};
        }}
        .grand-card:hover {{ transform: translateY(-5px); border-color: {accent}; box-shadow: 0 15px 30px {shadow}; }}
        
        .img-area {{ 
            width: 100%; height: 220px; 
            background: #fff; 
            overflow:hidden; position: relative; display: flex; align-items: center; justify-content: center; 
            border-bottom: 1px solid {card_border}; 
        }}
        .img-area img {{ width: 100%; height: 100%; object-fit: contain; padding: 15px; }}
        
        .content-area {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; color: {text_color}; }}
        
        /* GİDER KARTI */
        .expense-card {{
            padding: 20px; border-radius: 18px; margin-bottom: 15px;
            border-left: 5px solid {accent}; 
            background: {card_bg} !important; 
            border: 1px solid {card_border}; 
            color: {text_color};
            box-shadow: 0 2px 8px {shadow};
        }}
        
        /* INPUTLAR (ZORLA RENK ATAMA) */
        .stTextInput input, .stNumberInput input, .stTextArea textarea {{
            color: {text_color} !important;
            background-color: {input_bg} !important;
            border-radius: 10px !important; /* Daha yuvarlak inputlar */
            padding: 10px 12px !important;
        }}
        
        /* BUTONLAR */
        .stButton>button {{
            background-color: {btn_bg} !important;
            color: {btn_txt} !important;
            border: 1px solid {card_border} !important;
            border-radius: 10px !important;
            transition: all 0.3s ease;
            font-weight: 500;
        }}
        .stButton>button:hover {{
            border-color: {accent} !important;
            color: {accent} !important;
            transform: scale(1.02);
        }}

        /* STICKY FOOTER */
        .sticky-footer {{
            position: fixed; bottom: 0; left: 0; width: 100%; z-index: 999;
            background: {card_bg}; border-top: 1px solid {card_border};
            padding: 15px 30px; display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 -5px 20px {shadow};
            backdrop-filter: blur(20px); /* Buzlu cam efekti */
            -webkit-backdrop-filter: blur(20px);
        }}
        
        /* TELEFON LİNKİ */
        a.phone-link {{ color: #34c759 !important; text-decoration: none; font-weight: bold; }}
        a.phone-link:hover {{ text-decoration: underline; }}
        
        /* HERO SAYACI */
        .hero-counter {{ text-align: center; padding: 60px 20px; margin-bottom: 30px; }}
        .hero-days {{ font-size: 5rem; font-weight: 700; color: {accent}; line-height: 1; font-family: 'Playfair Display', serif; letter-spacing: -2px; }}
        .hero-label {{ font-size: 1rem; letter-spacing: 4px; text-transform: uppercase; opacity: 0.6; color: {text_color} !important; margin-bottom: 10px; }}
        .hero-date {{ font-size: 1.1rem; color: #86868b !important; margin-top: 15px; font-weight: 500; }}
        
        /* GLOBAL DÜZELTMELER */
        div[data-baseweb="select"] span {{ color: {text_color} !important; }}
        div[data-baseweb="popover"], div[data-baseweb="menu"] {{ background-color: {menu_bg} !important; border: 1px solid {card_border} !important; }}
        div[data-baseweb="option"] {{ color: {text_color} !important; }}
    """
    st.markdown(f"<style>{common_css}</style>", unsafe_allow_html=True)

# --- 3. VERİ YÖNETİMİ ---
def get_data():
    required_cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum', 'adet', 'odenen']
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        if df is None or df.empty: return pd.DataFrame(columns=required_cols)
        for col in required_cols:
            if col not in df.columns: df[col] = ""
        df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
        df['odenen'] = pd.to_numeric(df['odenen'], errors='coerce').fillna(0)
        df['adet'] = pd.to_numeric(df['adet'], errors='coerce').fillna(1)
        return df.fillna("")
    except Exception as e:
        st.error(f"Veri bağlantı hatası: {e}")
        return pd.DataFrame(columns=required_cols)

def save_data(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Sayfa1", data=df)
        st.cache_data.clear()
    except Exception as e: st.warning("Kaydetme hatası.")

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

# --- 4. BAŞLANGIÇ ---
with st.sidebar:
    st.markdown("### 💍 Yuva & Co.")
    st.divider()
    theme_choice = st.radio("Tema Seçimi", ["Dark Luxury", "Light Elegance"], index=0 if st.session_state.theme == "Dark Luxury" else 1)
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()
    st.divider()
    if "last_undo" not in st.session_state: st.session_state.last_undo = None
    if st.button("♻️ Geri Al (Undo)", disabled=st.session_state.last_undo is None):
        if st.session_state.last_undo is not None:
            df = pd.concat([df, st.session_state.last_undo], ignore_index=True)
            save_data(df); st.session_state.last_undo = None; st.rerun()
    if st.button("📥 Excel Yedek Al"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("İndir", output.getvalue(), f"Yuva_Yedek.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

load_css()
df = get_data()

# HERO & SAYAÇ
days_left = (TARGET_DATE - date.today()).days
st.markdown(f"""<div class="hero-counter"><div class="hero-label">BÜYÜK GÜNE KALAN</div><div class="hero-days">{days_left} Gün</div><div class="hero-date">25 Nisan 2026</div></div>""", unsafe_allow_html=True)

# Arama
c_hero1, c_hero2 = st.columns([3,1])
with c_hero1:
    search = st.text_input("🔍 Ara...", placeholder="Ürün, görev veya kişi ara...")

if df.empty: filtered_df = df
else:
    mask = df.apply(lambda x: search.lower() in str(x).lower(), axis=1) if search else [True] * len(df)
    filtered_df = df[mask]

# --- 5. SEKMELER ---
tabs = st.tabs(["🛍️ KOLEKSİYON", "💸 GİDER & KAPORA", "✅ YAPILACAKLAR", "👥 REHBER & DAVET", "📊 ANALİZ"])

# === TAB 1: KOLEKSİYON ===
with tabs[0]:
    with st.container():
        c_filt1, c_filt2 = st.columns(2)
        filter_status = c_filt1.selectbox("Filtre", ["Tümü", "Sadece Alınacaklar", "Sadece Alınanlar"])
        sort_option = c_filt2.selectbox("Sıralama", ["En Yeni", "En Eski", "Pahalıdan Ucuza", "Ucuzdan Pahalıya"])
    
    st.write("") 
    with st.popover("➕ YENİ EŞYA EKLE", use_container_width=True):
        with st.form("add_item", clear_on_submit=True):
            u_url = st.text_input("Link")
            u_cat = st.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            u_prc = st.number_input("Birim Fiyat", min_value=0.0)
            u_qty = st.number_input("Adet", min_value=1, value=1)
            if st.form_submit_button("KAYDET"):
                tit, img = scrape_metadata(u_url)
                new_row = {"id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"), "ekleyen": "Biz", "tur": "Alisveris", "kategori": u_cat, "baslik": tit, "fiyat": u_prc * u_qty, "ilk_fiyat": u_prc * u_qty, "url": u_url, "img": img, "durum": "Alınacak", "adet": u_qty, "odenen": 0, "notlar": ""}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()

    items = filtered_df[filtered_df['tur'] == 'Alisveris']
    if filter_status == "Sadece Alınacaklar": items = items[items['durum'] != 'Alındı']
    elif filter_status == "Sadece Alınanlar": items = items[items['durum'] == 'Alındı']
    
    if sort_option == "En Yeni": items = items.sort_values('id', ascending=False)
    elif sort_option == "En Eski": items = items.sort_values('id', ascending=True)
    elif sort_option == "Pahalıdan Ucuza": items = items.sort_values('fiyat', ascending=False)
    elif sort_option == "Ucuzdan Pahalıya": items = items.sort_values('fiyat', ascending=True)

    if items.empty: st.info("Liste boş.")
    else:
        cols = st.columns(3)
        for i, (idx, row) in enumerate(items.iterrows()):
            with cols[i % 3]:
                is_done = row['durum'] == "Alındı"
                overlay = '<div style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:2;pointer-events:none;"><span style="font-size:3rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));">✅</span></div>' if is_done else ""
                img_src = row['img'] if row['img'] else "https://cdn-icons-png.flaticon.com/512/3081/3081840.png"
                st.markdown(f'<div class="grand-card">{overlay}<div class="img-area"><img src="{img_src}"></div><div class="content-area"><div style="opacity:0.7; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">{row["kategori"]}</div><h4 style="margin:5px 0; font-size:1.1rem; line-height:1.4;">{row["baslik"]}</h4><div style="font-size:1.3rem; color:#d4af37; font-weight:700; margin-top:auto;">{float(row["fiyat"]):,.0f} TL</div></div></div>', unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("✅ ALDIK" if not is_done else "İPTAL", key=f"st_{row['id']}", use_container_width=True):
                    df.at[idx, 'durum'] = "Alındı" if not is_done else "Alınacak"
                    save_data(df); st.rerun()
                if b2.button("🗑️ SİL", key=f"dl_{row['id']}", use_container_width=True):
                    st.session_state.last_undo = df.loc[[idx]]; df = df.drop(idx); save_data(df); st.rerun()

# === TAB 2: GİDER ===
with tabs[1]:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📌 Gider / Hizmet Ekle")
        with st.form("add_expense", clear_on_submit=True):
            e_ad = st.text_input("Gider Adı")
            e_top = st.number_input("TOPLAM Tutar", min_value=0.0)
            e_kap = st.number_input("ÖDENEN (Kapora)", min_value=0.0)
            e_kat = st.selectbox("Kategori", ["Düğün", "Balayı", "Ev Tadilat", "Diğer"])
            if st.form_submit_button("EKLE"):
                new_row = {"id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"), "tur": "Ekstra", "baslik": e_ad, "fiyat": e_top, "odenen": e_kap, "kategori": e_kat, "durum": "Bekliyor", "adet": 1, "url":"", "img":"", "notlar":""}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()
    with c2:
        st.subheader("💸 Ödeme Durumu")
        expenses = filtered_df[filtered_df['tur'] == 'Ekstra']
        for i, r in expenses.iterrows():
            kalan = float(r['fiyat']) - float(r['odenen'])
            pct = float(r['odenen']) / float(r['fiyat']) if float(r['fiyat']) > 0 else 0
            st.markdown(f'<div class="expense-card"><div style="display:flex; justify-content:space-between; font-weight:700; font-size:1.1rem;"><span>{r["baslik"]}</span><span>{float(r["fiyat"]):,.0f} TL</span></div><div style="margin:10px 0; height:8px; background:rgba(128,128,128,0.2); border-radius:4px;"><div style="width:{min(pct*100, 100)}%; height:100%; background:#d4af37; border-radius:4px; box-shadow:0 0 10px rgba(212,175,55,0.3);"></div></div><div style="display:flex; justify-content:space-between; font-size:0.9rem; margin-top:5px;"><span style="color:#4ade80;">Ödenen: {float(r["odenen"]):,.0f} TL</span><span style="color:#ff6b6b;">Kalan: {kalan:,.0f} TL</span></div></div>', unsafe_allow_html=True)
            with st.expander("Düzenle"):
                c_up1, c_up2 = st.columns([3,1])
                new_pay = c_up1.number_input("Ödenen", value=float(r['odenen']), key=f"np_{r['id']}")
                if c_up1.button("Güncelle", key=f"up_{r['id']}"):
                    df.at[df[df['id']==r['id']].index[0], 'odenen'] = new_pay
                    save_data(df); st.rerun()
                if c_up2.button("Sil", key=f"del_ex_{r['id']}"):
                    df = df[df['id'] != r['id']]; save_data(df); st.rerun()

# === TAB 3: YAPILACAKLAR (APPLE STYLE) ===
with tabs[2]:
    # Başlık ve Hızlı Ekleme Yan Yana
    col_add, col_spc = st.columns([2, 1])
    with col_add:
        st.subheader("📝 Yapılacaklar Listesi")
        with st.form("todo_add", clear_on_submit=True, border=False):
            c_inp, c_btn = st.columns([4, 1])
            t_txt = c_inp.text_input("Yeni görev ekle...", label_visibility="collapsed")
            if c_btn.form_submit_button("Ekle", use_container_width=True):
                new_row = {"id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"), "tur": "ToDo", "baslik": t_txt, "durum": "Yapılacak", "fiyat":0, "odenen":0, "adet":1, "url":"", "img":"", "kategori":"", "notlar":""}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()
    
    st.write("") # Boşluk
    
    todos = filtered_df[filtered_df['tur'] == 'ToDo'].sort_values('id', ascending=False)
    
    if todos.empty:
        st.info("Henüz yapılacak bir görev yok. Keyfini çıkarın! 🎉")
    else:
        for i, r in todos.iterrows():
            is_checked = r['durum'] == "Yapıldı"
            
            # Apple Style Card Container (border=True ile CSS hedefliyoruz)
            with st.container(border=True):
                c_chk, c_txt, c_del = st.columns([1, 15, 1])
                
                # 1. Checkbox
                if c_chk.checkbox("", value=is_checked, key=f"chk_{r['id']}"):
                    new_status = "Yapılacak" if is_checked else "Yapıldı"
                    if new_status != r['durum']:
                        df.at[df[df['id']==r['id']].index[0], 'durum'] = new_status
                        save_data(df); st.rerun()
                
                # 2. Metin (Strikethrough CSS sınıfı ile)
                text_class = "todo-done" if is_checked else "todo-active"
                c_txt.markdown(f'<div class="{text_class}" style="padding-top: 5px; font-size:1.05rem;">{r["baslik"]}</div>', unsafe_allow_html=True)
                
                # 3. Sil Butonu (Minimalist)
                if c_del.button("✕", key=f"del_td_{r['id']}", help="Görevi Sil"):
                    df = df[df['id'] != r['id']]; save_data(df); st.rerun()

# === TAB 4: REHBER ===
with tabs[3]:
    c_u1, c_u2 = st.columns(2)
    with c_u1:
        st.subheader("📞 Kişi / Firma Ekle")
        with st.form("usta_add", clear_on_submit=True):
            nm = st.text_input("Ad / Firma")
            cat = st.selectbox("Hizmet Türü", ["Nakliye", "Mobilya", "Perde", "Beyaz Eşya", "Fotoğraf", "Organizasyon", "Tadilat", "Diğer"])
            tel = st.text_input("Telefon (Başında 0 olmadan)")
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
            with st.container(border=True): # Rehber de kart görünümüne geçti
                col_info, col_call, col_del = st.columns([3, 2, 1])
                with col_info:
                    kategori_str = f"({u['kategori']})" if u['kategori'] else ""
                    st.write(f"**{u['baslik']}** {kategori_str}")
                with col_call:
                    tel_display = clean_phone(u['notlar'])
                    if tel_display: st.markdown(f'<a href="tel:{tel_display}" class="phone-link">📞 {tel_display}</a>', unsafe_allow_html=True)
                    else: st.write("-")
                with col_del:
                    if st.button("Sil", key=f"del_usta_{u['id']}"):
                        df = df[df['id'] != u['id']]; save_data(df); st.rerun()

# === TAB 5: ANALİZ ===
with tabs[4]:
    alisveris = df[df['tur'] == 'Alisveris']
    ekstra = df[df['tur'] == 'Ekstra']
    grand_total = alisveris['fiyat'].sum() + ekstra['fiyat'].sum()
    grand_paid = alisveris[alisveris['durum']=='Alındı']['fiyat'].sum() + ekstra['odenen'].sum()
    grand_debt = grand_total - grand_paid
    m1, m2, m3 = st.columns(3)
    m1.metric("Planlanan", f"{grand_total:,.0f} TL")
    m2.metric("Ödenen", f"{grand_paid:,.0f} TL")
    m3.metric("Kalan", f"{grand_debt:,.0f} TL")
    if not alisveris.empty:
        fig = px.pie(alisveris, values='fiyat', names='kategori', title="Harcama Dağılımı", hole=0.5, template="plotly_dark" if st.session_state.theme=="Dark Luxury" else "plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# Footer
ft_bg = "#ffffff" if st.session_state.theme == "Light Elegance" else "#1a1a1a"
ft_txt = "#000000" if st.session_state.theme == "Light Elegance" else "#ffffff"
st.markdown(f'<div class="sticky-footer" style="background:{ft_bg}; color:{ft_txt};"><div style="font-weight:bold;">Toplam: {grand_total:,.0f} TL</div><div style="opacity:0.7;">Yuva & Co.</div></div>', unsafe_allow_html=True)
