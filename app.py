import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime, date
import time
import plotly.express as px
import re
import random
import urllib.parse

# --- 1. AYARLAR ---
st.set_page_config(page_title="Yuva & Co.", page_icon="💍", layout="wide")

# --- 2. TEMA VE CSS ---
if "theme" not in st.session_state:
    st.session_state.theme = "Dark Luxury"

# CSS (GÖRÜNTÜ MOTORU)
common_css = """
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@200;300;400;500;600&display=swap');
    body { font-family: 'Montserrat', sans-serif; }
    h1, h2, h3, h4 { font-family: 'Playfair Display', serif !important; }
    
    /* ÜRÜN KARTI */
    .grand-card {
        border-radius: 12px; overflow: hidden; margin-bottom: 20px; 
        position: relative; height: 100%; display: flex; flex-direction: column;
    }
    .grand-card:hover { transform: translateY(-5px); transition: transform 0.3s ease; }
    
    /* RESİM ALANI */
    .img-area {
        width: 100%; height: 300px; background-color: #fff;
        display: flex; align-items: center; justify-content: center;
        position: relative; border-bottom: 1px solid rgba(255,255,255,0.1);
        overflow: hidden;
    }
    .img-area img { width: 100%; height: 100%; object-fit: cover; object-position: center; }
    
    /* İÇERİK ALANI */
    .content-area { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
    
    .card-title {
        font-family: 'Playfair Display', serif; font-size: 1.1rem; line-height: 1.3;
        height: 2.8em; overflow: hidden; display: -webkit-box;
        -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 5px;
    }
    
    /* BADGE & ROZETLER */
    .badge-corner {
        position: absolute; top: 10px; left: 10px; padding: 4px 10px; border-radius: 6px; 
        font-size: 0.7rem; font-weight: bold; text-transform: uppercase;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3); z-index: 5;
    }
    .badge-qty {
        position: absolute; bottom: 10px; right: 10px; width: 40px; height: 40px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3); z-index: 10; border: 2px solid white;
    }
    .overlay-bought {
        position: absolute; top:0; left:0; width:100%; height:100%;
        background: rgba(0,0,0,0.7); z-index: 20;
        display: flex; align-items: center; justify-content: center;
        pointer-events: none;
    }
    
    /* HİZMET/GİDER KARTI */
    .expense-card {
        padding: 15px; border-radius: 12px; margin-bottom: 15px;
        border-left: 5px solid #d4af37;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .exp-header { display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1rem; margin-bottom: 5px; }
    .exp-detail { display: flex; justify-content: space-between; font-size: 0.9rem; }
"""

css_dark = f"""<style>{common_css}
    .stApp {{ background-color: #050505; background-image: radial-gradient(circle at 50% 0%, #1a1a1a 0%, #050505 80%); color: #e0e0e0; }}
    .grand-card {{ background: #1a1a1a; border: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
    .grand-card:hover {{ border-color: #d4af37; box-shadow: 0 10px 30px rgba(212, 175, 55, 0.15); }}
    h1, h2, h3, h4, .big-font {{ color: #d4af37 !important; text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.2); }}
    .expense-card {{ background: rgba(255,255,255,0.05); }}
    .badge-qty {{ background: #d4af37; color: #000; }}
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {{ background-color: #1a1a1a !important; color: #d4af37 !important; border: 1px solid #444 !important; }}
    .stButton>button {{ background-color: #222; color: #ccc; border: 1px solid #444; }}
    .stButton>button:hover {{ border-color: #d4af37; color: #d4af37; }}
</style>"""

css_light = f"""<style>{common_css}
    .stApp {{ background-color: #f8f9fa; color: #2c3e50; }}
    .grand-card {{ background: #fff; border: 1px solid #e0e0e0; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
    .grand-card:hover {{ border-color: #2c3e50; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
    h1, h2, h3, h4, .big-font {{ color: #2c3e50 !important; }}
    .expense-card {{ background: #fff; border: 1px solid #eee; border-left: 5px solid #2c3e50; }}
    .badge-qty {{ background: #2c3e50; color: #fff; }}
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {{ background-color: #fff !important; color: #2c3e50 !important; border: 1px solid #ccc !important; }}
    .stButton>button {{ background-color: #fff; color: #555; border: 1px solid #ccc; }}
    .stButton>button:hover {{ border-color: #2c3e50; color: #2c3e50; }}
</style>"""

if st.session_state.theme == "Dark Luxury": st.markdown(css_dark, unsafe_allow_html=True)
else: st.markdown(css_light, unsafe_allow_html=True)

# --- 3. FONKSİYONLAR ---
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

@st.cache_data(ttl=600)
def scrape_product_info(url):
    fallback_img = "https://cdn-icons-png.flaticon.com/512/3081/3081840.png"
    if not url or len(url) < 5: return "Yeni Ürün", fallback_img, 0
    try:
        encoded_url = urllib.parse.quote(url)
        api_url = f"https://api.microlink.io?url={encoded_url}&screenshot=false&meta=true"
        response = requests.get(api_url, timeout=10)
        data = response.json()
        if data.get('status') == 'success':
            info = data.get('data', {})
            title = info.get('title', 'Yeni Ürün')
            image = info.get('image', {}).get('url', fallback_img)
            if "Service Unavailable" in title or "Access Denied" in title: title = "Yeni Ürün (İsim Düzenle)"
            if not image: image = fallback_img
            return title, image, 0 
    except: pass
    return "Yeni Ürün (İsim Düzenle)", fallback_img, 0

# --- 4. GİRİŞ ---
if "user_name" not in st.session_state: st.session_state.user_name = None
if not st.session_state.user_name:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><h1 style='text-align:center;'>Yuva & Co.</h1>", unsafe_allow_html=True)
        pwd = st.text_input("Giriş Şifresi", type="password")
        if st.button("GİRİŞ", use_container_width=True):
            if pwd == "2024": st.session_state.auth = True
            else: st.error("Hatalı")
        if getattr(st.session_state, 'auth', False):
            col_k, col_b = st.columns(2)
            if col_k.button("KEREM"): st.session_state.user_name = "Kerem"; st.rerun()
            if col_b.button("BÜŞRA"): st.session_state.user_name = "Büşra"; st.rerun()
    st.stop()

# --- 5. DATA ---
try: 
    df = get_data()
    cols = ['id', 'tarih', 'ekleyen', 'tur', 'kategori', 'baslik', 'fiyat', 'ilk_fiyat', 'url', 'img', 'oncelik', 'notlar', 'durum', 'adet', 'odenen']
    for c in cols:
        if c not in df.columns: df[c] = ""
    if 'id' in df.columns: df['id'] = df['id'].astype(str)
    
    # Sayısal Dönüşümler
    df['fiyat'] = pd.to_numeric(df['fiyat'], errors='coerce').fillna(0)
    df['adet'] = pd.to_numeric(df['adet'], errors='coerce').fillna(1).astype(int)
    df['odenen'] = pd.to_numeric(df['odenen'], errors='coerce').fillna(0)
    
except: 
    df = pd.DataFrame(columns=cols)

# --- 6. MENÜ ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_name}")
    st.divider()
    mode = st.radio("Tema", ["Dark Luxury", "Light Elegance"], index=0 if st.session_state.theme=="Dark Luxury" else 1)
    if mode != st.session_state.theme: st.session_state.theme = mode; st.rerun()
    st.divider()
    if st.button("🔄 Yenile"): st.cache_data.clear(); st.rerun()

# --- 7. ANA EKRAN ---
TARGET_DATE = date(2026, 4, 25)
days_left = (TARGET_DATE - date.today()).days
c_head1, c_head2 = st.columns([3, 1])
with c_head1: st.markdown(f"<h1>Merhaba, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
with c_head2: 
    color = "#d4af37" if st.session_state.theme == "Dark Luxury" else "#2c3e50"
    st.markdown(f"<div style='text-align:right; border-left:4px solid {color}; padding-left:15px;'><span style='font-size:2rem; font-weight:bold; color:{color};'>{days_left}</span> <span style='font-size:1rem;'>GÜN</span></div>", unsafe_allow_html=True)

st.write("") 
tabs = st.tabs(["🛍️ KOLEKSİYON", "📋 PLANLAYICI & GİDER", "📊 ANALİZ", "🤖 AI ASİSTAN"])

# --- TAB 1: KOLEKSİYON ---
with tabs[0]:
    # FİLTRE VE SIRALAMA PANOSU
    with st.container():
        c_filt1, c_filt2 = st.columns(2)
        filter_status = c_filt1.selectbox("Durum Filtrele", ["Tümü", "Alınacaklar", "Alınanlar"])
        sort_opt = c_filt2.selectbox("Sıralama", ["En Yeni", "En Eski", "En Pahalı", "En Ucuz"])
        st.write("")

    # EKLEME MODÜLÜ
    with st.expander("➕ HIZLI EKLE", expanded=False):
        with st.form("add_item"):
            c1, c2 = st.columns([1, 1])
            url = c1.text_input("Ürün Linki")
            img_manual = c2.text_input("Resim Linki (Opsiyonel - Sağ Tıkla Kopyala)")
            c3, c4, c5, c6 = st.columns([2, 1, 1, 2])
            cat = c3.selectbox("Kategori", ["Otomatik Algıla", "Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Diğer"])
            manual_price = c4.number_input("Birim Fiyat", min_value=0.0, value=None, placeholder="0.00")
            qty = c5.number_input("Adet", min_value=1, value=1)
            pri = c6.selectbox("Öncelik", ["Yüksek", "Orta", "Düşük"])
            if st.form_submit_button("KAYDET", use_container_width=True):
                with st.spinner("Kaydediliyor..."):
                    title, img, s_price = scrape_product_info(url)
                    if img_manual: img = img_manual
                    base_price = s_price if s_price > 0 else (manual_price if manual_price else 0.0)
                    final_total_price = base_price * qty
                    final_cat = cat
                    if cat == "Otomatik Algıla": final_cat = detect_category_from_title(title)
                    new_row = pd.DataFrame([{
                        "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                        "ekleyen": st.session_state.user_name, "tur": "Alisveris",
                        "kategori": final_cat, "baslik": title, 
                        "fiyat": final_total_price, "ilk_fiyat": final_total_price,
                        "url": url, "img": img, "oncelik": pri, "notlar": "", "durum": "Alınacak", "adet": qty, "odenen": 0
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    update_all_data(df)
                    st.success("Eklendi!"); time.sleep(1); st.rerun()

    # LİSTELEME MANTIĞI
    all_cats = [c for c in df['kategori'].unique() if c]
    filter_cat = st.multiselect("Kategori Filtrele:", all_cats, default=all_cats)
    
    # Ana Filtre
    view_df = df[(df['kategori'].isin(filter_cat)) & (df['tur'] == 'Alisveris')]
    
    # Durum Filtresi
    if filter_status == "Alınacaklar": view_df = view_df[view_df['durum'] != 'Alındı']
    elif filter_status == "Alınanlar": view_df = view_df[view_df['durum'] == 'Alındı']
    
    # Sıralama
    if sort_opt == "En Yeni": view_df = view_df.sort_values('id', ascending=False)
    elif sort_opt == "En Eski": view_df = view_df.sort_values('id', ascending=True)
    elif sort_opt == "En Pahalı": view_df = view_df.sort_values('fiyat', ascending=False)
    elif sort_opt == "En Ucuz": view_df = view_df.sort_values('fiyat', ascending=True)
    
    if not view_df.empty:
        cols = st.columns(2) 
        for i, (idx, row) in enumerate(view_df.iterrows()):
            with cols[i % 2]:
                is_done = row['durum'] == "Alındı"
                card_id = row['id']
                overlay_html = f'<div class="overlay-bought"><span style="color:#2ecc71; font-size:2rem; font-weight:bold; border:3px solid #2ecc71; padding:10px 20px; border-radius:10px; background:rgba(0,0,0,0.8);">✅ ALINDI</span></div>' if is_done else ""
                curr = float(row['fiyat'])
                piece_count = int(row['adet']) if row['adet'] else 1
                qty_badge_html = f'<div class="badge-qty">x{piece_count}</div>' if piece_count > 1 else ""
                img_src = row['img'] if row['img'] and len(str(row['img'])) > 5 else "https://placehold.co/400x300/1a1a1a/d4af37?text=Resim+Yok"
                
                card_html = f"""<div class="grand-card">{overlay_html}<div class="img-area"><img src="{img_src}" onerror="this.onerror=null;this.src='https://placehold.co/400x300/111/444?text=Hata';"><div class="badge-corner" style="background:#000; color:#fff;">{row['ekleyen']}</div>{qty_badge_html}</div><div class="content-area"><div style="display:flex; justify-content:space-between; color:#888; font-size:0.8rem; margin-bottom:5px;"><span>{str(row['kategori']).upper()}</span><span>{row['oncelik']}</span></div><div class="card-title">{row['baslik']}</div><div style="margin-top:15px; font-size:1.4rem; font-weight:bold;">{curr:,.0f} TL</div></div></div>"""
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Sağ Üst Silme (Dışarıda)
                b_col1, b_col2 = st.columns([6, 1])
                with b_col2:
                     if st.button("❌", key=f"del_top_{card_id}", help="Sil"): delete_data(card_id); st.rerun()

                with st.expander("✏️ Düzenle / Link"):
                     with st.form(f"edit_{card_id}"):
                         e_title = st.text_input("Ürün Adı", value=row['baslik'])
                         e_url = st.text_input("Link", value=row['url'])
                         e_img = st.text_input("Resim", value=row['img'])
                         e_prc = st.number_input("Fiyat", value=float(row['fiyat']))
                         e_qty = st.number_input("Adet", value=int(row['adet']))
                         if st.form_submit_button("GÜNCELLE"):
                             idx_orig = df[df['id'] == card_id].index[0]
                             df.at[idx_orig, 'baslik'] = e_title
                             df.at[idx_orig, 'url'] = e_url
                             df.at[idx_orig, 'img'] = e_img
                             df.at[idx_orig, 'fiyat'] = e_prc * e_qty
                             df.at[idx_orig, 'adet'] = e_qty
                             update_all_data(df); st.rerun()

                c1, c2 = st.columns([2, 2])
                with c1:
                    if not is_done:
                        if st.button("✅ ALDIK", key=f"buy_{card_id}", use_container_width=True):
                            df.at[df[df['id'] == card_id].index[0], 'durum'] = "Alındı"; update_all_data(df); st.rerun()
                    else:
                        if st.button("↩️ İPTAL", key=f"ret_{card_id}", use_container_width=True):
                            df.at[df[df['id'] == card_id].index[0], 'durum'] = "Alınacak"; update_all_data(df); st.rerun()
                with c2: 
                    if row['url'] and len(str(row['url'])) > 5: st.link_button("🔗 GİT", row['url'], use_container_width=True)
                st.write("")

# --- TAB 2: PLANLAYICI (GELİŞMİŞ KAPORA SİSTEMİ) ---
with tabs[1]:
    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        st.subheader("💸 Ekstra Giderler (Hizmet vb.)")
        with st.form("add_expense", clear_on_submit=True):
            e1, e2 = st.columns([2, 1])
            nm = e1.text_input("Gider Adı (Düğün Salonu vb.)")
            pr = e2.number_input("TOPLAM Tutar (TL)", min_value=0.0, value=None, placeholder="0.00")
            paid = st.number_input("ÖDENEN Kapora", min_value=0.0, value=None, placeholder="0.00")
            cat = st.selectbox("Kategori", ["Düğün", "Balayı", "Diğer"])
            
            if st.form_submit_button("GİDER EKLE", use_container_width=True):
                pr_val = pr if pr else 0.0
                pd_val = paid if paid else 0.0
                new_row = pd.DataFrame([{
                    "id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"),
                    "ekleyen": st.session_state.user_name, "tur": "Ekstra", 
                    "baslik": nm, "fiyat": pr_val, "odenen": pd_val,
                    "kategori": cat, "ilk_fiyat": pr_val, "url":"", "img":"", "oncelik":"", "notlar":"", "durum":"", "adet": 1
                }])
                df = pd.concat([df, new_row], ignore_index=True); update_all_data(df); st.rerun()
        
        exps = df[df['tur'] == 'Ekstra']
        if not exps.empty:
            for i, r in exps.iterrows():
                total = float(r['fiyat'])
                paid = float(r['odenen'])
                remain = total - paid
                
                st.markdown(f"""
                <div class="expense-card">
                    <div class="exp-header">
                        <span>{r['baslik']}</span>
                        <span>{total:,.0f} TL</span>
                    </div>
                    <div class="exp-detail">
                        <span style="color:#4ade80;">✅ Ödenen: {paid:,.0f} TL</span>
                        <span style="color:#f87171; font-weight:bold;">⏳ Kalan: {remain:,.0f} TL</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("💰 Ödeme Düzenle"):
                    with st.form(f"pay_{r['id']}"):
                        new_paid = st.number_input("Toplam Ödenen Tutar", value=paid)
                        if st.form_submit_button("GÜNCELLE"):
                            df.at[df[df['id'] == r['id']].index[0], 'odenen'] = new_paid
                            update_all_data(df); st.rerun()
                
                if st.button("Sil", key=f"del_ex_{r['id']}"): delete_data(r['id']); st.rerun()

    with col_p2:
        st.subheader("📝 Yapılacaklar")
        with st.form("new_todo", clear_on_submit=True):
            t1, t2 = st.columns([3, 1])
            tsk = t1.text_input("Görev"); 
            if t2.form_submit_button("EKLE"):
                new_row = pd.DataFrame([{"id": str(int(time.time())), "tarih": datetime.now().strftime("%d.%m.%Y"), "ekleyen": st.session_state.user_name, "tur": "ToDo", "baslik": tsk, "durum": "Yapılacak", "kategori":"", "fiyat":0, "ilk_fiyat":0, "url":"", "img":"", "oncelik":"", "notlar":"", "adet": 1, "odenen":0}])
                df = pd.concat([df, new_row], ignore_index=True); update_all_data(df); st.rerun()
        todos = df[df['tur'] == 'ToDo']
        for i, r in todos.iterrows():
            chk = r['durum'] == "Yapıldı"
            st.markdown(f"<div style='padding:10px; border-bottom:1px solid #333; text-decoration:{'line-through' if chk else 'none'}'>{r['baslik']}</div>", unsafe_allow_html=True)
            b1, b2 = st.columns([1, 4])
            with b1: 
                if st.button("✅", key=f"d_{r['id']}"): df.at[df[df['id'] == r['id']].index[0], 'durum'] = "Yapılacak" if chk else "Yapıldı"; update_all_data(df); st.rerun()
            with b2: 
                if st.button("🗑️", key=f"dd_{r['id']}"): delete_data(r['id']); st.rerun()

# --- TAB 3: ANALİZ ---
with tabs[2]:
    c1, c2, c3 = st.columns(3)
    
    items_total = df[df['tur'] == 'Alisveris']['fiyat'].sum()
    items_bought = df[(df['tur'] == 'Alisveris') & (df['durum'] == 'Alındı')]['fiyat'].sum()
    
    extra_df = df[df['tur'] == 'Ekstra']
    extra_total = extra_df['fiyat'].sum()
    extra_paid = extra_df['odenen'].sum()
    extra_remain = extra_total - extra_paid
    
    grand_total_planned = items_total + extra_total
    grand_total_paid = items_bought + extra_paid 
    grand_total_debt = (items_total - items_bought) + extra_remain 
    
    c1.metric("GENEL TOPLAM (Planlanan)", f"{grand_total_planned:,.0f} TL")
    c2.metric("CEBİMİZDEN ÇIKAN (Ödenen)", f"{grand_total_paid:,.0f} TL")
    c3.metric("KALAN İHTİYAÇ / BORÇ", f"{grand_total_debt:,.0f} TL")
    
    st.divider()
    if not df[df['tur']=='Alisveris'].empty:
        st.plotly_chart(px.pie(df[df['tur']=='Alisveris'], values='fiyat', names='kategori', title="Eşya Harcamaları Dağılımı", hole=0.5), use_container_width=True)

# --- TAB 4: AI ---
with tabs[3]:
    st.subheader("🤖 AI Asistan")
    if st.button("🔍 Evi Analiz Et"):
        st.info("Analiz: Mutfak kategorisi eksik görünüyor. Airfryer ve Kahve makinesi eklediniz mi?")
    if st.button("✨ Fikir Ver"):
        st.success(f"Öneri: {random.choice(['Dyson Süpürge', 'Smeg Kettle', 'Robot Süpürge'])}")
