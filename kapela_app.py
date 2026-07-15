import streamlit as st
import sqlite3
import re
import os
from datetime import datetime
from pushbullet import Pushbullet

# --- BEZPEČNÁ KONFIGURÁCIA (Streamlit Secrets) ---
# Ak bežíš lokálne, Streamlit si tieto hodnoty vytiahne z .streamlit/secrets.toml
# Na Streamlit Cloud ich zadáš priamo v nastaveniach aplikácie.
PB_API_KEY = st.secrets.get("PB_API_KEY", "o.Ir4LWAKm78pwEhpKkAf6WZY9uZPNCkSm")  # Fallback pre lokálne testovanie
LOGIN_MENO = st.secrets.get("ADMIN_USER", "ovcanskeparobci")
LOGIN_HESLO = st.secrets.get("ADMIN_PASS", "OvcanskeParobci123")

DB_FILE = "kalendar.db"
KAPELA_FOTO_URL = "https://i.postimg.cc/T1Pkgjnw/1000027016.jpg" 

# --- DATABÁZOVÝ MANAŽMENT (SQLite) ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rezervacie (
            id TEXT PRIMARY KEY,
            datum TEXT,
            cas TEXT,
            meno TEXT,
            tel TEXT,
            email TEXT,
            detaily TEXT,
            stav TEXT
        )
    """)
    conn.commit()
    conn.close()

def nacti_data():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM rezervacie")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def uloz_novu_rezervaciu(id_req, datum, cas, meno, tel, email, detaily, stav="cakajuce"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO rezervacie (id, datum, cas, meno, tel, email, detaily, stav)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (id_req, str(datum), str(cas), meno, tel, email, detaily, stav))
    conn.commit()
    conn.close()

def aktualizuj_stav(id_req, novy_stav):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE rezervacie SET stav = ? WHERE id = ?", (novy_stav, id_req))
    conn.commit()
    conn.close()

def zmaz_rezervaciu(id_req):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM rezervacie WHERE id = ?", (id_req,))
    conn.commit()
    conn.close()

# Inicializácia DB pri štarte
init_db()

# --- DIZAJN ---
def apply_style():
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), 
                        url("{KAPELA_FOTO_URL}");
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
            image-rendering: -webkit-optimize-contrast;
            color: #ffffff;
        }}
        [data-testid="stSidebar"] {{ background-color: rgba(20, 20, 20, 0.85) !important; backdrop-filter: blur(12px); border-right: 1px solid #d4af37; }}
        h1, h2, h3, h4 {{ color: #d4af37 !important; font-family: 'Playfair Display', serif; text-shadow: 4px 4px 8px #000000; text-align: center; }}
        
        .info-box {{
            background: rgba(212, 175, 55, 0.15);
            border: 1px solid #d4af37;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            margin: 10px 0;
        }}

        .stForm {{ background-color: rgba(0, 0, 0, 0.8) !important; border: 2px solid #d4af37 !important; border-radius: 20px; padding: 30px; }}
        .stButton>button {{ background-color: #d4af37 !important; color: black !important; border-radius: 12px !important; font-weight: bold !important; width: 100%; transition: 0.3s; }}
        
        .admin-detail-box {{
            background-color: rgba(0, 100, 255, 0.15);
            border-left: 5px solid #0064ff;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-size: 0.95rem;
        }}
        
        /* Zaoblené obrázky v galérii s jemným tieňom */
        .gallery-img {{
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            margin-bottom: 20px;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- POMOCNÉ FUNKCIE ---
def valid_email(email):
    if not email:
        return True  # Email je nepovinný
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def posli_upozornenie(text):
    if not PB_API_KEY or PB_API_KEY.startswith("o.") is False:
        return False
    try:
        pb = Pushbullet(PB_API_KEY)
        pb.push_note("🎸 NOVÝ DOPYT", text)
        return True
    except Exception as e:
        print(f"Pushbullet error: {e}")
        return False

# --- ŠTART APP ---
st.set_page_config(page_title="Ovčanske Parobci", page_icon="🎻", layout="centered")
apply_style()

st.sidebar.markdown("## PAROBCI")
menu = st.sidebar.radio("NAVIGÁCIA", ["🎸 Rezervácia", "📸 Galéria", "🔐 Administrácia"])

# --- 1. REZERVÁCIA ---
if menu == "🎸 Rezervácia":
    st.title("🎻 Ovčanske Parobci")
    st.markdown('<div class="info-box">🪗 Akordeón | 🎻 Husle | 🥁 Bubon | 🎷 Saxofón</div>', unsafe_allow_html=True)
    
    with st.form("main_booking"):
        st.subheader("📩 Rezervačný dopyt")
        col1, col2 = st.columns(2)
        with col1: datum = st.date_input("Dátum akcie", min_value=datetime.now())
        with col2: cas = st.time_input("Čas začiatku")
        
        meno = st.text_input("Meno a priezvisko")
        tel = st.text_input("Telefónne číslo")
        email = st.text_input("E-mail")
        mesto_detaily = st.text_area("Miesto konania a iné detaily")
        
        if st.form_submit_button("ODOSLAŤ REZERVÁCIU"):
            db = nacti_data()
            # Kontrola, či je už termín pevne schválený
            termin_obsadeny = any(a['datum'] == str(datum) and a.get('stav') == 'schvalene' for a in db)
            
            if termin_obsadeny:
                st.error("Tento termín je už bohužiaľ obsadený a schválený.")
            elif not meno or not tel:
                st.warning("Prosím, vyplňte meno a telefónne číslo.")
            elif not valid_email(email):
                st.error("Zadajte e-mail v správnom formáte.")
            elif len(tel.replace(" ", "")) < 9:
                st.error("Telefónne číslo sa zdá byť príliš krátke.")
            else:
                novy_id = str(datetime.now().timestamp()).replace(".", "")
                uloz_novu_rezervaciu(novy_id, datum, cas, meno, tel, email, mesto_detaily)
                
                # Pushbullet správa
                posli_upozornenie(f"Nový dopyt: {datum}\n{meno} ({tel})\nMiesto: {mesto_detaily}")
                
                st.balloons()
                st.success("Odoslané! Váš dopyt evidujeme a čoskoro sa vám ozveme. ✅")

# --- 2. GALÉRIA ---
elif menu == "📸 Galéria":
    st.title("📸 Galéria")
    fotky = [
        "https://i.postimg.cc/vZKfzcN0/received-1165768235166057.jpg", 
        "https://i.postimg.cc/6pPn0ymH/received-640306331056375.jpg", 
        "https://i.postimg.cc/cLzwmrbT/received-796698713423840.jpg", 
        "https://i.postimg.cc/RZYKRND1/received-936809825229820.jpg"
    ]
    for f in fotky: 
        st.image(f, use_container_width=True)

# --- 3. ADMIN ---
else:
    st.title("🔐 Administrácia")
    if 'auth' not in st.session_state: 
        st.session_state['auth'] = False
        
    if not st.session_state['auth']:
        with st.form("login"):
            u = st.text_input("Meno")
            h = st.text_input("Heslo", type="password")
            if st.form_submit_button("Vstúpiť"):
                if u == LOGIN_MENO and h == LOGIN_HESLO: 
                    st.session_state['auth'] = True
                    st.rerun()
                else: 
                    st.error("Nesprávne prihlasovacie údaje!")
    else:
        if st.sidebar.button("Odhlásiť sa"): 
            st.session_state['auth'] = False
            st.rerun()
            
        t1, t2, t3 = st.tabs(["📩 Nové dopyty", "📅 Kalendár", "➕ Pridať"])
        db = nacti_data()
        
        with t1:
            # Čakajúce dopyty zoradené od najnovších dátumov
            cakajuce = [a for a in db if a.get("stav") == "cakajuce"]
            cakajuce.sort(key=lambda x: x['datum'])
            
            if not cakajuce:
                st.info("Žiadne nové čakajúce dopyty. 🎉")
                
            for i, a in enumerate(cakajuce):
                info_mesto = a.get('detaily', 'Neuvedené')
                with st.expander(f"DOPYT: {a['datum']} - {a.get('meno', 'Neznámy')}"):
                    # Rýchle klikateľné prepojenia
                    st.markdown(f"📞 **Kontakt:** [{a.get('tel', '---')}](tel:{a.get('tel', '')}) | 📧 [{a.get('email', '---')}](mailto:{a.get('email', '')})")
                    st.write(f"🕒 **Čas:** {a.get('cas', '---')}")
                    st.markdown(f"""<div class="admin-detail-box"><b>Miesto a detaily:</b><br>{info_mesto}</div>""", unsafe_allow_html=True)
                    
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Schváliť", key=f"ok{i}"):
                        aktualizuj_stav(a['id'], "schvalene")
                        st.rerun()
                    if c2.button("🗑️ Zmazať", key=f"no{i}"):
                        zmaz_rezervaciu(a['id'])
                        st.rerun()
        
        with t2:
            # Schválené akcie zoradené chronologicky
            schvalene = [a for a in db if a.get("stav") == "schvalene"]
            schvalene.sort(key=lambda x: x['datum'])
            
            if not schvalene:
                st.info("Zatiaľ žiadne schválené akcie v kalendári.")
                
            for i, a in enumerate(schvalene):
                info_mesto = a.get('detaily', 'Neuvedené')
                with st.expander(f"📅 {a['datum']} - {a.get('meno', 'Akcia')}"):
                    st.markdown(f"📞 **Kontakt:** [{a.get('tel', '---')}](tel:{a.get('tel', '')}) | 🕒 {a.get('cas', '')}")
                    st.markdown(f"""<div class="admin-detail-box"><b>Miesto/Poznámka:</b><br>{info_mesto}</div>""", unsafe_allow_html=True)
                    
                    if st.button("🗑️ Odstrániť", key=f"del{i}"):
                        zmaz_rezervaciu(a['id'])
                        st.rerun()
        
        with t3:
            with st.form("add_manual"):
                d = st.date_input("Dátum")
                m = st.text_input("Názov")
                det = st.text_area("Miesto/Poznámka")
                if st.form_submit_button("Uložiť"):
                    novy_id = str(datetime.now().timestamp()).replace(".", "")
                    uloz_novu_rezervaciu(novy_id, d, "Neuvedený", m, "Neuvedené", "Neuvedený", det, stav="schvalene")
                    st.success("Akcia pridaná priamo do kalendára! ✅")
                    st.rerun()

st.markdown(f'<div style="text-align:center; margin-top:50px; color:#ccc;"><b>Podpora:</b> 0944 757 122</div>', unsafe_allow_html=True)
