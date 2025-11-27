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
TARGET_DATE = date(2025, 4, 25) # Düğün Tarihi
BG_DARK = "#0e0e0e"

# --- 2. CSS & GÖRSEL MOTORU ---
def load_css():
    common_css = """
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Montserrat:wght@300;400;500;600&display=swap');
        body { font-family: 'Montserrat', sans-serif; }
        h1, h2, h3, h4 { font-family: 'Playfair Display', serif !important; }
        
        .grand-card {
            border-radius: 12px; overflow: hidden; margin-bottom: 20px; 
            position: relative; height: 100%; display: flex; flex-direction: column;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            background: #1a1a1a; border: 1px solid #333;
        }
        .grand-card:hover { transform: translateY(-5px); border-color: #d4af37; box-shadow: 0 10px 30px rgba(212, 175, 55, 0.15); }
        
        .img-area { width: 100%; height: 200px; background:#222; overflow:hidden; position: relative; }
        .img-area img { width: 100%; height: 100%; object-fit: cover; }
        
        .content-area { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
        
        /* GİDER KARTI */
        .expense-card {
            padding: 15px; border-radius: 12px; margin-bottom: 15px;
            border-left: 5px solid #d4af37; background: rgba(255,255,255,0.05);
        }
        .sticky-footer {
            position: fixed; bottom: 0; left: 0; width: 100%; z-index: 999;
            background: rgba(15, 15, 15, 0.95); border-top: 1px solid #333;
            padding: 10px 20px; display: flex; justify-content: space-between; align-items: center;
            backdrop-filter: blur(10px);
        }
        /* TELEFON LİNKİ */
        a.phone-link { color: #4ade80 !important; text-decoration: none; font-weight: bold; }
        a.phone-link:hover { text-decoration: underline; }
    """
    st.markdown(f"<style>{common_css}.stApp {{ background-color: {BG_DARK}; color: #e0e0e0; }}</style>", unsafe_allow_html=True)

# --- 3. VERİ YÖNETİMİ ---
def get_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        # Orijinal sütun isimlerini koruyoruz
        cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum', 'adet', 'odenen']
        for c in cols:
            if c not in df.columns: df[c] = ""
        
        df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
        df['odenen'] = pd.to_numeric(df['odenen'], errors='coerce').fillna(0)
        df['adet'] = pd.to_numeric(df['adet'], errors='coerce').fillna(1)
        return df
    except:
        return pd.DataFrame(columns=['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum', 'adet', 'odenen'])

def save_data(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Sayfa1", data=df)
        st.cache_data.clear()
    except:
        pass

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

# --- 4. BAŞLANGIÇ ---
load_css()
df = get_data()
if "last_undo" not in st.session_state: st.session_state.last_undo = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### 💍 Yuva & Co.")
    days = (TARGET_DATE - date.today()).days
    st.metric("Büyük Gün", f"{days} Gün Kaldı")
    st.divider()
    
    st.subheader("💰 Maaş Sayacı")
    salary = st.number_input("Aylık Ortak Gelir", value=0, step=1000)
    if salary > 0:
        months_left = days // 30
        st.caption(f"Düğüne kadar ~{months_left * salary:,.0f} TL potansiyel gelir.")

    st.divider()
    if st.button("♻️ Geri Al (Undo)", disabled=st.session_state.last_undo is None):
        if st.session_state.last_undo is not None:
            df = pd.concat([df, st.session_state.last_undo], ignore_index=True)
            save_data(df); st.session_state.last_undo = None; st.rerun()

    if st.button("📥 Excel Yedek Al"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("İndir", output.getvalue(), f"Yuva_Yedek.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Üst Arama
c_hero1, c_hero2 = st.columns([3,1])
with c_hero1:
    st.markdown(f"<h2>Hoş Geldiniz.</h2>", unsafe_allow_html=True)
    search = st.text_input("🔍 Evin içinde ara...", placeholder="Ürün, Gider veya Not ara...")

mask = df.apply(lambda x: search.lower() in str(x).lower(), axis=1) if search else [True] * len(df)
filtered_df = df[mask]

# --- 6. SEKMELER ---
tabs = st.tabs(["🛍️ KOLEKSİYON", "💸 GİDER & KAPORA", "📝 YAPILACAKLAR", "👥 DAVET & USTA", "📊 ANALİZ"])

# === TAB 1: KOLEKSİYON ===
with tabs[0]:
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
    cols = st.columns(3)
    for i, (idx, row) in enumerate(items.iterrows()):
        with cols[i % 3]:
            is_done = row['durum'] == "Alındı"
            overlay = '<div style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:2;pointer-events:none;"><span style="font-size:3rem;">✅</span></div>' if is_done else ""
            img_src = row['img'] if row['img'] else "https://cdn-icons-png.flaticon.com/512/3081/3081840.png"
            
            # Kart HTML (Tek Satır)
            card_html = f'<div class="grand-card">{overlay}<div class="img-area"><img src="{img_src}"></div><div class="content-area"><div style="color:#888; font-size:0.8rem;">{row["kategori"]}</div><h4 style="margin:5px 0; font-size:1rem;">{row["baslik"]}</h4><div style="font-size:1.2rem; color:#d4af37; font-weight:bold;">{float(row["fiyat"]):,.0f} TL</div></div></div>'
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
            
            # Gider HTML (Tek Satır)
            exp_html = f'<div class="expense-card"><div style="display:flex; justify-content:space-between; font-weight:bold;"><span>{r["baslik"]}</span><span>{float(r["fiyat"]):,.0f} TL</span></div><div style="margin:5px 0; height:6px; background:#333; border-radius:3px;"><div style="width:{min(pct*100, 100)}%; height:100%; background:#d4af37; border-radius:3px;"></div></div><div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:5px;"><span style="color:#4ade80;">Ödenen: {float(r["odenen"]):,.0f} TL</span><span style="color:#f87171;">Kalan: {kalan:,.0f} TL</span></div></div>'
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
        
        style = "text-decoration:line-through; color:#666;" if chk else ""
        col_text.markdown(f"<span style='{style}'>{r['baslik']}</span>", unsafe_allow_html=True)
        if col_del.button("❌", key=f"del_td_{r['id']}"):
            df = df[df['id'] != r['id']]; save_data(df); st.rerun()

# === TAB 4: DAVET & USTA (GÜNCELLENDİ) ===
with tabs[3]:
    c_u1, c_u2 = st.columns(2)
    with c_u1:
        st.subheader("📞 Usta Ekle")
        with st.form("usta_add"):
            nm = st.text_input("Ad / Firma")
            # YENİ: Kategori Seçimi
            cat = st.selectbox("Hizmet Türü", ["Nakliye", "Mobilya", "Perde", "Beyaz Eşya", "Fotoğraf", "Organizasyon", "Tadilat", "Diğer"])
            tel = st.text_input("Telefon (Başında 0 olmadan)")
            if st.form_submit_button("Kaydet"):
                # Kategori bilgisini de kaydediyoruz
                new_row = {"id": str(int(time.time())), "tur": "Usta", "baslik": nm, "notlar": tel, "fiyat":0, "odenen":0, "adet":1, "url":"", "img":"", "durum":"", "kategori": cat}
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
                # Kategori varsa parantez içinde göster
                kategori_str = f"({u['kategori']})" if u['kategori'] else ""
                st.write(f"**{u['baslik']}** {kategori_str}")
            with col_call:
                # YENİ: Tıkla Ara Özelliği
                tel_clean = ''.join(filter(str.isdigit, str(u['notlar'])))
                if tel_clean:
                    st.markdown(f'<a href="tel:{tel_clean}" class="phone-link">📞 {u["notlar"]}</a>', unsafe_allow_html=True)
                else:
                    st.write(u['notlar'])
            with col_del:
                # YENİ: Silme Butonu
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

st.markdown(f'<div class="sticky-footer"><div style="color:#fff;"><b>Toplam:</b> {grand_total:,.0f} TL</div><div style="color:#aaa;">Yuva & Co.</div></div>', unsafe_allow_html=True)
