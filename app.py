import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import time
from datetime import datetime, date
import urllib.parse
from io import BytesIO
import plotly.express as px

# --- 1. AYARLAR & YAPILANDIRMA ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

# Sabitler
TARGET_DATE = date(2026, 4, 25) # Düğün Tarihi
PASSWORD = "2024"

# --- 2. SESSION STATE ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "theme" not in st.session_state: st.session_state.theme = "Dark Luxury"

# --- 3. CSS VE GÖRSEL MOTORU ---
def load_css():
    is_dark = st.session_state.theme == "Dark Luxury"
    
    bg_color = "#000000" if is_dark else "#f2f2f7"
    text_color = "#f5f5f7" if is_dark else "#1d1d1f"
    card_bg = "#1c1c1e" if is_dark else "#ffffff"
    card_border = "#2c2c2e" if is_dark else "#d1d1d6"
    accent = "#d4af37" 
    input_bg = "#1c1c1e" if is_dark else "#ffffff"
    btn_bg = "#2c2c2e" if is_dark else "#ffffff"
    btn_txt = "#fff" if is_dark else "#000"
    shadow = "rgba(0,0,0,0.5)" if is_dark else "rgba(0,0,0,0.1)"
    
    # iOS Renkleri
    ios_bg = "#000000"
    ios_item_bg = "#1c1c1e"
    ios_text = "#ffffff"
    ios_border = "#38383a"

    # SVG İkonlar
    icon_trash = '''<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff453a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>'''
    icon_phone = '''<svg width="22" height="22" viewBox="0 0 24 24" fill="#34c759" stroke="none"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>'''
    icon_check = '''<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#34c759" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'''

    common_css = f"""
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600&family=Playfair+Display:wght@400;600;700&display=swap');
        
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        h1, h2, h3, h4 {{ font-family: 'Playfair Display', serif !important; color: {accent} !important; }}
        .stApp {{ background-color: {bg_color}; color: {text_color}; }}
        
        /* IPHONE FRAME */
        .iphone-frame {{
            max-width: 400px; margin: 0 auto; background-color: {ios_bg};
            border-radius: 40px; border: 8px solid #333; padding: 20px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5); position: relative; min-height: 500px;
        }}
        .iphone-notch {{
            width: 120px; height: 25px; background: #000; margin: -20px auto 10px auto;
            border-bottom-left-radius: 15px; border-bottom-right-radius: 15px; z-index: 10;
        }}
        .ios-list-header {{ color: {ios_text}; font-size: 2rem; font-weight: bold; margin-bottom: 20px; padding-left: 10px; }}
        .ios-list-item {{
            display: flex; align-items: center; justify-content: space-between;
            background-color: {ios_item_bg}; padding: 15px; border-bottom: 1px solid {ios_border}; color: {ios_text};
        }}
        .ios-list-item:first-child {{ border-top-left-radius: 12px; border-top-right-radius: 12px; }}
        .ios-list-item:last-child {{ border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; border-bottom: none; }}
        .ios-name {{ font-weight: 600; font-size: 1rem; }}
        .ios-sub {{ font-size: 0.8rem; color: #888; }}
        
        /* TO-DO KARTLARI */
        .todo-container {{
            background-color: {card_bg}; border-radius: 12px; padding: 15px; margin-bottom: 10px;
            box-shadow: 0 2px 5px {shadow}; display: flex; align-items: center; gap: 15px;
            border: 1px solid {card_border}; transition: transform 0.2s;
        }}
        .todo-container:hover {{ transform: scale(1.01); border-color: {accent}; }}
        .todo-text {{ flex-grow: 1; font-size: 1rem; font-weight: 500; color: {text_color}; }}
        .todo-done {{ text-decoration: line-through; color: #636366; flex-grow: 1; font-size: 1rem; }}
        
        /* KART TASARIMLARI */
        .grand-card {{
            background: {card_bg}; border: 1px solid {card_border};
            border-radius: 16px; overflow: hidden; margin-bottom: 20px;
            box-shadow: 0 4px 10px {shadow}; transition: 0.3s;
        }}
        .grand-card:hover {{ transform: translateY(-5px); border-color: {accent}; }}
        .img-area {{ width: 100%; height: 200px; background: #fff; display: flex; align-items: center; justify-content: center; }}
        .img-area img {{ max-height: 90%; max-width: 90%; object-fit: contain; }}
        .content-area {{ padding: 15px; color: {text_color}; }}
        
        .expense-card {{
            background: {card_bg}; border: 1px solid {card_border};
            border-left: 4px solid {accent}; border-radius: 12px; padding: 15px; margin-bottom: 10px; color: {text_color};
        }}
        
        /* WIDGETS */
        .stTextInput input, .stNumberInput input, .stSelectbox, .stTextArea textarea {{
            background: {input_bg} !important; color: {text_color} !important;
            border: 1px solid {card_border} !important; border-radius: 10px !important;
        }}
        .stButton>button {{
            background: {btn_bg} !important; color: {btn_txt} !important;
            border: 1px solid {card_border} !important; border-radius: 10px !important;
        }}
        .hero-days {{ font-size: 4rem; font-weight: 700; color: {accent}; font-family: 'Playfair Display', serif; text-align: center; }}
        .hero-sub {{ text-align: center; font-size: 0.9rem; letter-spacing: 2px; opacity: 0.7; color: {text_color}; }}
        .sticky-footer {{
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            background: {card_bg}; border: 1px solid {card_border};
            padding: 10px 30px; border-radius: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            display: flex; gap: 20px; align-items: center; z-index: 9999;
        }}
    """
    st.markdown(f"<style>{common_css}</style>", unsafe_allow_html=True)
    return icon_trash, icon_phone, icon_check

# --- 4. VERİ YÖNETİMİ ---
def get_data():
    req = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum', 'adet', 'odenen']
    conn = st.connection("gsheets", type=GSheetsConnection)
    for _ in range(3):
        try:
            df = conn.read(ttl=0)
            if df is None or df.empty: return pd.DataFrame(columns=req)
            for c in req: 
                if c not in df.columns: df[c] = ""
            df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
            df['odenen'] = pd.to_numeric(df['odenen'], errors='coerce').fillna(0)
            df['adet'] = pd.to_numeric(df['adet'], errors='coerce').fillna(1)
            return df.fillna("")
        except: time.sleep(1)
    return pd.DataFrame(columns=req)

def save_data(df):
    conn = st.connection("gsheets", type=GSheetsConnection)
    for _ in range(3):
        try: conn.update(worksheet="Sayfa1", data=df); st.cache_data.clear(); return
        except: time.sleep(1)

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

def clean_phone(p):
    s = ''.join(filter(str.isdigit, str(p)))
    return "0" + s if len(s) == 10 else s

# --- 5. UYGULAMA ---
if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"<h1 style='text-align:center; color:#d4af37; font-size:3rem;'>Yuva & Co.</h1>", unsafe_allow_html=True)
        pwd = st.text_input("Giriş Şifresi", type="password")
        if st.button("Giriş", use_container_width=True):
            if pwd == PASSWORD: st.session_state.authenticated = True; st.rerun()
            else: st.error("Hatalı")
    st.stop()

icon_trash, icon_phone, icon_check = load_css()
df = get_data()

with st.sidebar:
    st.markdown("### 💍 Yuva & Co.")
    st.divider()
    tm = st.radio("Tema", ["Dark Luxury", "Light Elegance"], index=0 if st.session_state.theme == "Dark Luxury" else 1)
    if tm != st.session_state.theme: st.session_state.theme = tm; st.rerun()
    st.divider()
    if st.button("Çıkış"): st.session_state.authenticated = False; st.rerun()
    if st.button("📥 Yedekle"):
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
        st.download_button("İndir", out.getvalue(), "Yedek.xlsx")

days = (TARGET_DATE - date.today()).days
st.markdown(f"<div class='hero-sub'>BÜYÜK GÜNE KALAN</div><div class='hero-days'>{days} Gün</div>", unsafe_allow_html=True)

c_src, c_null = st.columns([3,1])
with c_src: search = st.text_input("🔍 Ara...", placeholder="Ürün, görev veya kişi...")
filtered_df = df[df.apply(lambda x: search.lower() in str(x).lower(), axis=1)] if not df.empty else df

tabs = st.tabs(["🛍️ KOLEKSİYON", "💸 GİDERLER", "✅ YAPILACAKLAR", "📱 REHBER", "📊 DURUM"])

# TAB 1: KOLEKSİYON
with tabs[0]:
    with st.popover("➕ ÜRÜN EKLE", use_container_width=True):
        with st.form("add_item", clear_on_submit=True):
            lnk = st.text_input("Link"); cat = st.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Diğer"])
            prc = st.number_input("Fiyat"); qty = st.number_input("Adet", 1)
            if st.form_submit_button("EKLE"):
                tt, im = scrape_metadata(lnk)
                row = {"id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"), "tur": "Alisveris", "kategori": cat, "baslik": tt, "fiyat": prc*qty, "url": lnk, "img": im, "durum": "Alınacak", "adet": qty}
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True); save_data(df); st.rerun()
    
    items = filtered_df[filtered_df['tur'] == 'Alisveris']
    if not items.empty:
        cols = st.columns(3)
        for i, (ix, row) in enumerate(items.iterrows()):
            with cols[i%3]:
                bought = row['durum'] == "Alındı"
                ovl = f'<div style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:2;">{icon_check}</div>' if bought else ""
                st.markdown(f'<div class="grand-card">{ovl}<div class="img-area"><img src="{row["img"]}"></div><div class="content-area"><div style="opacity:0.7;font-size:0.8rem;">{row["kategori"]}</div><div style="font-weight:bold;margin:5px 0;">{row["baslik"]}</div><div style="color:#d4af37;font-size:1.2rem;">{row["fiyat"]:,.0f} TL</div></div></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                if c1.button("ALDIK" if not bought else "İPTAL", key=f"b{row['id']}", use_container_width=True):
                    df.at[ix, 'durum'] = "Alındı" if not bought else "Alınacak"; save_data(df); st.rerun()
                if c2.button("SİL", key=f"d{row['id']}", use_container_width=True):
                    df = df.drop(ix); save_data(df); st.rerun()

# TAB 2: GİDERLER
with tabs[1]:
    with st.popover("➕ GİDER EKLE", use_container_width=True):
        with st.form("add_exp", clear_on_submit=True):
            nm = st.text_input("Gider"); tp = st.number_input("Toplam"); pd_ = st.number_input("Ödenen")
            if st.form_submit_button("KAYDET"):
                row = {"id": str(int(time.time())), "tur": "Ekstra", "baslik": nm, "fiyat": tp, "odenen": pd_, "durum": "Bekliyor"}
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True); save_data(df); st.rerun()
    
    exps = filtered_df[filtered_df['tur'] == 'Ekstra']
    for i, r in exps.iterrows():
        rem = r['fiyat'] - r['odenen']
        pct = (r['odenen'] / r['fiyat'] * 100) if r['fiyat'] > 0 else 0
        st.markdown(f'<div class="expense-card"><div style="display:flex;justify-content:space-between;font-weight:bold;"><span>{r["baslik"]}</span><span>{r["fiyat"]:,.0f} TL</span></div><div style="margin:5px 0;height:5px;background:#333;border-radius:3px;"><div style="width:{pct}%;height:100%;background:#d4af37;"></div></div><div style="display:flex;justify-content:space-between;font-size:0.8rem;"><span style="color:#4ade80">Ödenen: {r["odenen"]:,.0f} TL</span><span style="color:#ff453a">Kalan: {rem:,.0f} TL</span></div></div>', unsafe_allow_html=True)
        with st.expander("Düzenle"):
            c1, c2 = st.columns([3,1])
            new_pd = c1.number_input("Ödenen", value=float(r['odenen']), key=f"p{r['id']}")
            if c1.button("GÜNCELLE", key=f"u{r['id']}"): df.at[i, 'odenen'] = new_pd; save_data(df); st.rerun()
            if c2.button("SİL", key=f"dx{r['id']}"): df = df.drop(i); save_data(df); st.rerun()

# TAB 3: YAPILACAKLAR
with tabs[2]:
    with st.form("todo_add", clear_on_submit=True, border=False):
        c1, c2 = st.columns([4,1])
        tsk = c1.text_input("Yeni görev...", label_visibility="collapsed")
        if c2.form_submit_button("EKLE", use_container_width=True):
            row = {"id": str(int(time.time())), "tur": "ToDo", "baslik": tsk, "durum": "Yapılacak"}
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True); save_data(df); st.rerun()
            
    todos = filtered_df[filtered_df['tur'] == 'ToDo'].sort_values('id', ascending=False)
    for i, r in todos.iterrows():
        done = r['durum'] == "Yapıldı"
        cls = "todo-done" if done else "todo-text"
        st.markdown(f'<div class="todo-container"><div style="font-size:1.2rem; cursor:pointer;">{"✅" if done else "⬜"}</div><div class="{cls}">{r["baslik"]}</div></div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 15])
        with c1:
            if st.button("Değiştir", key=f"t{r['id']}"): 
                df.at[i, 'durum'] = "Yapılacak" if done else "Yapıldı"; save_data(df); st.rerun()
        with c2:
            if st.button("Sil", key=f"del_t{r['id']}"): df = df.drop(i); save_data(df); st.rerun()

# TAB 4: REHBER
with tabs[3]:
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("add_contact", clear_on_submit=True):
            nm = st.text_input("İsim"); ph = st.text_input("Tel"); cat = st.text_input("Etiket")
            if st.form_submit_button("REHBERE EKLE"):
                row = {"id": str(int(time.time())), "tur": "Usta", "baslik": nm, "notlar": clean_phone(ph), "kategori": cat}
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True); save_data(df); st.rerun()
    
    with c2:
        contacts = filtered_df[filtered_df['tur'] == 'Usta']
        html_list = ""
        for i, r in contacts.iterrows():
            tel = r['notlar']
            html_list += f'<div class="ios-list-item"><div><div class="ios-name">{r["baslik"]}</div><div class="ios-sub">{r["kategori"]}</div></div><div class="ios-actions"><a href="tel:{tel}" style="text-decoration:none;">{icon_phone}</a></div></div>'
        
        st.markdown(f'<div class="iphone-frame"><div class="iphone-notch"></div><div class="ios-list-header">Kişiler</div><div style="background:#1c1c1e; border-radius:12px; overflow:hidden;">{html_list}</div></div>', unsafe_allow_html=True)
        
        with st.expander("🗑️ Kişi Sil"):
            for i, r in contacts.iterrows():
                c_del1, c_del2 = st.columns([3, 1])
                c_del1.write(f"{r['baslik']}")
                if c_del2.button("Sil", key=f"del_c{r['id']}"):
                    df = df.drop(i); save_data(df); st.rerun()

# TAB 5: ANALİZ
with tabs[4]:
    analiz_items = df[df['tur']=='Alisveris']
    
    # Giderleri de hesaba kat (Veriler geri geldi)
    analiz_gider = df[df['tur'] == 'Ekstra']
    
    grand_total = analiz_items['fiyat'].sum() + analiz_gider['fiyat'].sum()
    grand_paid = analiz_items[analiz_items['durum']=='Alındı']['fiyat'].sum() + analiz_gider['odenen'].sum()
    grand_debt = grand_total - grand_paid
    
    if not analiz_items.empty:
        fig = px.pie(analiz_items, values='fiyat', names='kategori', title="Harcamalar", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
    # Toplam Bütçe Kartları (Düzeltildi)
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Planlanan", f"{grand_total:,.0f} TL")
    c2.metric("Toplam Ödenen", f"{grand_paid:,.0f} TL")
    c3.metric("Kalan Borç", f"{grand_debt:,.0f} TL", delta_color="inverse")

# Footer
text_color_footer = "#000000" if st.session_state.theme == "Light Elegance" else "#ffffff"
st.markdown(f'<div class="sticky-footer"><div style="font-weight:bold; color:{text_color_footer}">Toplam: {grand_total:,.0f} TL</div><div style="opacity:0.7; color:{text_color_footer}">Yuva & Co.</div></div>', unsafe_allow_html=True)


