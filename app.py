import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import time
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import random
import urllib.parse
from io import BytesIO

# --- 1. AYARLAR & YAPILANDIRMA ---
st.set_page_config(page_title="Yuva & Co. | Ultimate Planner", page_icon="💍", layout="wide")

# Sabitler
TARGET_DATE = date(2025, 4, 25) # Düğün Tarihi
THEME_COLOR = "#d4af37" # Gold
BG_DARK = "#0e0e0e"

# --- 2. CSS & GÖRSEL MOTORU ---
def load_css(theme):
    common_css = """
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Montserrat:wght@300;400;500;600&display=swap');
        body { font-family: 'Montserrat', sans-serif; }
        h1, h2, h3, h4 { font-family: 'Playfair Display', serif !important; }
        
        /* ÖZEL BİLEŞENLER */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { border-radius: 4px; padding: 10px 20px; }
        
        /* KART STİLLERİ */
        .grand-card {
            border-radius: 12px; overflow: hidden; margin-bottom: 20px; 
            position: relative; height: 100%; display: flex; flex-direction: column;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .grand-card:hover { transform: translateY(-5px); }
        .img-area { width: 100%; height: 220px; position: relative; overflow: hidden; background:#222; }
        .img-area img { width: 100%; height: 100%; object-fit: cover; }
        .content-area { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
        
        /* CHIP FİLTRELER */
        .chip-container { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px; }
        .chip { 
            padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 0.9rem; 
            border: 1px solid rgba(255,255,255,0.2); transition: all 0.2s;
        }
        .chip:hover { background: rgba(212, 175, 55, 0.2); border-color: #d4af37; }
        .chip.active { background: #d4af37; color: #000; font-weight: bold; border-color: #d4af37; }

        /* STICKY FOOTER */
        .sticky-footer {
            position: fixed; bottom: 0; left: 0; width: 100%; z-index: 999;
            background: rgba(15, 15, 15, 0.95); border-top: 1px solid #333;
            padding: 10px 20px; display: flex; justify-content: space-between; align-items: center;
            backdrop-filter: blur(10px); box-shadow: 0 -5px 20px rgba(0,0,0,0.5);
        }
        
        /* PROGRESS BAR */
        .prog-bg { width:100%; height:6px; background:#333; border-radius:3px; margin-top:5px; }
        .prog-fill { height:100%; background: linear-gradient(90deg, #d4af37, #f1c40f); border-radius:3px; }
    """
    
    dark_css = f"""<style>{common_css}
        .stApp {{ background-color: {BG_DARK}; color: #e0e0e0; }}
        .grand-card {{ background: #1a1a1a; border: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
        .grand-card:hover {{ border-color: {THEME_COLOR}; box-shadow: 0 10px 30px rgba(212, 175, 55, 0.15); }}
        h1, h2, h3, .highlight {{ color: {THEME_COLOR} !important; }}
        .stTextInput>div>div>input {{ background-color: #1a1a1a !important; color: #fff !important; border-color: #444; }}
    </style>"""
    
    st.markdown(dark_css, unsafe_allow_html=True)

# --- 3. VERİ YÖNETİMİ ---
def get_data():
    # Şema: id, type, category, title, price, paid, status, url, img, quantity, notes, extra_data (json/dict str)
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        # Eksik kolonları tamamla
        required_cols = ['id', 'type', 'category', 'title', 'price', 'paid', 'status', 'url', 'img', 'quantity', 'notes', 'extra_data']
        for c in required_cols:
            if c not in df.columns: df[c] = ""
        return df
    except:
        # Bağlantı yoksa session state kullan (Local Mode)
        if 'local_df' not in st.session_state:
            st.session_state.local_df = pd.DataFrame(columns=['id', 'type', 'category', 'title', 'price', 'paid', 'status', 'url', 'img', 'quantity', 'notes', 'extra_data'])
        return st.session_state.local_df

def save_data(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Sayfa1", data=df)
        st.cache_data.clear()
    except:
        st.session_state.local_df = df

def scrape_metadata(url):
    fallback = "https://cdn-icons-png.flaticon.com/512/3081/3081840.png"
    if not url or len(url) < 5: return "Yeni Ürün", fallback, 0
    try:
        encoded = urllib.parse.quote(url)
        resp = requests.get(f"https://api.microlink.io?url={encoded}&meta=true", timeout=5)
        data = resp.json()
        if data['status'] == 'success':
            d = data['data']
            return d.get('title', 'Ürün'), d.get('image', {}).get('url', fallback), 0
    except: pass
    return "Manuel Giriş", fallback, 0

# --- 4. SESSION STATE BAŞLATMA ---
if "theme" not in st.session_state: st.session_state.theme = "Dark Luxury"
if "view_mode" not in st.session_state: st.session_state.view_mode = "Kart"
if "scratchpad" not in st.session_state: st.session_state.scratchpad = ""
if "last_undo" not in st.session_state: st.session_state.last_undo = None
load_css(st.session_state.theme)
df = get_data()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### 💍 Yuva & Co.")
    st.caption("Kerem & Büşra | Yönetici Paneli")
    
    st.markdown("---")
    
    # Kalan Gün
    days = (TARGET_DATE - date.today()).days
    st.metric("Büyük Güne Kalan", f"{days} Gün")
    
    st.markdown("---")
    
    # Maaş Sayacı
    st.subheader("💰 Maaş Sayacı")
    salary = st.number_input("Ortak Aylık Gelir", value=0, step=1000)
    if salary > 0:
        months_left = days // 30
        potential = months_left * salary
        st.caption(f"Düğüne kadar tahmini **{potential:,.0f} TL** daha kazanacaksınız.")
        
    st.markdown("---")
    
    # Scratchpad
    st.subheader("📝 Karalama Defteri")
    st.session_state.scratchpad = st.text_area("Hızlı Notlar", value=st.session_state.scratchpad, height=150, placeholder="Aklına geleni yaz...")
    
    if st.button("♻️ Geri Al (Undo)", disabled=st.session_state.last_undo is None):
        if st.session_state.last_undo is not None:
            df = pd.concat([df, st.session_state.last_undo], ignore_index=True)
            save_data(df)
            st.session_state.last_undo = None
            st.rerun()

# --- 6. HERO & SEARCH ---
c_hero1, c_hero2 = st.columns([3, 1])
hour = datetime.now().hour
greeting = "Günaydın" if hour < 12 else "İyi Akşamlar" if hour > 17 else "Merhaba"

with c_hero1:
    st.markdown(f"<h1 style='font-size:2.5rem;'>{greeting}, Yuva Kurucuları.</h1>", unsafe_allow_html=True)
    search_query = st.text_input("🔍 Evin içinde ara...", placeholder="Airfryer, Davetiye, Fotoğrafçı...")

with c_hero2:
    if st.button("☁️ Yedekle (Excel)"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        st.download_button("İNDİR", output.getvalue(), f"Yuva_Yedek_{date.today()}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# FİLTRELEME MANTIĞI
mask = df.apply(lambda x: search_query.lower() in str(x).lower(), axis=1) if search_query else [True] * len(df)
filtered_df = df[mask]

# --- 7. SEKME YAPISI ---
tabs = st.tabs(["🛍️ KOLEKSİYON", "📋 PLAN & BÜTÇE", "👥 DAVET & MASA", "🛠️ USTA & LOJİSTİK", "⚡ BÜYÜK GÜN", "📊 ANALİZ"])

# === TAB 1: KOLEKSİYON (ALIŞVERİŞ) ===
with tabs[0]:
    # Üst Bar: Filtreler ve Görünüm
    c_f1, c_f2, c_f3 = st.columns([4, 1, 1])
    with c_f1:
        categories = ["Tümü", "Salon", "Mutfak", "Yatak Odası", "Elektronik", "Banyo", "Dekorasyon"]
        selected_cat = st.selectbox("Kategori", categories, label_visibility="collapsed")
    with c_f2:
        view = st.selectbox("Görünüm", ["Kart", "Liste", "Galeri (Mood)"], label_visibility="collapsed")
    with c_f3:
        with st.popover("➕ Ürün Ekle"):
            with st.form("add_product"):
                u_url = st.text_input("Link (Otomatik Doldurur)")
                u_cat = st.selectbox("Kategori", categories[1:])
                u_price = st.number_input("Fiyat", min_value=0.0)
                u_qty = st.number_input("Adet", min_value=1, value=1)
                u_tag = st.text_input("Etiketler (Örn: #IKEA #Çeyiz)")
                if st.form_submit_button("KAYDET"):
                    tit, img, _ = scrape_metadata(u_url)
                    new_row = {
                        "id": str(int(time.time())), "type": "item", "category": u_cat,
                        "title": tit, "price": u_price * u_qty, "paid": 0, "status": "Alınacak",
                        "url": u_url, "img": img, "quantity": u_qty, "notes": u_tag, "extra_data": ""
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df); st.rerun()

    # Liste Oluşturma
    shop_df = filtered_df[filtered_df['type'] == 'item']
    if selected_cat != "Tümü": shop_df = shop_df[shop_df['category'] == selected_cat]
    
    if view == "Kart":
        cols = st.columns(3)
        for i, (idx, row) in enumerate(shop_df.iterrows()):
            with cols[i % 3]:
                is_bought = row['status'] == "Alındı"
                overlay = '<div style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:2;pointer-events:none;"><span style="font-size:3rem;">✅</span></div>' if is_bought else ""
                
                st.markdown(f"""
                <div class="grand-card">
                    {overlay}
                    <div class="img-area"><img src="{row['img']}"></div>
                    <div class="content-area">
                        <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#888;">
                            <span>{row['category']}</span><span>{row['notes']}</span>
                        </div>
                        <h4 style="margin:5px 0;">{row['title']}</h4>
                        <div style="font-size:1.2rem; font-weight:bold; color:#d4af37;">{float(row['price']):,.0f} TL</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2, b3 = st.columns([2, 1, 1])
                if not is_bought:
                    if b1.button("ALDIK", key=f"buy_{row['id']}", use_container_width=True):
                        st.balloons()
                        df.at[idx, 'status'] = "Alındı"
                        save_data(df); st.rerun()
                else:
                    if b1.button("İPTAL", key=f"ret_{row['id']}", use_container_width=True):
                        df.at[idx, 'status'] = "Alınacak"
                        save_data(df); st.rerun()
                
                if b2.button("✏️", key=f"ed_{row['id']}"):
                    st.toast("Düzenleme şimdilik listeden yapılıyor.")
                if b3.button("🗑️", key=f"del_{row['id']}"):
                    st.session_state.last_undo = df.loc[[idx]]
                    df = df.drop(idx)
                    save_data(df); st.rerun()

    elif view == "Liste":
        edited_df = st.data_editor(shop_df, use_container_width=True, num_rows="dynamic", 
                                   column_config={"img": st.column_config.ImageColumn("Görsel"), "price": st.column_config.NumberColumn("Fiyat", format="%.0f TL")})
        # Veri düzenleme (basit versiyon, gelişmiş update gerekebilir)
    
    elif view == "Galeri (Mood)":
        st.markdown("<div style='display:flex; flex-wrap:wrap; gap:10px;'>", unsafe_allow_html=True)
        for _, row in shop_df.iterrows():
            st.markdown(f"<img src='{row['img']}' style='width:150px; height:150px; object-fit:cover; border-radius:10px; border:2px solid #333;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# === TAB 2: PLAN & BÜTÇE ===
with tabs[1]:
    col_fin1, col_fin2 = st.columns([2, 1])
    
    with col_fin1:
        st.subheader("💸 Gider Takvimi (Timeline)")
        # Ödeme Verisi Hazırlama (Mock)
        expenses = df[(df['type'] == 'expense') | (df['type'] == 'item')]
        if not expenses.empty:
            expenses['date'] = pd.to_datetime(expenses['id'].apply(lambda x: datetime.fromtimestamp(int(x)).strftime('%Y-%m-%d')), errors='coerce')
            fig = px.scatter(expenses, x="date", y="price", size="price", color="category", hover_name="title", title="Harcama Zaman Çizelgesi", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
    with col_fin2:
        st.subheader("📌 Gider Ekle")
        with st.form("new_exp"):
            e_name = st.text_input("Gider Adı (Düğün Salonu vb.)")
            e_tot = st.number_input("Toplam Tutar", min_value=0.0)
            e_paid = st.number_input("Ödenen Kapora", min_value=0.0)
            e_date = st.date_input("Son Ödeme Tarihi")
            if st.form_submit_button("EKLE"):
                new_row = {
                    "id": str(int(time.time())), "type": "expense", "category": "Düğün",
                    "title": e_name, "price": e_tot, "paid": e_paid, "status": "Bekliyor",
                    "url": "", "img": "", "quantity": 1, "notes": str(e_date), "extra_data": ""
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df); st.rerun()
        
        # Gider Listesi
        exps = df[df['type'] == 'expense']
        for i, r in exps.iterrows():
            rem = float(r['price']) - float(r['paid'])
            st.warning(f"**{r['title']}**: Kalan {rem:,.0f} TL (Son: {r['notes']})")

# === TAB 3: DAVETLİLER & MASA ===
with tabs[2]:
    c_dav1, c_dav2 = st.columns([1, 2])
    
    with c_dav1:
        st.subheader("👥 Hızlı Davetli Ekle")
        # Toplu Ekleme
        bulk_names = st.text_area("İsimler (Her satıra bir isim)", height=150)
        u_side = st.selectbox("Taraf", ["Kız Tarafı", "Erkek Tarafı", "Ortak"])
        u_table = st.number_input("Masa No Atama", min_value=1, value=1)
        if st.button("LİSTEYE EKLE"):
            names = bulk_names.split('\n')
            new_guests = []
            for n in names:
                if n.strip():
                    new_guests.append({
                        "id": str(int(time.time()) + random.randint(1,1000)), "type": "guest", "category": u_side,
                        "title": n.strip(), "price": 0, "paid": 0, "status": "LCV Bekliyor",
                        "url": "", "img": "", "quantity": u_table, "notes": "", "extra_data": ""
                    })
            if new_guests:
                df = pd.concat([df, pd.DataFrame(new_guests)], ignore_index=True)
                save_data(df); st.rerun()
        
        st.info("💡 500 kişilik liste için Excel'den kopyalayıp buraya yapıştırabilirsin.")

    with c_dav2:
        guests = df[df['type'] == 'guest']
        total_g = len(guests)
        
        st.subheader(f"Masa Düzeni ({total_g} Kişi)")
        
        # Masa Görünümü
        tables = sorted(guests['quantity'].unique())
        if tables:
            t_tabs = st.tabs([f"Masa {int(t)}" for t in tables])
            for idx, t in enumerate(tables):
                with t_tabs[idx]:
                    t_guests = guests[guests['quantity'] == t]
                    for _, g in t_guests.iterrows():
                        c1, c2, c3 = st.columns([3, 2, 1])
                        c1.write(f"**{g['title']}** ({g['category']})")
                        status = c2.selectbox("Durum", ["LCV Bekliyor", "Geliyor", "Gelemiyor"], key=f"lcv_{g['id']}", label_visibility="collapsed")
                        if c3.button("Sil", key=f"gdel_{g['id']}"):
                            df = df[df['id'] != g['id']]; save_data(df); st.rerun()

# === TAB 4: USTA & LOJİSTİK ===
with tabs[3]:
    st.subheader("📞 Usta & Satıcı Rehberi")
    with st.expander("Yeni Kişi Ekle"):
        with st.form("vendor_add"):
            v_name = st.text_input("Firma/Kişi Adı")
            v_serv = st.selectbox("Hizmet", ["Nakliye", "Perdeci", "Fotoğrafçı", "Mobilyacı", "Organizasyon"])
            v_tel = st.text_input("Telefon")
            if st.form_submit_button("KAYDET"):
                new_row = {
                    "id": str(int(time.time())), "type": "vendor", "category": v_serv,
                    "title": v_name, "price": 0, "paid": 0, "status": "Aktif",
                    "url": "", "img": "", "quantity": 1, "notes": v_tel, "extra_data": ""
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df); st.rerun()
    
    vendors = df[df['type'] == 'vendor']
    for _, v in vendors.iterrows():
        with st.container():
            cv1, cv2, cv3 = st.columns([2, 2, 1])
            cv1.markdown(f"**{v['title']}** ({v['category']})")
            
            # WhatsApp Linki Oluşturma
            clean_tel = ''.join(filter(str.isdigit, str(v['notes'])))
            if len(clean_tel) > 9:
                wa_msg = urllib.parse.quote(f"Merhaba {v['title']}, düğün organizasyonu için rahatsız ettim.")
                wa_link = f"https://wa.me/{clean_tel}?text={wa_msg}"
                cv2.markdown(f"[💬 WhatsApp]({wa_link}) | 📞 {v['notes']}")
            else:
                cv2.write(f"📞 {v['notes']}")
                
            if cv3.button("Sil", key=f"vdel_{v['id']}"):
                df = df[df['id'] != v['id']]; save_data(df); st.rerun()
    
    st.divider()
    st.subheader("📦 Taşınma & QR")
    st.info("Koli üzerine yazacağın numara: **KOLI-01**")
    # QR kod oluşturma mantığı burada görselleştirilebilir.

# === TAB 5: BÜYÜK GÜN (D-DAY) ===
with tabs[4]:
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        st.subheader("⏱️ Akış Planı")
        timeline_items = ["08:00 - Kuaför", "12:00 - Damat Traşı", "14:00 - Dış Çekim", "18:00 - Salona Geçiş", "19:00 - Nikah", "20:00 - İlk Dans"]
        for item in timeline_items:
            st.checkbox(item)
            
    with col_d2:
        st.subheader("🎵 Müzik Listesi")
        musics = st.text_area("Şarkılar (Giriş, Dans, Pasta)", height=150, placeholder="Giriş: A Thousand Years\nDans: Pera - Seni Seviyorum")
        if st.button("DJ İçin PDF İndir"):
             st.toast("Liste DJ formatında indirildi!")

    with col_d3:
        st.subheader("💍 Takı & Hediye Takip")
        with st.form("gift_log"):
            g_who = st.text_input("Kim Taktı?")
            g_what = st.text_input("Ne Taktı? (Çeyrek, 100$, vb.)")
            if st.form_submit_button("KAYDET"):
                 st.success("Kaydedildi!")
        
        st.subheader("🚑 Acil Durum Çantası")
        checklist = ["İğne İplik", "Yedek Gömlek", "Ağrı Kesici", "Powerbank", "Tel Toka"]
        for c in checklist:
            st.checkbox(c, key=f"chk_{c}")

# === TAB 6: ANALİZ ===
with tabs[5]:
    items_total = df[df['type'] == 'item']['price'].sum()
    items_paid = df[(df['type'] == 'item') & (df['status'] == 'Alındı')]['price'].sum()
    
    exp_total = df[df['type'] == 'expense']['price'].sum()
    exp_paid = df[df['type'] == 'expense']['paid'].sum()
    
    grand_total = items_total + exp_total
    grand_paid = items_paid + exp_paid
    grand_debt = grand_total - grand_paid
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Bütçe", f"{grand_total:,.0f} TL")
    m2.metric("Ödenen", f"{grand_paid:,.0f} TL")
    m3.metric("Kalan İhtiyaç", f"{grand_debt:,.0f} TL", delta_color="inverse")
    
    st.progress(min(grand_paid / (grand_total if grand_total > 0 else 1), 1.0))
    
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        shop_items = df[df['type']=='item']
        if not shop_items.empty:
            fig = px.pie(shop_items, values='price', names='category', title="Eşya Harcama Dağılımı", hole=0.4, template="plotly_dark")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

# === STICKY FOOTER ===
st.markdown(f"""
<div class="sticky-footer">
    <div style="color:#fff; font-weight:bold;">Sepet Toplamı: <span style="color:#d4af37;">{items_total:,.0f} TL</span></div>
    <div style="color:#aaa; font-size:0.8rem;">Yuva & Co. v2.0</div>
</div>
""", unsafe_allow_html=True)
