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
        bg_color = "#0e0e0e"
        text_color = "#e0e0e0"
        card_bg = "#1a1a1a"
        card_border = "#333"
        accent = "#d4af37" # Gold
        input_bg = "#1a1a1a"
        menu_bg = "#262730"
        btn_bg = "#222"
        btn_txt = "#fff"
        shadow = "rgba(0,0,0,0.5)"
    else: # Light Elegance (TAMİR EDİLDİ - YÜKSEK KONTRAST)
        bg_color = "#ffffff" 
        text_color = "#000000" # Simsiyah yazı
        card_bg = "#f9f9f9" # Kartlar hafif gri ayrılsın
        card_border = "#cccccc" # Belirgin çerçeve
        accent = "#d4af37" 
        input_bg = "#ffffff"
        menu_bg = "#ffffff"
        btn_bg = "#f0f0f0"
        btn_txt = "#000000"
        shadow = "rgba(0,0,0,0.1)"

    common_css = f"""
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Montserrat:wght@300;400;500;600&display=swap');
        body {{ font-family: 'Montserrat', sans-serif; }}
        h1, h2, h3, h4 {{ font-family: 'Playfair Display', serif !important; color: {accent} !important; }}
        
        /* Genel Yazı Renkleri - Zorla Uygula */
        .stApp, .stMarkdown, p, span, div, label, h1, h2, h3, h4, h5, h6 {{ color: {text_color} !important; }}
        .stApp {{ background-color: {bg_color}; }}
        
        /* KART TASARIMI */
        .grand-card {{
            border-radius: 12px; overflow: hidden; margin-bottom: 20px; 
            position: relative; height: 100%; display: flex; flex-direction: column;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            background: {card_bg} !important; 
            border: 1px solid {card_border};
            box-shadow: 0 4px 10px {shadow};
        }}
        .grand-card:hover {{ transform: translateY(-5px); border-color: {accent}; box-shadow: 0 10px 20px {shadow}; }}
        
        /* RESİM ALANI */
        .img-area {{ 
            width: 100%; height: 220px; 
            background: #fff; /* Resim alanı her zaman beyaz olsun ürün net görünsün */
            overflow:hidden; position: relative; display: flex; align-items: center; justify-content: center; 
            border-bottom: 1px solid {card_border}; 
        }}
        .img-area img {{ width: 100%; height: 100%; object-fit: contain; padding: 10px; }}
        
        .content-area {{ padding: 15px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; color: {text_color}; }}
        
        /* GİDER KARTI */
        .expense-card {{
            padding: 15px; border-radius: 12px; margin-bottom: 15px;
            border-left: 5px solid {accent}; 
            background: {card_bg} !important; 
            border: 1px solid {card_border}; 
            color: {text_color};
            box-shadow: 0 2px 5px {shadow};
        }}
        
        /* INPUTLAR (ZORLA RENK ATAMA) */
        input, textarea, select {{
            color: {text_color} !important;
            background-color: {input_bg} !important;
        }}
        
        /* Streamlit Widget Düzeltmeleri */
        .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div, .stTextArea>div>div {{
            background-color: {input_bg} !important;
            border-color: {card_border} !important;
        }}
        .stTextInput input, .stNumberInput input, .stTextArea textarea {{
            color: {text_color} !important;
        }}
        
        /* Dropdown Metinleri */
        div[data-baseweb="select"] span {{
            color: {text_color} !important;
        }}
        
        /* BUTONLAR */
        .stButton>button {{
            background-color: {btn_bg} !important;
            color: {btn_txt} !important;
            border: 1px solid {card_border} !important;
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            border-color: {accent} !important;
            color: {accent} !important;
        }}

        /* STICKY FOOTER */
        .sticky-footer {{
            position: fixed; bottom: 0; left: 0; width: 100%; z-index: 999;
            background: {card_bg}; border-top: 1px solid {card_border};
            padding: 10px 20px; display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 -2px 10px {shadow};
        }}
        
        /* TELEFON LİNKİ */
        a.phone-link {{ color: #4ade80 !important; text-decoration: none; font-weight: bold; }}
        a.phone-link:hover {{ text-decoration: underline; }}
        
        /* HERO SAYACI */
        .hero-counter {{ text-align: center; padding: 40px 20px; margin-bottom: 20px; }}
        .hero-days {{ font-size: 4rem; font-weight: bold; color: {accent}; line-height: 1; font-family: 'Playfair Display', serif; }}
        .hero-label {{ font-size: 1.2rem; letter-spacing: 2px; text-transform: uppercase; opacity: 0.8; color: {text_color} !important; }}
        .hero-date {{ font-size: 1rem; color: #888 !important; margin-top: 10px; }}
    """
    st.markdown(f"<style>{common_css}</style>", unsafe_allow_html=True)

# --- 3. VERİ YÖNETİMİ (GÜÇLENDİRİLMİŞ) ---
def get_data():
    # Zorunlu sütunlar listesi
    required_cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum', 'adet', 'odenen']
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        
        # Eğer veri boş veya None gelirse boş DataFrame oluştur
        if df is None or df.empty:
            return pd.DataFrame(columns=required_cols)

        # Eksik sütunları tamamla (ÇÖKME ÖNLEYİCİ)
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" # Eksik sütunu boş string ile oluştur
        
        # Sayısal dönüşümler (Hata vermeden)
        df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
        df['odenen'] = pd.to_numeric(df['odenen'], errors='coerce').fillna(0)
        df['adet'] = pd.to_numeric(df['adet'], errors='coerce').fillna(1)
        
        # NaN değerleri temizle
        df = df.fillna("")
        
        return df
    except Exception as e:
        # Bağlantı hatası olursa uygulamayı çökertme, boş tablo ile aç
        st.error(f"Veri bağlantı hatası, yerel modda açılıyor: {e}")
        return pd.DataFrame(columns=required_cols)

def save_data(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Sayfa1", data=df)
        st.cache_data.clear()
    except Exception as e:
        st.warning("Kaydetme sırasında bir hata oluştu, ancak işlem devam ediyor.")

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
    return digits

# --- 4. BAŞLANGIÇ ---
# Sidebar
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

# --- 5. HERO & ORTA SAYAÇ ---
days_left = (TARGET_DATE - date.today()).days

st.markdown(f"""
<div class="hero-counter">
    <div class="hero-label">BÜYÜK GÜNE KALAN</div>
    <div class="hero-days">{days_left} Gün</div>
    <div class="hero-date">25 Nisan 2026</div>
</div>
""", unsafe_allow_html=True)

# Arama
c_hero1, c_hero2 = st.columns([3,1])
with c_hero1:
    search = st.text_input("🔍 Evin içinde ara...", placeholder="Ürün, Gider veya Not ara...")

# HATA ÖNLEYİCİ ARAMA MANTIĞI
if df.empty:
    filtered_df = df # Boşsa aynen bırak
else:
    mask = df.apply(lambda x: search.lower() in str(x).lower(), axis=1) if search else [True] * len(df)
    filtered_df = df[mask]

# --- 6. SEKMELER ---
tabs = st.tabs(["🛍️ KOLEKSİYON", "💸 GİDER & KAPORA", "📝 YAPILACAKLAR", "👥 DAVET & USTA", "📊 ANALİZ"])

# === TAB 1: KOLEKSİYON ===
with tabs[0]:
    with st.container():
        c_filt1, c_filt2 = st.columns(2)
        filter_status = c_filt1.selectbox("Görünüm Filtresi", ["Tümü", "Sadece Alınacaklar", "Sadece Alınanlar"])
        sort_option = c_filt2.selectbox("Sıralama", ["En Yeni Eklenen", "En Eski Eklenen", "Fiyat: Yüksekten Düşüğe", "Fiyat: Düşükten Yükseğe"])
    
    st.write("") 

    with st.popover("➕ YENİ EŞYA EKLE", use_container_width=True):
        with st.form("add_item"):
            u_url = st.text_input("Link")
            u_cat = st.selectbox("Kategori", ["Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            u_prc = st.number_input("Birim Fiyat", min_value=0.0)
            u_qty = st.number_input("Adet", min_value=1, value=1)
            if st.form_submit_button("KAYDET"):
                tit, img = scrape_metadata(u_url)
                new_row = {
                    "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                    "ekleyen": "Biz", "tur": "Alisveris", "kategori": u_cat,
                    "baslik": tit, "fiyat": u_prc * u_qty, "ilk_fiyat": u_prc * u_qty,
                    "url": u_url, "img": img, "durum": "Alınacak", "adet": u_qty, "odenen": 0, "notlar": ""
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df); st.rerun()

    items = filtered_df[filtered_df['tur'] == 'Alisveris']
    
    if filter_status == "Sadece Alınacaklar": items = items[items['durum'] != 'Alındı']
    elif filter_status == "Sadece Alınanlar": items = items[items['durum'] == 'Alındı']
        
    if sort_option == "En Yeni Eklenen": items = items.sort_values('id', ascending=False)
    elif sort_option == "En Eski Eklenen": items = items.sort_values('id', ascending=True)
    elif sort_option == "Fiyat: Yüksekten Düşüğe": items = items.sort_values('fiyat', ascending=False)
    elif sort_option == "Fiyat: Düşükten Yükseğe": items = items.sort_values('fiyat', ascending=True)

    if items.empty:
        st.info("Bu kriterlere uygun eşya bulunamadı veya liste boş.")
    else:
        cols = st.columns(3)
        for i, (idx, row) in enumerate(items.iterrows()):
            with cols[i % 3]:
                is_done = row['durum'] == "Alındı"
                overlay = '<div style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:2;pointer-events:none;"><span style="font-size:3rem;">✅</span></div>' if is_done else ""
                img_src = row['img'] if row['img'] else "https://cdn-icons-png.flaticon.com/512/3081/3081840.png"
                
                card_html = f'<div class="grand-card">{overlay}<div class="img-area"><img src="{img_src}"></div><div class="content-area"><div style="opacity:0.7; font-size:0.8rem;">{row["kategori"]}</div><h4 style="margin:5px 0; font-size:1rem;">{row["baslik"]}</h4><div style="font-size:1.2rem; color:#d4af37; font-weight:bold;">{float(row["fiyat"]):,.0f} TL</div></div></div>'
                st.markdown(card_html, unsafe_allow_html=True)
                
                b1, b2 = st.columns(2)
                if b1.button("✅ ALDIK" if not is_done else "İPTAL", key=f"st_{row['id']}", use_container_width=True):
                    df.at[idx, 'durum'] = "Alındı" if not is_done else "Alınacak"
                    save_data(df); st.rerun()
                if b2.button("🗑️ Sil", key=f"dl_{row['id']}", use_container_width=True):
                    st.session_state.last_undo = df.loc[[idx]]
                    df = df.drop(idx); save_data(df); st.rerun()

# === TAB 2: GİDER & KAPORA ===
with tabs[1]:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📌 Gider / Hizmet Ekle")
        with st.form("add_expense"):
            e_ad = st.text_input("Gider Adı")
            e_top = st.number_input("TOPLAM Tutar", min_value=0.0)
            e_kap = st.number_input("ÖDENEN (Kapora)", min_value=0.0)
            e_kat = st.selectbox("Kategori", ["Düğün", "Balayı", "Ev Tadilat", "Diğer"])
            if st.form_submit_button("EKLE"):
                new_row = {
                    "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                    "tur": "Ekstra", "baslik": e_ad, "fiyat": e_top, "odenen": e_kap,
                    "kategori": e_kat, "durum": "Bekliyor", "adet": 1, "url":"", "img":"", "notlar":""
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df); st.rerun()
                
    with c2:
        st.subheader("💸 Ödeme Takibi")
        expenses = filtered_df[filtered_df['tur'] == 'Ekstra']
        for i, r in expenses.iterrows():
            kalan = float(r['fiyat']) - float(r['odenen'])
            pct = float(r['odenen']) / float(r['fiyat']) if float(r['fiyat']) > 0 else 0
            
            exp_html = f'<div class="expense-card"><div style="display:flex; justify-content:space-between; font-weight:bold;"><span>{r["baslik"]}</span><span>{float(r["fiyat"]):,.0f} TL</span></div><div style="margin:5px 0; height:6px; background:#ccc; border-radius:3px;"><div style="width:{min(pct*100, 100)}%; height:100%; background:#d4af37; border-radius:3px;"></div></div><div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:5px;"><span style="color:#4ade80;">Ödenen: {float(r["odenen"]):,.0f} TL</span><span style="color:#f87171;">Kalan: {kalan:,.0f} TL</span></div></div>'
            st.markdown(exp_html, unsafe_allow_html=True)
            
            with st.expander("Düzenle"):
                c_up1, c_up2 = st.columns([3,1])
                new_pay = c_up1.number_input("Ödenen Tutar", value=float(r['odenen']), key=f"np_{r['id']}")
                if c_up1.button("Güncelle", key=f"up_{r['id']}"):
                    df.at[df[df['id']==r['id']].index[0], 'odenen'] = new_pay
                    save_data(df); st.rerun()
                if c_up2.button("Sil", key=f"del_ex_{r['id']}"):
                    df = df[df['id'] != r['id']]; save_data(df); st.rerun()

# === TAB 3: YAPILACAKLAR ===
with tabs[2]:
    st.subheader("📝 To-Do Listesi")
    with st.form("todo_add", clear_on_submit=True):
        c_t1, c_t2 = st.columns([4, 1])
        t_txt = c_t1.text_input("Yapılacak İş")
        if c_t2.form_submit_button("EKLE"):
            new_row = {
                "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                "tur": "ToDo", "baslik": t_txt, "durum": "Yapılacak",
                "fiyat":0, "odenen":0, "adet":1, "url":"", "img":"", "kategori":"", "notlar":""
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df); st.rerun()
            
    todos = filtered_df[filtered_df['tur'] == 'ToDo']
    for i, r in todos.iterrows():
        chk = r['durum'] == "Yapıldı"
        col_check, col_text, col_del = st.columns([1, 10, 1])
        if col_check.checkbox("", value=chk, key=f"chk_{r['id']}"):
            new_status = "Yapılacak" if chk else "Yapıldı"
            if new_status != r['durum']:
                df.at[df[df['id']==r['id']].index[0], 'durum'] = new_status
                save_data(df); st.rerun()
        
        style = "text-decoration:line-through; opacity:0.6;" if chk else ""
        col_text.markdown(f"<span style='{style}'>{r['baslik']}</span>", unsafe_allow_html=True)
        if col_del.button("❌", key=f"del_td_{r['id']}"):
            df = df[df['id'] != r['id']]; save_data(df); st.rerun()

# === TAB 4: DAVET & USTA ===
with tabs[3]:
    c_u1, c_u2 = st.columns(2)
    with c_u1:
        st.subheader("📞 Usta Ekle")
        with st.form("usta_add"):
            nm = st.text_input("Ad / Firma")
            cat = st.selectbox("Hizmet Türü", ["Nakliye", "Mobilya", "Perde", "Beyaz Eşya", "Fotoğraf", "Organizasyon", "Tadilat", "Diğer"])
            tel = st.text_input("Telefon (Başında 0 olmadan)")
            if st.form_submit_button("Kaydet"):
                tel_cleaned = clean_phone(tel)
                new_row = {"id": str(int(time.time())), "tur": "Usta", "baslik": nm, "notlar": tel_cleaned, "fiyat":0, "odenen":0, "adet":1, "url":"", "img":"", "durum":"", "kategori": cat}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True); save_data(df); st.rerun()
                
    with c_u2:
        st.subheader("👥 Davetli Ekle")
        with st.form("guest_add"):
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
            col_info, col_call, col_del = st.columns([3, 2, 1])
            with col_info:
                kategori_str = f"({u['kategori']})" if u['kategori'] else ""
                st.write(f"**{u['baslik']}** {kategori_str}")
            with col_call:
                tel_display = clean_phone(u['notlar'])
                if tel_display:
                    st.markdown(f'<a href="tel:{tel_display}" class="phone-link">📞 {tel_display}</a>', unsafe_allow_html=True)
                else:
                    st.write("-")
            with col_del:
                if st.button("Sil", key=f"del_usta_{u['id']}"):
                    df = df[df['id'] != u['id']]
                    save_data(df)
                    st.rerun()

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
        fig = px.pie(alisveris, values='fiyat', names='kategori', title="Harcamalar", hole=0.4, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# Footer da temaya uyumlu
ft_bg = "#ffffff" if st.session_state.theme == "Light Elegance" else "#1a1a1a"
ft_txt = "#000000" if st.session_state.theme == "Light Elegance" else "#ffffff"

st.markdown(f'<div class="sticky-footer" style="background:{ft_bg}; color:{ft_txt};"><div style="font-weight:bold;">Toplam: {grand_total:,.0f} TL</div><div style="opacity:0.7;">Yuva & Co.</div></div>', unsafe_allow_html=True)
