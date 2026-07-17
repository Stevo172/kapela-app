import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from pushbullet import Pushbullet
from supabase import create_client
import calendar

# --- BEZPEČNÁ KONFIGURÁCIA (IBA st.secrets) ---
# ⚠️ VŠETKY CITLIVÉ ÚDAJE MUSIA BYŤ V st.secrets - NIKDY V KÓDE!
try:
    PB_API_KEY = st.secrets["PB_API_KEY"]
    LOGIN_MENO = st.secrets["ADMIN_USER"]
    LOGIN_HESLO = st.secrets["ADMIN_PASS"]
    SENDER_EMAIL = st.secrets["sender_email"]
    SENDER_PASSWORD = st.secrets["sender_password"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except KeyError as e:
    st.error(f"❌ KRITICKÁ CHYBA: Chýba secret '{e.args[0]}' v Streamlit Secrets! Kontaktujte správcu.")
    st.stop()

KAPELA_FOTO_URL = "https://i.postimg.cc/T1Pkgjnw/1000027016.jpg" 

# --- NASTAVENIE CIEN ---
CENA_OSLAVA_HODINA = 130
CENA_SPRIEVOD_ZAKLAD = 300
CENA_SPRIEVOD_POLHODINA = 50  
CENA_STOLY_HODINA = 120  
CENA_APARATURA = 100      
CENA_ZA_KM = 0.50        

# --- INICIALIZÁCIA SUPABASE ---
@st.cache_resource
def get_supabase_client():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"❌ Nepodarilo sa vytvoriť Supabase klienta: {e}")
        return None

supabase = get_supabase_client()

# --- SKRYTIE GITHUB IKONY A STREAMLIT MENU ---
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
        
        /* Skrytie sidebaru a menu */
        [data-testid="collapsedSidebarNoOverlay"], 
        [data-testid="stSidebar"], 
        button[data-testid="stSidebarCollapseButton"] {{
            display: none !important;
        }}
        
        /* Skrytie GitHub ikony a menu v pravom hornom rohu */
        [data-testid="stToolbar"] {{
            display: none !important;
        }}
        
        /* Skrytie "Deploy" tlačidla */
        .stDeployButton {{
            display: none !important;
        }}
        
        h1, h2, h3, h4 {{ color: #d4af37 !important; font-family: 'Playfair Display', serif; text-shadow: 4px 4px 8px #000000; text-align: center; }}
        
        .info-box {{
            background: rgba(212, 175, 55, 0.15);
            border: 1px solid #d4af37;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            margin: 10px 0;
        }}

        .cennik-container {{
            background: rgba(0, 0, 0, 0.85);
            border: 2px solid #d4af37;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 0 25px rgba(212, 175, 55, 0.25);
            margin-bottom: 25px;
        }}

        .kalkulacka-box {{
            background: rgba(212, 175, 55, 0.25);
            border: 2px dashed #d4af37;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin: 20px 0;
            box-shadow: 0 0 15px rgba(212, 175, 55, 0.20);
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

        div[data-testid="stRadio"] {{
            background: transparent !important;
            padding: 10px 0 !important;
        }}
        div[data-testid="stRadio"] > div[role="radiogroup"] {{
            display: flex !important;
            flex-direction: row !important;
            justify-content: center !important;
            flex-wrap: wrap !important;
            gap: 12px !important;
        }}
        div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {{
            display: none !important;
        }}
        div[data-testid="stRadio"] div[role="radiogroup"] > label {{
            background-color: rgba(0, 0, 0, 0.75) !important;
            border: 2px solid #d4af37 !important;
            color: #ffffff !important;
            padding: 12px 24px !important;
            border-radius: 30px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            font-weight: bold !important;
            text-align: center !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5) !important;
            min-width: 140px !important;
        }}
        div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {{
            background-color: rgba(212, 175, 55, 0.25) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 15px rgba(212, 175, 55, 0.3) !important;
        }}
        div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {{
            background-color: #d4af37 !important;
            color: #000000 !important;
            box-shadow: 0 0 18px #d4af37 !important;
            border-color: #ffffff !important;
        }}

        /* KALENDÁR TABUĽKA ŠTÝLY */
        .calendar-table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(0, 0, 0, 0.7);
            border: 2px solid #d4af37;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }}

        .calendar-table th {{
            background: rgba(212, 175, 55, 0.3);
            color: #d4af37;
            padding: 12px;
            font-weight: bold;
            border: 1px solid #d4af37;
            text-align: center;
        }}

        .calendar-table td {{
            padding: 10px;
            border: 1px solid #555;
            text-align: center;
            font-weight: bold;
            min-height: 40px;
            vertical-align: middle;
        }}

        .day-volny {{
            background-color: rgba(0, 180, 100, 0.4);
            border: 2px solid #00ff88 !important;
            color: #00ff88;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .day-volny:hover {{
            background-color: rgba(0, 200, 120, 0.6);
            box-shadow: 0 0 10px #00ff88;
        }}

        .day-obsadeny {{
            background-color: rgba(200, 0, 0, 0.4);
            border: 2px solid #ff4444 !important;
            color: #ff6666;
        }}

        .day-cakajuci {{
            background-color: rgba(200, 150, 0, 0.4);
            border: 2px solid #ffbb00 !important;
            color: #ffdd00;
        }}

        .day-empty {{
            background-color: rgba(50, 50, 50, 0.3);
            border: 1px solid #333 !important;
            color: #666;
        }}

        .legend-box {{
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #d4af37;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }}

        .legend-color {{
            width: 25px;
            height: 25px;
            border-radius: 4px;
            border: 2px solid;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- FUNKCIE PRE NAČÍTANIE ZO SUPABASE ---
def nacti_data():
    if supabase:
        try:
            response = supabase.table("kalendar").select("*").execute()
            return response.data if response.data else []
        except Exception as e:
            st.error(f"Chyba načítania zo Supabase: {e}")
    return []

def nacti_media():
    vysledky = {"fotky": [], "videa": []}
    if supabase:
        try:
            response = supabase.storage.from_("parobci-media").list()
            if response:
                for subor in response:
                    nazov = subor.get("name", "")
                    if nazov and nazov != ".emptyFolderPlaceholder":
                        try:
                            public_url = supabase.storage.from_("parobci-media").get_public_url(nazov)
                            ext = nazov.split(".")[-1].lower()
                            if ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                                vysledky["fotky"].append(public_url)
                            elif ext in ["mp4", "mov", "avi", "webm"]:
                                vysledky["videa"].append(public_url)
                        except Exception as e:
                            pass
        except Exception as e:
            pass
    return vysledky

def nacti_vsetky_media():
    subbory_list = []
    if supabase:
        try:
            response = supabase.storage.from_("parobci-media").list()
            if response:
                for subor in response:
                    nazov = subor.get("name", "")
                    if nazov and nazov != ".emptyFolderPlaceholder":
                        ext = nazov.split(".")[-1].lower()
                        typ = "Foto" if ext in ["jpg", "jpeg", "png", "gif", "webp"] else "Video" if ext in ["mp4", "mov", "avi", "webm"] else "Iný"
                        subbory_list.append({
                            "nazov": nazov,
                            "ext": ext,
                            "typ": typ,
                            "velkost": subor.get("metadata", {}).get("size", 0),
                            "vytvorene": subor.get("created_at", "")
                        })
        except Exception as e:
            pass
    return subbory_list

# --- KALENDÁR GENERÁTOR (TABUĽKA) ---
def vygeneruj_kalendar(rok, mesiac, db_data):
    """Vygeneruje HTML tabuľku s farbením dní podľa stavu"""
    # Získaj všetky obsadené a čakajúce dni
    obsadene_dni = set()
    cakajuce_dni = set()
    
    for zaznam in db_data:
        try:
            datum_obj = datetime.strptime(zaznam.get('datum', ''), '%Y-%m-%d').date()
            if datum_obj.year == rok and datum_obj.month == mesiac:
                if zaznam.get('stav') == 'schvalene':
                    obsadene_dni.add(datum_obj.day)
                elif zaznam.get('stav') == 'cakajuce':
                    cakajuce_dni.add(datum_obj.day)
        except:
            pass
    
    # Vygeneruj HTML tabuľku
    mesiace = ["Januar", "Februar", "Marec", "April", "Maj", "Jun", 
               "Jul", "August", "September", "Oktober", "November", "December"]
    
    cal = calendar.monthcalendar(rok, mesiac)
    dny_tyzdna = ["Po", "Ut", "St", "Št", "Pia", "So", "Ne"]
    
    html = f"""
    <h4 style="text-align: center; color: #d4af37;">📅 {mesiace[mesiac-1]} {rok}</h4>
    <table class="calendar-table">
        <tr>
    """
    
    # Hlavičky dní
    for den_nazov in dny_tyzdna:
        html += f"<th>{den_nazov}</th>"
    
    html += "</tr>"
    
    # Dni kalendára
    for tyzden in cal:
        html += "<tr>"
        for den in tyzden:
            if den == 0:
                html += '<td class="day-empty"></td>'
            else:
                datum_str = f"{rok}-{mesiac:02d}-{den:02d}"
                datum_obj = datetime.strptime(datum_str, '%Y-%m-%d').date()
                dnes = datetime.now().date()
                
                if datum_obj < dnes:
                    html += f'<td class="day-empty">❌<br>{den}</td>'
                elif den in obsadene_dni:
                    html += f'<td class="day-obsadeny">🔴<br>{den}</td>'
                elif den in cakajuce_dni:
                    html += f'<td class="day-cakajuci">🟡<br>{den}</td>'
                else:
                    html += f'<td class="day-volny">🟢<br>{den}</td>'
        
        html += "</tr>"
    
    html += """
    </table>
    <div class="legend-box">
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(0, 180, 100, 0.4); border-color: #00ff88;"></div>
            <span>🟢 Voľný</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(200, 150, 0, 0.4); border-color: #ffbb00;"></div>
            <span>🟡 Čakajúci</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(200, 0, 0, 0.4); border-color: #ff4444;"></div>
            <span>🔴 Obsadený</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: rgba(50, 50, 50, 0.3); border-color: #333;"></div>
            <span>❌ Minulosť</span>
        </div>
    </div>
    """
    
    return html

# --- NOTIFIKÁCIE ---
def posli_upozornenie(text):
    try:
        if PB_API_KEY:
            pb = Pushbullet(PB_API_KEY)
            pb.push_note("🎸 NOVÝ DOPYT", text)
            return True
    except Exception as e:
        st.error(f"⚠️ Pushbullet neodoslal správu! Chyba: {e}")
    return False

def posli_email_zakaznikovi(to_email, meno_klienta, datum_akcie, cas_akcie, typ_vystupenia, celkova_cena, detaily_miesta):
    if not to_email or "@" not in to_email or not SENDER_PASSWORD:
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"Status: Prijatie dopytu - Ovčanske Parobci ({datum_akcie})"
        
        body = f"""Dobrý deň, {meno_klienta},

ďakujeme za Váš záujem o vystúpenie našej hudobnej skupiny Ovčanske Parobci.
Vašu požiadavku sme úspešne prijali a momentálne ju spracovávame. 

Rekapitulácia Vášho dopytu:
------------------------------------------
Dátum akcie: {datum_akcie}
Čas začiatku: {cas_akcie}
Typ vystúpenia: {typ_vystupenia}
Orientačná cena: {celkova_cena}
Miesto konania a detaily: {detaily_miesta}
------------------------------------------

Čoskoro Vás budeme kontaktovať pre telefonické potvrdenie termínu a doladenie detailov.

S pozdravom,
Ľudová hudba Ovčanske Parobci
Tel. číslo: 0944 757 122
E-mail: {SENDER_EMAIL}
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        return True
    except Exception as e:
        st.warning(f"Nepodarilo sa odoslať potvrdzujúci e-mail zákazníkovi: {e}")
        return False

# --- ŠTART APP ---
st.set_page_config(page_title="Ovčanske Parobci", page_icon="🎻", layout="centered", initial_sidebar_state="collapsed")
apply_style()

menu = st.radio(
    "NAVIGÁCIA", 
    ["🎸 Rezervácia", "💰 Cenník", "📸 Galéria", "🔐 Administrácia"], 
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

if 'db_data' not in st.session_state:
    st.session_state['db_data'] = nacti_data()

# --- 1. REZERVÁCIA ---
if menu == "🎸 Rezervácia":
    st.title("🎻 Rezervácia vystúpenia")
    st.markdown('<div class="info-box">🪗 Akordeón | 🎻 Husle | 🥁 Bubon | 🎷 Saxofón</div>', unsafe_allow_html=True)
    
    # --- KALENDÁR ---
    st.markdown("<h4 style='text-align: center; margin-bottom: 10px; margin-top: 20px;'>📅 Dostupnosť v kalendári</h4>", unsafe_allow_html=True)
    
    dnes = datetime.now()
    mesice_options = []
    for i in range(12):
        mesiac_num = dnes.month + i
        rok_num = dnes.year
        if mesiac_num > 12:
            mesiac_num -= 12
            rok_num += 1
        mesice_options.append((rok_num, mesiac_num))
    
    vybrany_mesiac = st.selectbox(
        "Vyber mesiac:",
        mesice_options,
        format_func=lambda x: f"{['Januar', 'Februar', 'Marec', 'April', 'Maj', 'Jun', 'Jul', 'August', 'September', 'Oktober', 'November', 'December'][x[1]-1]} {x[0]}",
        key="mesiac_selector"
    )
    
    db = nacti_data()
    kalendar_html = vygeneruj_kalendar(vybrany_mesiac[0], vybrany_mesiac[1], db)
    st.markdown(kalendar_html, unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center; margin-bottom: 5px; margin-top: 20px;'>Výpočet ceny vystúpenia</h4>", unsafe_allow_html=True)
    
    typ_akcie = st.selectbox(
        "Vyberte typ vystúpenia:",
        ["🎂 Rodinná oslava / Jubileum", "👰 Svadobný sprievod a odobierka", "🍻 Hranie pomedzi stoly / Posedenie"]
    )
    
    col_vstupy, col_km = st.columns(2)
    cena_hudba = 0
    popis_hudby = ""
    
    with col_vstupy:
        if typ_akcie == "🎂 Rodinná oslava / Jubileum":
            hodiny = st.slider("Dĺžka hrania (v hodinách)", min_value=1, max_value=12, value=5, key="hours_oslava")
            cena_hudba = hodiny * CENA_OSLAVA_HODINA
            popis_hudby = f"Rodinná oslava ({hodiny} hod.)"
            
        elif typ_akcie == "👰 Svadobný sprievod a odobierka":
            st.info("Základná cena zahŕňa sprievod do 2 hodín (akusticky).")
            polhodiny_navyse = st.slider("Čas navyše (počet začatých polhodín)", min_value=0, max_value=10, value=0, key="extra_sprievod")
            cena_hudba = CENA_SPRIEVOD_ZAKLAD + (polhodiny_navyse * CENA_SPRIEVOD_POLHODINA)
            if polhodiny_navyse > 0:
                popis_hudby = f"Svadobný sprievod (2 hod. + {polhodiny_navyse}x polhodina navyše)"
            else:
                popis_hudby = "Svadobný sprievod (základ do 2 hod.)"
                
        elif typ_akcie == "🍻 Hranie pomedzi stoly / Posedenie":
            hodiny = st.slider("Dĺžka hrania (v hodinách)", min_value=1, max_value=12, value=3, key="hours_stoly")
            cena_hudba = hodiny * CENA_STOLY_HODINA
            popis_hudby = f"Hranie pomedzi stoly ({hodiny} hod.)"

    with col_km:
        km = st.slider("Vzdialenosť z obce Ovčie (v km jednosmerne)", min_value=0, max_value=300, value=0, step=5, key="calc_km")
    
    potrebuje_aparaturu = st.checkbox(
        f"Zabezpečiť zvukovú aparatúru (aktívne reprobedne, mixpult, mikrofóny) (+{CENA_APARATURA} €)",
        value=False
    )
    
    cena_doprava = km * 2 * CENA_ZA_KM
    prplatok_aparatura = CENA_APARATURA if potrebuje_aparaturu else 0
    celkova_cena = cena_hudba + cena_doprava + prplatok_aparatura
    
    detaily_vypoctu = f"{popis_hudby}: {cena_hudba:.2f} €"
    if potrebuje_aparaturu:
        detaily_vypoctu += f" | Ozvučenie: {CENA_APARATURA:.2f} €"
    detaily_vypoctu += f" | Doprava {km*2} km celkovo: {cena_doprava:.2f} €"
    
    st.markdown(f"""
        <div class="kalkulacka-box">
            <span style="font-size: 1.1rem; color: #ccc;">Odhadovaná cena vystúpenia:</span><br>
            <span style="font-size: 2.2rem; font-weight: bold; color: #d4af37;">{celkova_cena:.2f} €</span><br>
            <small style="color: #aaa;">({detaily_vypoctu})</small>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("main_booking"):
        st.subheader("📩 Rezervačný dopyt")
        
        col1, col2 = st.columns(2)
        with col1: 
            datum = st.date_input("Dátum akcie", min_value=datetime.now())
        with col2: 
            cas = st.time_input("Čas začiatku")
            
        meno = st.text_input("Meno a priezvisko")
        tel = st.text_input("Telefónne číslo")
        email = st.text_input("E-mail")
        mesto_detaily = st.text_area("Presná adresa konania (mesto/sála) a iné detaily")
        
        if st.form_submit_button("ODOSLAŤ REZERVÁCIU S TOUTO CENOU"):
            db = nacti_data()
            
            if any(a['datum'] == str(datum) for a in db if a.get('stav') == 'schvalene'):
                st.error("Tento termín je už obsadený.")
            elif not meno or not tel:
                st.warning("Vyplňte, prosím, vaše meno a telefónne číslo.")
            else:
                txt_aparatury = "S APARATÚROU" if potrebuje_aparaturu else "BEZ aparatúry"
                vypocitana_cena_txt = f"{celkova_cena:.2f} € ({popis_hudby}, {txt_aparatury}, {km} km jednosmerne)"
                
                nova = {
                    "id": str(datetime.now().timestamp()), 
                    "datum": str(datum), 
                    "cas": f"{cas.strftime('%H:%M')}",
                    "meno": meno, 
                    "tel": tel, 
                    "email": email, 
                    "detaily": f"[{typ_akcie}] [Ozvučenie: {txt_aparatury}] {mesto_detaily}", 
                    "vypocitana_cena": vypocitana_cena_txt,  
                    "stav": "cakajuce"
                }
                
                if supabase:
                    try:
                        res = supabase.table("kalendar").insert(nova).execute()
                        if res.data:
                            st.session_state['db_data'] = nacti_data()
                            
                            posli_upozornenie(f"Nový dopyt: {datum}\n{meno} ({tel})\nTyp: {typ_akcie}\nMiesto: {mesto_detaily}\nCena: {vypocitana_cena_txt}")
                            if email:
                                posli_email_zakaznikovi(email, meno, str(datum), cas.strftime('%H:%M'), typ_akcie, vypocitana_cena_txt, mesto_detaily)
                            
                            st.balloons()
                            st.success("Odoslané! Ozveme sa vám. ✅ Taktiež sme Vám odoslali potvrdzujúci e-mail.")
                        else:
                            st.error("Chyba: Dáta sa nepodarilo zapísať do databázy.")
                    except Exception as e:
                        st.error(f"Chyba zápisu do Supabase: {e}")
                else:
                    st.error("Chyba: Databáza Supabase nie je pripojená!")

# --- 2. PODROBNÝ CENNÍK ---
elif menu == "💰 Cenník":
    st.title("💰 Cenník služieb")
    st.markdown(f"""
        <div class="cennik-container">
            <h3 style="margin-top: 0; padding-top: 20px; color: #d4af37; text-align: center;">Naše sadzby (sme 5-členná kapela)</h3>
            <table style="width: 100%; color: #fff; border-collapse: collapse; margin-top: 20px;">
                <tr style="border-bottom: 2px solid #d4af37; text-align: left;">
                    <th style="padding: 12px; color: #d4af37;">Služba</th>
                    <th style="padding: 12px; color: #d4af37;">Cena</th>
                    <th style="padding: 12px; color: #d4af37;">Poznámka</th>
                </tr>
                <tr style="border-bottom: 1px solid rgba(212,175,55,0.2);">
                    <td style="padding: 12px; font-weight: bold;">🎂 Rodinná oslava / Jubileum</td>
                    <td style="padding: 12px; color: #d4af37; font-weight: bold;">{CENA_OSLAVA_HODINA} € / hodina</td>
                    <td style="padding: 12px; color: #ccc; font-size: 0.9rem;">Živé hranie na oslavách.</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(212,175,55,0.2);">
                    <td style="padding: 12px; font-weight: bold;">👰 Svadobný sprievod a odobierka</td>
                    <td style="padding: 12px; color: #d4af37; font-weight: bold;">{CENA_SPRIEVOD_ZAKLAD} € základ</td>
                    <td style="padding: 12px; color: #ccc; font-size: 0.9rem;">Do 2 hodín. Každá ďalšia polhodina +{CENA_SPRIEVOD_POLHODINA} €.</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(212,175,55,0.2);">
                    <td style="padding: 12px; font-weight: bold;">🍻 Hranie pomedzi stoly / Posedenie</td>
                    <td style="padding: 12px; color: #d4af37; font-weight: bold;">{CENA_STOLY_HODINA} € / hodina</td>
                    <td style="padding: 12px; color: #ccc; font-size: 0.9rem;">Komorné akustické hranie naživo.</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(212,175,55,0.2);">
                    <td style="padding: 12px; font-weight: bold;">🎤 Profesionálna zvuková aparatúra</td>
                    <td style="padding: 12px; color: #d4af37; font-weight: bold;">+{CENA_APARATURA} € jednorazovo</td>
                    <td style="padding: 12px; color: #ccc; font-size: 0.9rem;">Pre väčšie sály/vonku.</td>
                </tr>
                <tr>
                    <td style="padding: 12px; font-weight: bold;">🚗 Doprava (z obce Ovčie)</td>
                    <td style="padding: 12px; color: #d4af37; font-weight: bold;">{CENA_ZA_KM:.2f} € / km</td>
                    <td style="padding: 12px; color: #ccc; font-size: 0.9rem;">Počíta sa cesta tam aj späť.</td>
                </tr>
            </table>
        </div>
    """, unsafe_allow_html=True)

# --- 3. GALÉRIA ---
elif menu == "📸 Galéria":
    st.title("📸 Galéria a Videá")
    
    media = nacti_media()
    
    if media["videa"]:
        st.subheader("🎥 Videá z našich vystúpení")
        col_v1, col_v2 = st.columns(2)
        for idx, video_url in enumerate(media["videa"]):
            if idx % 2 == 0:
                with col_v1:
                    st.video(video_url)
            else:
                with col_v2:
                    st.video(video_url)
        st.markdown("<hr style='border-color: rgba(212,175,55,0.3);'>", unsafe_allow_html=True)
        
    st.subheader("🖼️ Fotogaléria")
    
    if media["fotky"]:
        col_img1, col_img2 = st.columns(2)
        for idx, f in enumerate(media["fotky"]):
            if idx % 2 == 0:
                with col_img1:
                    st.image(f, use_container_width=True)
            else:
                with col_img2:
                    st.image(f, use_container_width=True)
    else:
        st.info("📸 Galéria je zatiaľ prázdna. Fotky budú pridané čoskoro.")

# --- 4. ADMIN ---
else:
    col_title, col_logout = st.columns([3, 1])
    with col_title:
        st.title("🔐 Administrácia")
    
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    
    if not st.session_state['auth']:
        with st.form("login"):
            u = st.text_input("Meno")
            h = st.text_input("Heslo", type="password")
            if st.form_submit_button("Vstúpiť"):
                if u == LOGIN_MENO and h == LOGIN_HESLO: 
                    st.session_state['auth'] = True
                    st.rerun()
                else: 
                    st.error("❌ Nesprávne prihlasovacie údaje!")
    else:
        with col_logout:
            st.write("") 
            if st.button("Odhlásiť sa", key="logout_btn"): 
                st.session_state['auth'] = False
                st.rerun()
                
        t1, t2, t3, t4 = st.tabs(["📩 Nové dopyty", "📅 Kalendár", "📁 Sprava medii", "➕ Pridat udalost"])
        
        db = nacti_data()
        
        # --- TAB 1: NOVÉ DOPYTY ---
        with t1:
            cakajuce = [a for a in db if a.get("stav") == "cakajuce"]
            if not cakajuce:
                st.info("Žiadne nové dopyty.")
            for i, a in enumerate(cakajuce):
                info_mesto = a.get('detaily', 'Neuvedené')
                kalkulacia = a.get('vypocitana_cena', 'Nenapočítaná')
                with st.expander(f"DOPYT: {a['datum']} - {a.get('meno', 'Neznámy')}"):
                    st.write(f"📞 **Kontakt:** {a.get('tel', '---')} | 📧 {a.get('email', '---')}")
                    st.write(f"🕒 **Čas:** {a.get('cas', '---')}")
                    st.write(f"💰 **Cena:** {kalkulacia}")
                    st.markdown(f"""<div class="admin-detail-box"><b>Miesto a detaily:</b><br>{info_mesto}</div>""", unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns(3)
                    if c1.button("✅ Schváliť", key=f"ok{i}"):
                        if supabase:
                            try:
                                supabase.table("kalendar").update({"stav": "schvalene"}).eq("id", a['id']).execute()
                                st.session_state['db_data'] = nacti_data()
                                st.success("Dopyt schválený!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Nepodarilo sa schváliť v Supabase: {e}")
                    
                    if c2.button("🗑️ Zmazať", key=f"no{i}"):
                        if supabase:
                            try:
                                supabase.table("kalendar").delete().eq("id", a['id']).execute()
                                st.session_state['db_data'] = nacti_data()
                                st.success("Dopyt vymazaný!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Nepodarilo sa vymazať zo Supabase: {e}")
                        
                    edit_key = f"edit_active_t1_{a['id']}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False
                        
                    if c3.button("✍️ Upraviť", key=f"btn_edit_t1_{i}"):
                        st.session_state[edit_key] = not st.session_state[edit_key]
                        st.rerun()
                    
                    if st.session_state[edit_key]:
                        with st.form(key=f"form_edit_t1_{a['id']}"):
                            novy_datum = st.text_input("Dátum", value=a.get('datum', ''))
                            novy_cas = st.text_input("Čas", value=a.get('cas', ''))
                            nove_meno = st.text_input("Meno", value=a.get('meno', ''))
                            novy_tel = st.text_input("Telefón", value=a.get('tel', ''))
                            novy_email = st.text_input("E-mail", value=a.get('email', ''))
                            nove_detaily = st.text_area("Miesto/Poznámka", value=info_mesto)
                            
                            if st.form_submit_button("Uložiť zmeny"):
                                upravene = {
                                    "datum": novy_datum,
                                    "cas": novy_cas,
                                    "meno": nove_meno,
                                    "tel": novy_tel,
                                    "email": novy_email,
                                    "detaily": nove_detaily
                                }
                                if supabase:
                                    try:
                                        supabase.table("kalendar").update(upravene).eq("id", a['id']).execute()
                                        st.session_state['db_data'] = nacti_data()
                                        st.session_state[edit_key] = False
                                        st.success("Zmeny uložené!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Chyba úpravy Supabase: {e}")
        
        # --- TAB 2: KALENDÁR ---
        with t2:
            schvalene = [a for a in db if a.get("stav") == "schvalene"]
            schvalene.sort(key=lambda x: x['datum'])
            if not schvalene:
                st.info("Kalendár je prázdny.")
            for i, a in enumerate(schvalene):
                info_mesto = a.get('detaily', 'Neuvedené')
                kalkulacia = a.get('vypocitana_cena', 'Nenapočítaná')
                with st.expander(f"📅 {a['datum']} - {a.get('meno', 'Akcia')}"):
                    st.write(f"📞 {a.get('tel', '')} | 🕒 {a.get('cas', '')}")
                    st.write(f"💰 **Orientačná kalkulácia:** {kalkulacia}")
                    st.markdown(f"""<div class="admin-detail-box"><b>Miesto/Poznámka:</b><br>{info_mesto}</div>""", unsafe_allow_html=True)
                    
                    c1, c2 = st.columns(2)
                    
                    if c1.button("🗑️ Odstrániť", key=f"del{i}"):
                        if supabase:
                            try:
                                supabase.table("kalendar").delete().eq("id", a['id']).execute()
                                st.session_state['db_data'] = nacti_data()
                                st.success("Akcia odstránená!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Nepodarilo sa zmazať zo Supabase: {e}")
                    
                    edit_key_t2 = f"edit_active_t2_{a['id']}"
                    if edit_key_t2 not in st.session_state:
                        st.session_state[edit_key_t2] = False
                        
                    if c2.button("✍️ Upraviť", key=f"btn_edit_t2_{i}"):
                        st.session_state[edit_key_t2] = not st.session_state[edit_key_t2]
                        st.rerun()
                    
                    if st.session_state[edit_key_t2]:
                        with st.form(key=f"form_edit_t2_{a['id']}"):
                            novy_datum = st.text_input("Dátum", value=a.get('datum', ''))
                            novy_cas = st.text_input("Čas", value=a.get('cas', ''))
                            nove_meno = st.text_input("Meno / Názov", value=a.get('meno', ''))
                            novy_tel = st.text_input("Telefón", value=a.get('tel', ''))
                            novy_email = st.text_input("E-mail", value=a.get('email', ''))
                            nove_detaily = st.text_area("Miesto/Poznámka", value=info_mesto)
                            
                            if st.form_submit_button("Uložiť zmeny"):
                                upravene = {
                                    "datum": novy_datum,
                                    "cas": novy_cas,
                                    "meno": nove_meno,
                                    "tel": novy_tel,
                                    "email": novy_email,
                                    "detaily": nove_detaily
                                }
                                if supabase:
                                    try:
                                        supabase.table("kalendar").update(upravene).eq("id", a['id']).execute()
                                        st.session_state['db_data'] = nacti_data()
                                        st.session_state[edit_key_t2] = False
                                        st.success("Zmeny uložené!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Chyba úpravy Supabase: {e}")
        
        # --- TAB 3: SPRAVA MEDIÍ ---
        with t3:
            st.subheader("📁 Nahrať fotky a videá priamo z počítača")
            st.write("Tu môžete nahrať fotky (.jpg, .png) alebo videá (.mp4), ktoré sa ihneď zobrazia v Galérii.")
            
            subor_na_nahratie = st.file_uploader(
                "Kliknite sem alebo pretiahnite súbor", 
                type=["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "avi", "webm"],
                key="uploader_medii"
            )
            
            if subor_na_nahratie is not None:
                if st.button("🚀 NAHRAŤ VYBRANÝ SÚBOR"):
                    if supabase:
                        try:
                            subor_bytes = subor_na_nahratie.read()
                            povodny_nazov = subor_na_nahratie.name
                            cisty_nazov = f"{int(datetime.now().timestamp())}_{povodny_nazov.replace(' ', '_')}"
                            
                            res = supabase.storage.from_("parobci-media").upload(
                                path=cisty_nazov,
                                file=subor_bytes,
                                file_options={"content-type": subor_na_nahratie.type}
                            )
                            
                            if res:
                                st.success(f"Súbor '{povodny_nazov}' bol úspešne nahraný! 🎉")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Chyba pri nahrávaní súboru: {e}")
                    else:
                        st.error("Chyba: Pripojenie k Supabase nie je aktívne.")
            
            st.markdown("<hr style='border-color: rgba(212,175,55,0.3); margin-top: 30px;'>", unsafe_allow_html=True)
            st.subheader("📸 Všetky médiá v galérii")
            
            vsetky_media = nacti_vsetky_media()
            
            if vsetky_media:
                st.write(f"**Počet súborov:** {len(vsetky_media)}")
                
                for idx, media_item in enumerate(vsetky_media):
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"📄 **{media_item['nazov'][:40]}...**" if len(media_item['nazov']) > 40 else f"📄 **{media_item['nazov']}**")
                    
                    with col2:
                        st.write(f"🏷️ {media_item['typ']}")
                    
                    with col3:
                        velkost_kb = media_item['velkost'] / 1024
                        st.write(f"💾 {velkost_kb:.1f} KB")
                    
                    with col4:
                        if st.button("🗑️", key=f"delete_media_{idx}"):
                            if supabase:
                                try:
                                    supabase.storage.from_("parobci-media").remove([media_item['nazov']])
                                    st.success(f"Súbor '{media_item['nazov']}' vymazaný!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Chyba pri vymazávaní: {e}")
            else:
                st.info("Galéria je zatiaľ prázdna.")
        
        # --- TAB 4: PRIDAŤ UDALOSŤ ---
        with t4:
            with st.form("add_manual"):
                st.subheader("➕ Manuálne pridať akciu")
                
                d = st.date_input("Dátum akcie", value=datetime.today())
                t_time = st.time_input("Čas začiatku", value=datetime.now().time())
                m = st.text_input("Meno a priezvisko / Názov akcie")
                tel_cislo = st.text_input("Telefónne číslo")
                em_adresa = st.text_input("E-mail")
                dohodnuta_cena = st.text_input("Dohodnutá cena (napr. 500.00 €)", value="0.00 €")
                det = st.text_area("Presná adresa konania (mesto/sála) a iné detaily")
                
                if st.form_submit_button("Uložiť do kalendára"):
                    if not m:
                        st.warning("Zadajte aspoň názov alebo meno akcie.")
                    else:
                        nova_akcia = {
                            "id": str(datetime.now().timestamp()), 
                            "datum": str(d), 
                            "cas": t_time.strftime('%H:%M'),
                            "meno": m, 
                            "tel": tel_cislo,
                            "email": em_adresa,
                            "vypocitana_cena": dohodnuta_cena,
                            "detaily": det, 
                            "stav": "schvalene"
                        }
                        if supabase:
                            try:
                                supabase.table("kalendar").insert(nova_akcia).execute()
                                st.session_state['db_data'] = nacti_data()
                                st.success("Akcia bola úspešne pridaná do kalendára!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Chyba pridania na Supabase: {e}")

st.markdown(f'''
<div style="text-align:center; margin-top:50px; color:#ccc; line-height: 1.6;">
    <b>Podpora</b><br>
    <b>Tel. číslo:</b> 0944 757 122<br>
    <b>E-mail:</b> kollarstevo55@gmail.com
</div>
''', unsafe_allow_html=True)
