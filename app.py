import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime
import uuid
from PIL import Image
import io

# ── Konfiguráció
st.set_page_config(page_title="Ingatlan Nyilvántartó", page_icon="🏠", layout="wide")

SUPABASE_URL = "https://ckdfmzeanmnwwrkhhzop.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

TYPES = ['Ház', 'Lakás', 'Zártkerti ingatlan', 'Telek', 'Üzleti ingatlan', 'Egyéb']
SUBTYPES = {
    'Ház': ['Családi ház', 'Ikerház', 'Sorház', 'Nyaraló', 'Kastély', 'Tanya', 'Egyéb'],
    'Lakás': ['Panel lakás', 'Tégla lakás', 'Újépítésű lakás', 'Loft', 'Penthouse', 'Egyéb'],
    'Zártkerti ingatlan': ['Zártkerti kisház', 'Gazdasági épület', 'Présház', 'Pince', 'Egyéb'],
    'Telek': ['Építési telek', 'Zártkert', 'Mezőgazdasági terület', 'Erdő', 'Egyéb'],
    'Üzleti ingatlan': ['Iroda', 'Üzlethelyiség', 'Raktár', 'Ipari ingatlan', 'Vendéglátó egység', 'Egyéb'],
    'Egyéb': ['Egyéb'],
}
DOC_TYPES = ['Megbízási szerződés', 'Megtekintési nyilatkozat', 'Adatfelvételi lap',
             'Tulajdoni lap', 'Térképmásolat', 'Adatkezelési nyilatkozat', 'Egyéb']

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

def uid():
    return str(uuid.uuid4())[:8]

def now():
    return datetime.now().isoformat()

def fmt_ar(n):
    if not n:
        return '–'
    return f"{int(n):,} Ft".replace(',', ' ')

# ── Session state inicializálás
for k, v in [('user',''),('section','prop'),('prop_view','list'),
             ('prop_cur',None),('ker_view','list'),('ker_cur',None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Alap CSS
st.markdown("""
<style>
    div[data-testid="metric-container"] { background:#f8fafc; border:1px solid #e2e8f0; border-radius:.5rem; padding:.5rem; }
    .stTabs [data-baseweb="tab"] { font-size:.9rem; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════
# BEJELENTKEZÉS
# ══════════════════════════════════════
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center;padding:3rem 0 1rem'>
            <div style='font-size:4rem'>🏠</div>
            <h2 style='color:#1a3a6b'>Ingatlan Nyilvántartó</h2>
            <p style='color:#64748b'>Add meg a neved a belépéshez</p>
        </div>""", unsafe_allow_html=True)
        name = st.text_input("Neved", placeholder="Pl. Gyöngyi", label_visibility="collapsed")
        if st.button("Belépés →", use_container_width=True, type="primary"):
            if name.strip():
                st.session_state.user = name.strip()
                st.rerun()
    st.stop()

# ══════════════════════════════════════
# DB FÜGGVÉNYEK
# ══════════════════════════════════════

def load_props():
    try:
        return supabase.table('megbizasok').select('*').order('letrehozva', desc=True).execute().data or []
    except: return []

def load_prop(id):
    try:
        return supabase.table('megbizasok').select('*').eq('id', id).single().execute().data
    except: return None

def save_prop(data):
    try:
        supabase.table('megbizasok').upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"Mentési hiba: {e}"); return False

def del_prop(id):
    try:
        supabase.table('megbizasok').delete().eq('id', id).execute(); return True
    except: return False

def load_teendok(mid):
    try:
        return supabase.table('teendok').select('*').eq('megbizas_id', mid).order('letrehozva').execute().data or []
    except: return []

def save_teendo(data):
    try:
        supabase.table('teendok').upsert(data).execute(); return True
    except: return False

def del_teendo(id):
    try: supabase.table('teendok').delete().eq('id', id).execute()
    except: pass

def load_erdeklodok(mid):
    try:
        return supabase.table('erdeklodok').select('*').eq('megbizas_id', mid).order('letrehozva').execute().data or []
    except: return []

def save_erdeklodo(data):
    try:
        supabase.table('erdeklodok').upsert(data).execute(); return True
    except: return False

def del_erdeklodo(id):
    try: supabase.table('erdeklodok').delete().eq('id', id).execute()
    except: pass

def load_kers():
    try:
        return supabase.table('keresesi_megbizasok').select('*').order('letrehozva', desc=True).execute().data or []
    except: return []

def load_ker(id):
    try:
        return supabase.table('keresesi_megbizasok').select('*').eq('id', id).single().execute().data
    except: return None

def save_ker(data):
    try:
        supabase.table('keresesi_megbizasok').upsert(data).execute(); return True
    except Exception as e:
        st.error(f"Mentési hiba: {e}"); return False

def del_ker(id):
    try:
        supabase.table('keresesi_megbizasok').delete().eq('id', id).execute(); return True
    except: return False

def load_kiajanlottak(kid):
    try:
        return supabase.table('kiajanlottak').select('*').eq('ker_id', kid).order('letrehozva').execute().data or []
    except: return []

def save_kiajanlott(data):
    try:
        supabase.table('kiajanlottak').upsert(data).execute(); return True
    except: return False

def del_kiajanlott(id):
    try: supabase.table('kiajanlottak').delete().eq('id', id).execute()
    except: pass

def add_naplo(rekord_id, tabla, mit):
    try:
        supabase.table('naplo').insert({
            'id': uid(), 'tabla': tabla, 'rekord_id': rekord_id,
            'ki': st.session_state.user, 'mit': mit, 'datum': now()
        }).execute()
    except: pass

def load_naplo(rekord_id):
    try:
        return supabase.table('naplo').select('*').eq('rekord_id', rekord_id).order('datum', desc=True).execute().data or []
    except: return []

def upload_foto(file, prop_id):
    try:
        img = Image.open(file)
        if img.width > 900:
            r = 900 / img.width
            img = img.resize((900, int(img.height * r)), Image.LANCZOS)
        buf = io.BytesIO()
        img.convert('RGB').save(buf, format='JPEG', quality=78)
        buf.seek(0)
        fn = f"{prop_id}_{uid()}.jpg"
        supabase.storage.from_('fotok').upload(fn, buf.read(), {'content-type': 'image/jpeg'})
        return supabase.storage.from_('fotok').get_public_url(fn)
    except Exception as e:
        st.error(f"Fotó feltöltési hiba: {e}"); return None

# ══════════════════════════════════════
# NAVIGÁCIÓ
# ══════════════════════════════════════
c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 0.8])
with c1:
    st.markdown(f"### 🏠 Ingatlan Nyilvántartó &nbsp; <small style='color:#94a3b8'>👤 {st.session_state.user}</small>", unsafe_allow_html=True)
with c2:
    if st.button("📋 Eladási megbízások", use_container_width=True,
                 type="primary" if st.session_state.section == 'prop' else "secondary"):
        st.session_state.section = 'prop'; st.session_state.prop_view = 'list'; st.rerun()
with c3:
    if st.button("🔍 Keresési igények", use_container_width=True,
                 type="primary" if st.session_state.section == 'ker' else "secondary"):
        st.session_state.section = 'ker'; st.session_state.ker_view = 'list'; st.rerun()
with c4:
    if st.button("🚪 Kilépés"):
        st.session_state.user = ''; st.rerun()
st.divider()

# ══════════════════════════════════════
# ELADÁSI MEGBÍZÁSOK
# ══════════════════════════════════════
if st.session_state.section == 'prop':

    # ── LISTA
    if st.session_state.prop_view == 'list':
        props = load_props()
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Összes", len(props))
        c2.metric("Aktív", sum(1 for p in props if p.get('statusz')=='Aktiv'))
        c3.metric("Függőben", sum(1 for p in props if p.get('statusz')=='Fuggoben'))
        c4.metric("Lezárva", sum(1 for p in props if p.get('statusz')=='Lezarva'))

        cs, cf, cn = st.columns([2,1,1])
        with cs: search = st.text_input("Keresés", placeholder="Cím, tulajdonos, HRSZ...", label_visibility="collapsed")
        with cf: sf = st.selectbox("Szűrő", ["Minden","Aktív","Függőben","Lezárva"], label_visibility="collapsed")
        with cn:
            if st.button("➕ Új megbízás", type="primary", use_container_width=True):
                st.session_state.prop_view = 'new'; st.session_state.prop_cur = None; st.rerun()

        filt = props
        if search:
            q = search.lower()
            filt = [p for p in filt if any(q in str(p.get(f,'')).lower() for f in ['cim','tulajnev','hrsz','referens'])]
        sf_map = {"Aktív":"Aktiv","Függőben":"Fuggoben","Lezárva":"Lezarva"}
        if sf != "Minden": filt = [p for p in filt if p.get('statusz') == sf_map[sf]]

        if not filt:
            st.info("Még nincs megbízás." if not props else "Nincs találat.")
        else:
            cols = st.columns(3)
            for i, p in enumerate(filt):
                with cols[i % 3]:
                    with st.container(border=True):
                        if p.get('fofoto'):
                            st.image(p['fofoto'], use_container_width=True)
                        else:
                            st.markdown("<div style='height:140px;background:#f1f5f9;border-radius:.5rem;display:flex;align-items:center;justify-content:center;font-size:3rem'>🏠</div>", unsafe_allow_html=True)
                        sl = {'Aktiv':'🟢','Fuggoben':'🟡','Lezarva':'⚫'}.get(p.get('statusz',''),'')
                        st.markdown(f"**{p.get('cim','(Cím nélkül)')}**  {sl}")
                        st.caption(f"{p.get('tipus','')} · {p.get('altipus','')}")
                        if p.get('ar'): st.markdown(f"**{fmt_ar(p['ar'])}**")
                        r1,r2 = st.columns(2)
                        if p.get('alap'): r1.caption(f"📐 {p['alap']} m²")
                        if p.get('hrsz'): r2.caption(f"HRSZ: {p['hrsz']}")
                        if st.button("Megnyitás →", key=f"op_{p['id']}", use_container_width=True):
                            st.session_state.prop_cur = p['id']; st.session_state.prop_view = 'detail'; st.rerun()

    # ── ÚJ / SZERKESZTÉS
    elif st.session_state.prop_view in ['new','edit']:
        is_new = st.session_state.prop_view == 'new'
        prop = {} if is_new else (load_prop(st.session_state.prop_cur) or {})
        cb, ct = st.columns([1,5])
        with cb:
            if st.button("← Vissza"):
                st.session_state.prop_view = 'list' if is_new else 'detail'; st.rerun()
        with ct:
            st.subheader("🆕 Új eladási megbízás" if is_new else "✏️ Szerkesztés")

        with st.form("prop_form"):
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("**📍 Azonosítás**")
                cim = st.text_input("Cím *", value=prop.get('cim',''))
                tipus = st.selectbox("Típus", TYPES, index=TYPES.index(prop['tipus']) if prop.get('tipus') in TYPES else 0)
                subs = SUBTYPES.get(tipus,['Egyéb'])
                altipus = st.selectbox("Altípus", subs, index=subs.index(prop['altipus']) if prop.get('altipus') in subs else 0)
                hrsz = st.text_input("Helyrajzi szám (HRSZ)", value=prop.get('hrsz',''))
                statusz = st.selectbox("Státusz", ["Aktiv","Fuggoben","Lezarva"],
                    format_func=lambda x: {"Aktiv":"Aktív","Fuggoben":"Függőben","Lezarva":"Lezárva"}[x],
                    index=["Aktiv","Fuggoben","Lezarva"].index(prop.get('statusz','Aktiv')))
                referens = st.text_input("Referens", value=prop.get('referens', st.session_state.user))
                st.markdown("**💰 Ár & méretek**")
                ar = st.number_input("Kínálati ár (Ft)", value=float(prop.get('ar') or 0), min_value=0.0, step=100000.0)
                alap = st.number_input("Alapterület (m²)", value=float(prop.get('alap') or 0), min_value=0.0)
                telek = st.number_input("Telekterület (m²)", value=float(prop.get('telek') or 0), min_value=0.0)
                jutalek = st.number_input("Jutalék (%)", value=float(prop.get('jutalek') or 0), min_value=0.0, max_value=100.0, step=0.5)
            with c2:
                st.markdown("**👤 Tulajdonos**")
                tulajnev = st.text_input("Neve", value=prop.get('tulajnev',''))
                tulajtel = st.text_input("Telefon", value=prop.get('tulajtel',''))
                tulajemail = st.text_input("Email", value=prop.get('tulajemail',''))
                st.markdown("**📅 Megbízás**")
                kezdet = st.date_input("Kezdete", value=date.fromisoformat(prop['kezdet']) if prop.get('kezdet') else date.today())
                lejarat = st.date_input("Lejárata", value=date.fromisoformat(prop['lejarat']) if prop.get('lejarat') else date.today())

            st.markdown("**⚖️ Jogi megjegyzések**")
            jogi = st.text_area("Jogi megjegyzések", value=prop.get('jogimegjegyzes',''), height=80, label_visibility="collapsed")
            st.markdown("**📝 Hirdetési szöveg**")
            hirsz = st.text_area("Hirdetési szöveg", value=prop.get('hirsz',''), height=180, label_visibility="collapsed")
            st.markdown("**🔗 Hirdetési linkek** (soronként egy)")
            linkek_text = st.text_area("Hirdetési linkek", value='\n'.join(prop.get('hirdetesi_linkek') or []),
                height=80, label_visibility="collapsed", placeholder="https://ingatlanbazar.hu/...")
            st.markdown("**📸 Főfotó feltöltése** (kártyán megjelenő)")
            if prop.get('fofoto'):
                st.image(prop['fofoto'], width=200, caption="Jelenlegi főfotó")
            foto_file = st.file_uploader("Főfotó", type=['jpg','jpeg','png','webp'], label_visibility="collapsed")
            st.markdown("**🔗 További fotók — Google Drive linkek** (soronként egy)")
            drive_text = st.text_area("Drive linkek", value='\n'.join(prop.get('drive_linkek') or []),
                height=80, label_visibility="collapsed", placeholder="https://drive.google.com/...")
            st.markdown("**📄 Dokumentumok** (Típus: Link — soronként egy)")
            dok_lines = [f"{d.get('tipus','')}: {d.get('link','')}" for d in (prop.get('dokumentumok') or [])]
            dok_text = st.text_area("Dokumentumok", value='\n'.join(dok_lines), height=100, label_visibility="collapsed",
                placeholder="Megbízási szerződés: https://...\nTulajdoni lap: https://...")

            if st.form_submit_button("💾 Mentés", type="primary", use_container_width=True):
                if not cim.strip():
                    st.error("A cím megadása kötelező!")
                else:
                    linkek = [l.strip() for l in linkek_text.splitlines() if l.strip()]
                    drive_linkek = [l.strip() for l in drive_text.splitlines() if l.strip()]
                    dokumentumok = []
                    for line in dok_text.splitlines():
                        if ':' in line:
                            p2 = line.split(':',1)
                            dokumentumok.append({'tipus': p2[0].strip(), 'link': p2[1].strip()})
                    prop_id = prop.get('id') or uid()
                    fofoto_url = prop.get('fofoto','')
                    if foto_file:
                        url = upload_foto(foto_file, prop_id)
                        if url: fofoto_url = url
                    data = {
                        'id': prop_id, 'cim': cim, 'tipus': tipus, 'altipus': altipus, 'hrsz': hrsz,
                        'ar': ar or None, 'alap': alap or None, 'telek': telek or None,
                        'tulajnev': tulajnev, 'tulajtel': tulajtel, 'tulajemail': tulajemail,
                        'kezdet': kezdet.isoformat(), 'lejarat': lejarat.isoformat(),
                        'jutalek': jutalek or None, 'referens': referens, 'statusz': statusz,
                        'jogimegjegyzes': jogi, 'hirsz': hirsz, 'fofoto': fofoto_url,
                        'hirdetesi_linkek': linkek, 'drive_linkek': drive_linkek,
                        'dokumentumok': dokumentumok, 'letrehozva': prop.get('letrehozva') or now()
                    }
                    if save_prop(data):
                        add_naplo(prop_id, 'megbizasok', 'Megbízás létrehozva' if is_new else 'Módosítva')
                        st.success("✅ Mentve!")
                        st.session_state.prop_cur = prop_id; st.session_state.prop_view = 'detail'; st.rerun()

    # ── RÉSZLETES NÉZET
    elif st.session_state.prop_view == 'detail':
        prop = load_prop(st.session_state.prop_cur)
        if not prop:
            st.session_state.prop_view = 'list'; st.rerun()

        cb, ct, ce, cd = st.columns([1,4,1,1])
        with cb:
            if st.button("← Lista"): st.session_state.prop_view = 'list'; st.rerun()
        with ct:
            sl = {'Aktiv':'🟢 Aktív','Fuggoben':'🟡 Függőben','Lezarva':'⚫ Lezárva'}.get(prop.get('statusz',''),'')
            st.subheader(f"{prop.get('cim','')}  {sl}")
        with ce:
            if st.button("✏️ Szerkesztés", use_container_width=True):
                st.session_state.prop_view = 'edit'; st.rerun()
        with cd:
            if st.button("🗑️ Törlés", use_container_width=True):
                if del_prop(prop['id']):
                    st.session_state.prop_view = 'list'; st.rerun()

        if prop.get('fofoto'): st.image(prop['fofoto'], width=350)

        c1,c2,c3,c4,c5,c6 = st.columns(6)
        for col,(l,v) in zip([c1,c2,c3,c4,c5,c6],[
            ("💰 Ár",fmt_ar(prop.get('ar'))),("📐 Alap",f"{prop['alap']} m²" if prop.get('alap') else '–'),
            ("🌿 Telek",f"{prop['telek']} m²" if prop.get('telek') else '–'),
            ("💼 Jutalék",f"{prop['jutalek']}%" if prop.get('jutalek') else '–'),
            ("👤 Referens",prop.get('referens') or '–'),("📍 HRSZ",prop.get('hrsz') or '–')]):
            col.metric(l,v)

        t1,t2,t3,t4,t5,t6 = st.tabs(["📍 Alapadatok","✅ Teendők","👥 Érdeklődők","📝 Hirdetés","📄 Dokumentumok","📋 Napló"])

        with t1:
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("**👤 Tulajdonos**")
                for l,v in [("Név",prop.get('tulajnev')),("Telefon",prop.get('tulajtel')),("Email",prop.get('tulajemail')),
                            ("Típus / Altípus",f"{prop.get('tipus','')} / {prop.get('altipus','')}"),
                            ("Kezdet",prop.get('kezdet')),("Lejárat",prop.get('lejarat'))]:
                    st.write(f"{l}: **{v or '–'}**")
            with c2:
                st.markdown("**⚖️ Jogi megjegyzések**")
                st.info(prop.get('jogimegjegyzes') or '(Nincs bejegyzés)')

        with t2:
            teendok = load_teendok(prop['id'])
            kesz = sum(1 for t in teendok if t.get('kesz'))
            st.caption(f"{kesz}/{len(teendok)} teljesítve")
            for t in teendok:
                cc,cs2,cd2,cx = st.columns([0.5,3,1.5,0.5])
                with cc:
                    nk = st.checkbox("", value=t.get('kesz',False), key=f"t_{t['id']}")
                    if nk != t.get('kesz',False):
                        save_teendo({**t,'kesz':nk})
                        add_naplo(prop['id'],'teendok',f"{'✅ Kész' if nk else '🔄 Újranyitva'}: {t.get('szoveg','')}")
                        st.rerun()
                with cs2: st.write(f"~~{t.get('szoveg','')}~~" if t.get('kesz') else t.get('szoveg',''))
                with cd2: st.caption(t.get('datum') or '')
                with cx:
                    if st.button("✕", key=f"dt_{t['id']}"):
                        del_teendo(t['id']); st.rerun()
            st.divider()
            with st.form("new_t"):
                ca,cb2,cc2 = st.columns([3,1.5,1])
                with ca: ns = st.text_input("Teendő", label_visibility="collapsed", placeholder="Teendő leírása...")
                with cb2: nd = st.date_input("Határidő", value=date.today(), label_visibility="collapsed")
                with cc2:
                    if st.form_submit_button("➕"):
                        if ns.strip():
                            save_teendo({'id':uid(),'megbizas_id':prop['id'],'szoveg':ns,'datum':nd.isoformat(),'kesz':False,'letrehozva':now()})
                            st.rerun()

        with t3:
            elist = load_erdeklodok(prop['id'])
            for e in elist:
                with st.expander(f"👤 {e.get('nev') or '(Névtelen)'}  📞 {e.get('tel') or ''}"):
                    c1,c2 = st.columns(2)
                    with c1:
                        nn = st.text_input("Név", value=e.get('nev',''), key=f"en_{e['id']}")
                        nt = st.text_input("Telefon", value=e.get('tel',''), key=f"et_{e['id']}")
                        ne = st.text_input("Email", value=e.get('email',''), key=f"ee_{e['id']}")
                    with c2:
                        nk2 = st.text_input("Mit keres?", value=e.get('keres',''), key=f"ek_{e['id']}")
                        nm = st.text_input("Megjegyzés", value=e.get('megjegyzes',''), key=f"em_{e['id']}")
                    cs2,ck,cdel = st.columns(3)
                    with cs2:
                        if st.button("💾 Mentés", key=f"se_{e['id']}"):
                            save_erdeklodo({**e,'nev':nn,'tel':nt,'email':ne,'keres':nk2,'megjegyzes':nm})
                            add_naplo(prop['id'],'erdeklodok',f"Érdeklődő módosítva: {nn}"); st.success("Mentve!")
                    with ck:
                        if st.button("🔍 Keresési megbízás", key=f"ke_{e['id']}"):
                            kid = uid()
                            save_ker({'id':kid,'ugyfel_nev':nn,'ugyfel_tel':nt,'ugyfel_email':ne,
                                'referens':st.session_state.user,'statusz':'Aktiv','datum':date.today().isoformat(),
                                'megjegyzes':nk2,'forrasprop_id':prop['id'],'letrehozva':now()})
                            add_naplo(kid,'keresesi_megbizasok',f"Létrehozva érdeklődőből: {nn}")
                            st.session_state.section='ker'; st.session_state.ker_cur=kid
                            st.session_state.ker_view='detail'; st.rerun()
                    with cdel:
                        if st.button("🗑️ Törlés", key=f"de_{e['id']}"):
                            del_erdeklodo(e['id']); st.rerun()
            st.divider()
            with st.form("new_e"):
                st.markdown("**+ Új érdeklődő**")
                c1,c2 = st.columns(2)
                with c1:
                    nn2 = st.text_input("Név"); nt2 = st.text_input("Telefon"); ne2 = st.text_input("Email")
                with c2:
                    nk3 = st.text_input("Mit keres?"); nm2 = st.text_input("Megjegyzés")
                if st.form_submit_button("➕ Érdeklődő hozzáadása"):
                    if nn2.strip() or nt2.strip():
                        save_erdeklodo({'id':uid(),'megbizas_id':prop['id'],'nev':nn2,'tel':nt2,'email':ne2,
                            'keres':nk3,'megjegyzes':nm2,'letrehozva':now()})
                        add_naplo(prop['id'],'erdeklodok',f"Érdeklődő felvéve: {nn2}"); st.rerun()

        with t4:
            if prop.get('hirsz'):
                st.markdown("**📝 Hirdetési szöveg**")
                st.text_area("", value=prop['hirsz'], height=300, disabled=True, label_visibility="collapsed")
            if prop.get('hirdetesi_linkek'):
                st.markdown("**🔗 Hirdetési linkek**")
                for l in prop['hirdetesi_linkek']: st.markdown(f"[🔗 {l}]({l})")
            if prop.get('drive_linkek'):
                st.markdown("**📸 Drive fotó linkek**")
                for l in prop['drive_linkek']: st.markdown(f"[📸 {l}]({l})")

        with t5:
            docs = prop.get('dokumentumok') or []
            if not docs: st.caption("Nincs rögzített dokumentum")
            for d in docs:
                c1,c2 = st.columns([1,3])
                c1.markdown(f"**{d.get('tipus','')}**")
                if d.get('link'): c2.markdown(f"[🔗 Megnyitás]({d['link']})")

        with t6:
            naplo = load_naplo(prop['id'])
            if not naplo: st.caption("Nincs napló bejegyzés")
            for n in naplo:
                st.markdown(f"**{n.get('ki','')}** — {n.get('mit','')}  <small style='color:#94a3b8'>{str(n.get('datum',''))[:16]}</small>", unsafe_allow_html=True)
                st.divider()

# ══════════════════════════════════════
# KERESÉSI IGÉNYEK
# ══════════════════════════════════════
elif st.session_state.section == 'ker':

    if st.session_state.ker_view == 'list':
        kers = load_kers()
        c1,c2,c3 = st.columns(3)
        c1.metric("Összes", len(kers))
        c2.metric("Aktív", sum(1 for k in kers if k.get('statusz')=='Aktiv'))
        c3.metric("Lezárva", sum(1 for k in kers if k.get('statusz')=='Lezarva'))

        cs,cf,cn = st.columns([2,1,1])
        with cs: ks = st.text_input("Keresés", placeholder="Név, telefon, helyszín...", label_visibility="collapsed")
        with cf: kf = st.selectbox("Szűrő", ["Minden","Aktív","Lezárva"], label_visibility="collapsed")
        with cn:
            if st.button("➕ Új keresési megbízás", type="primary", use_container_width=True):
                st.session_state.ker_view = 'new'; st.rerun()

        filt = kers
        if ks:
            q = ks.lower()
            filt = [k for k in filt if any(q in str(k.get(f,'')).lower() for f in ['ugyfel_nev','ugyfel_tel','helyszin','referens'])]
        if kf != "Minden": filt = [k for k in filt if k.get('statusz') == ('Aktiv' if kf=='Aktív' else 'Lezarva')]

        if not filt: st.info("Még nincs keresési megbízás." if not kers else "Nincs találat.")
        for k in filt:
            with st.container(border=True):
                c1,c2,c3 = st.columns([3,2,1])
                with c1:
                    sl = {'Aktiv':'🟢','Lezarva':'⚫'}.get(k.get('statusz',''),'')
                    st.markdown(f"**{k.get('ugyfel_nev','(Névtelen)')}** {sl}")
                    if k.get('ugyfel_tel'): st.caption(f"📞 {k['ugyfel_tel']}")
                with c2:
                    if k.get('tipus'): st.caption(f"🏠 {k['tipus']}{' / '+k['altipus'] if k.get('altipus') else ''}")
                    if k.get('helyszin'): st.caption(f"📍 {k['helyszin']}")
                    if k.get('ar_tol') or k.get('ar_ig'): st.caption(f"💰 {fmt_ar(k.get('ar_tol'))} – {fmt_ar(k.get('ar_ig'))}")
                with c3:
                    kai = load_kiajanlottak(k['id'])
                    if kai: st.caption(f"🏠 {len(kai)} kiajánlott")
                    if st.button("Megnyitás →", key=f"ok_{k['id']}", use_container_width=True):
                        st.session_state.ker_cur = k['id']; st.session_state.ker_view = 'detail'; st.rerun()

    elif st.session_state.ker_view in ['new','edit']:
        is_new = st.session_state.ker_view == 'new'
        ker = {} if is_new else (load_ker(st.session_state.ker_cur) or {})
        cb,ct = st.columns([1,5])
        with cb:
            if st.button("← Vissza"): st.session_state.ker_view = 'list' if is_new else 'detail'; st.rerun()
        with ct: st.subheader("🆕 Új keresési megbízás" if is_new else "✏️ Szerkesztés")

        with st.form("ker_form"):
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("**👤 Ügyfél adatai**")
                ugyfel_nev = st.text_input("Ügyfél neve *", value=ker.get('ugyfel_nev',''))
                ugyfel_tel = st.text_input("Telefon", value=ker.get('ugyfel_tel',''))
                ugyfel_email = st.text_input("Email", value=ker.get('ugyfel_email',''))
                referens = st.text_input("Referens", value=ker.get('referens', st.session_state.user))
                statusz = st.selectbox("Státusz", ["Aktiv","Lezarva"],
                    format_func=lambda x: {"Aktiv":"Aktív","Lezarva":"Lezárva"}[x],
                    index=["Aktiv","Lezarva"].index(ker.get('statusz','Aktiv')))
                datum = st.date_input("Dátum", value=date.fromisoformat(ker['datum']) if ker.get('datum') else date.today())
            with c2:
                st.markdown("**🔍 Keresési paraméterek**")
                all_t = ['(Nem meghatározott)'] + TYPES
                tipus = st.selectbox("Keresett típus", all_t, index=all_t.index(ker['tipus']) if ker.get('tipus') in all_t else 0)
                if tipus in SUBTYPES:
                    subs2 = ['(Bármely)'] + SUBTYPES[tipus]
                    altipus = st.selectbox("Altípus", subs2, index=subs2.index(ker['altipus']) if ker.get('altipus') in subs2 else 0)
                else: altipus = ''
                helyszin = st.text_input("Helyszín / körzet", value=ker.get('helyszin',''))
                ca,cb2 = st.columns(2)
                with ca:
                    ar_tol = st.number_input("Ár min (Ft)", value=float(ker.get('ar_tol') or 0), min_value=0.0, step=100000.0)
                    alap_tol = st.number_input("Alap min (m²)", value=float(ker.get('alap_tol') or 0), min_value=0.0)
                with cb2:
                    ar_ig = st.number_input("Ár max (Ft)", value=float(ker.get('ar_ig') or 0), min_value=0.0, step=100000.0)
                    alap_ig = st.number_input("Alap max (m²)", value=float(ker.get('alap_ig') or 0), min_value=0.0)
            st.markdown("**📝 Megjegyzések / egyéb követelmények**")
            megjegyzes = st.text_area("", value=ker.get('megjegyzes',''), height=120, label_visibility="collapsed")
            if st.form_submit_button("💾 Mentés", type="primary", use_container_width=True):
                if not ugyfel_nev.strip(): st.error("Az ügyfél neve kötelező!")
                else:
                    kid = ker.get('id') or uid()
                    data = {'id':kid,'ugyfel_nev':ugyfel_nev,'ugyfel_tel':ugyfel_tel,'ugyfel_email':ugyfel_email,
                        'referens':referens,'statusz':statusz,'datum':datum.isoformat(),
                        'tipus':tipus if tipus!='(Nem meghatározott)' else '',
                        'altipus':altipus if altipus!='(Bármely)' else '',
                        'helyszin':helyszin,'ar_tol':ar_tol or None,'ar_ig':ar_ig or None,
                        'alap_tol':alap_tol or None,'alap_ig':alap_ig or None,
                        'megjegyzes':megjegyzes,'forrasprop_id':ker.get('forrasprop_id',''),
                        'letrehozva':ker.get('letrehozva') or now()}
                    if save_ker(data):
                        add_naplo(kid,'keresesi_megbizasok','Létrehozva' if is_new else 'Módosítva')
                        st.session_state.ker_cur = kid; st.session_state.ker_view = 'detail'; st.rerun()

    elif st.session_state.ker_view == 'detail':
        ker = load_ker(st.session_state.ker_cur)
        if not ker: st.session_state.ker_view = 'list'; st.rerun()

        cb,ct,ce,cd = st.columns([1,4,1,1])
        with cb:
            if st.button("← Lista"): st.session_state.ker_view = 'list'; st.rerun()
        with ct:
            sl = {'Aktiv':'🟢 Aktív','Lezarva':'⚫ Lezárva'}.get(ker.get('statusz',''),'')
            st.subheader(f"{ker.get('ugyfel_nev','(Névtelen)')}  {sl}")
        with ce:
            if st.button("✏️ Szerkesztés", use_container_width=True):
                st.session_state.ker_view = 'edit'; st.rerun()
        with cd:
            if st.button("🗑️ Törlés", use_container_width=True):
                del_ker(ker['id']); st.session_state.ker_view = 'list'; st.rerun()

        if ker.get('forrasprop_id'):
            src = load_prop(ker['forrasprop_id'])
            if src: st.info(f"🔗 Forrás ingatlan: **{src.get('cim','')}**")

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("📞 Telefon", ker.get('ugyfel_tel') or '–')
        c2.metric("🏠 Típus", ker.get('tipus') or '–')
        c3.metric("📍 Helyszín", ker.get('helyszin') or '–')
        c4.metric("👤 Referens", ker.get('referens') or '–')
        if ker.get('ar_tol') or ker.get('ar_ig'):
            st.caption(f"💰 {fmt_ar(ker.get('ar_tol'))} – {fmt_ar(ker.get('ar_ig'))}")
        if ker.get('alap_tol') or ker.get('alap_ig'):
            st.caption(f"📐 {ker.get('alap_tol','?')} – {ker.get('alap_ig','?')} m²")

        kt1,kt2,kt3 = st.tabs(["👤 Alapadatok","🏠 Kiajánlottak","📋 Napló"])

        with kt1:
            st.write(f"Email: **{ker.get('ugyfel_email') or '–'}**")
            st.write(f"Dátum: **{ker.get('datum') or '–'}**")
            if ker.get('megjegyzes'):
                st.markdown("**📝 Megjegyzések**"); st.info(ker['megjegyzes'])

        with kt2:
            props_aktiv = [p for p in load_props() if p.get('statusz')=='Aktiv']
            kiajanlottak = load_kiajanlottak(ker['id'])
            for ki in kiajanlottak:
                cim_label = ki.get('cim') or next((p['cim'] for p in props_aktiv if p['id']==ki.get('prop_id')),'(névtelen)')
                with st.expander(f"🏠 {cim_label}"):
                    tip = st.radio("Forrás", ['saját','külső'],
                        index=0 if ki.get('tipus','saját')=='saját' else 1, key=f"kit_{ki['id']}", horizontal=True)
                    if tip == 'saját':
                        opts = {p['id']:f"{p['cim']} – {fmt_ar(p.get('ar'))}" for p in props_aktiv}
                        opts[''] = '– Válassz –'
                        sel = st.selectbox("Saját ingatlan", list(opts.keys()),
                            format_func=lambda x: opts.get(x,''),
                            index=list(opts.keys()).index(ki.get('prop_id','')) if ki.get('prop_id') in opts else 0,
                            key=f"kip_{ki['id']}")
                        uj_cim = next((p['cim'] for p in props_aktiv if p['id']==sel),'')
                    else:
                        sel = ''
                        uj_cim = st.text_input("Cím", value=ki.get('cim',''), key=f"kic_{ki['id']}")
                    c1,c2 = st.columns(2)
                    with c1:
                        uj_kozv = st.text_input("Közvetítő", value=ki.get('kozvetito',''), key=f"kikv_{ki['id']}")
                        uj_jut = st.text_input("Jutalék megállapodás", value=ki.get('jutalek',''), key=f"kij_{ki['id']}")
                    with c2:
                        uj_link = st.text_input("Link", value=ki.get('link',''), key=f"kil_{ki['id']}")
                        uj_dat = st.date_input("Dátum", value=date.fromisoformat(ki['datum']) if ki.get('datum') else date.today(), key=f"kid_{ki['id']}")
                    uj_megj = st.text_input("Megjegyzés", value=ki.get('megjegyzes',''), key=f"kim_{ki['id']}")
                    cs2,cdel = st.columns(2)
                    with cs2:
                        if st.button("💾 Mentés", key=f"ski_{ki['id']}"):
                            save_kiajanlott({**ki,'tipus':tip,'prop_id':sel,'cim':uj_cim,
                                'link':uj_link,'kozvetito':uj_kozv,'jutalek':uj_jut,
                                'megjegyzes':uj_megj,'datum':uj_dat.isoformat()})
                            add_naplo(ker['id'],'kiajanlottak',f"Kiajánlott: {uj_cim}"); st.success("Mentve!")
                    with cdel:
                        if st.button("🗑️ Törlés", key=f"dki_{ki['id']}"):
                            del_kiajanlott(ki['id']); st.rerun()
            st.divider()
            if st.button("➕ Kiajánlott ingatlan hozzáadása", type="primary"):
                save_kiajanlott({'id':uid(),'ker_id':ker['id'],'tipus':'saját','prop_id':'','cim':'',
                    'link':'','kozvetito':'','jutalek':'','megjegyzes':'','datum':date.today().isoformat(),'letrehozva':now()})
                st.rerun()

        with kt3:
            naplo = load_naplo(ker['id'])
            if not naplo: st.caption("Nincs napló bejegyzés")
            for n in naplo:
                st.markdown(f"**{n.get('ki','')}** — {n.get('mit','')}  <small style='color:#94a3b8'>{str(n.get('datum',''))[:16]}</small>", unsafe_allow_html=True)
                st.divider()
