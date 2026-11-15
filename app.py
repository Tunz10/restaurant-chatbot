"""Customer-facing web UI. Run: streamlit run app.py"""
import datetime as dt
from html import escape

import streamlit as st

from bot import RESTORAN_ADI, RestoranBot
from menu import ad, cevir, gunun_yemekleri
from ollama_mod import ollama_baglan

UI = {
    "tr": {
        "alt": "Menü, fiyatlar ve besin değerleri hakkında sorularınızı yanıtlıyoruz.",
        "gunun": "Günün menüsü",
        "not": "Kalori değerleri porsiyon başına yaklaşık değerlerdir.",
        "yeni": "Yeni sohbet",
        "ornek_baslik": "Örnek sorular",
        "giris": "Bir soru yazın",
        "aylar": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
                  "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
        "gunler": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"],
        "ornekler": ["Asya mutfağından ne önerirsiniz?", "En ucuz yemek hangisi?",
                     "250 gr tavuk kaç kalori?", "Vejetaryen ana yemekler"],
    },
    "en": {
        "alt": "Ask us about the menu, prices and nutrition.",
        "gunun": "Today's menu",
        "not": "Calories are approximate, per portion.",
        "yeni": "New chat",
        "ornek_baslik": "Try asking",
        "giris": "Ask a question",
        "aylar": ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"],
        "gunler": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "ornekler": ["What do you recommend from Asian cuisine?", "What is the cheapest dish?",
                     "How many calories in 250 g chicken?", "Vegetarian main courses"],
    },
}

st.set_page_config(page_title=RESTORAN_ADI, page_icon=":material/restaurant:", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:wght@400;700&display=swap');

:root { --ink:#26231f; --muted:#7b746a; --line:#e4ded3; --paper:#faf8f4; --accent:#8a3b24; }

#MainMenu, footer, [data-testid="stStatusWidget"], [data-testid="stDecoration"] { display:none; }
header[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:3rem; padding-bottom:6rem; max-width:720px; }

.masthead { padding-bottom:.2rem; }
.rule { border-bottom:1px solid var(--line); margin:.6rem 0 1.5rem; }
.masthead h1 { font-family:'Libre Caslon Text', Georgia, serif; font-weight:400; font-size:2.1rem;
               letter-spacing:-.01em; margin:0; padding:0; color:var(--ink); }
.masthead p { margin:.35rem 0 0; color:var(--muted); font-size:.95rem; }

[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { display:none; }
[data-testid="stChatMessage"] { background:transparent; padding:.25rem 0; gap:0; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { justify-content:flex-end; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background:#efe9df; border-radius:14px 14px 4px 14px; padding:.55rem .9rem; max-width:80%; flex:0 1 auto;
    margin:0 0 0 auto !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
    padding:.2rem 0; }
[data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li { font-size:.98rem; line-height:1.6; }
[data-testid="stChatMessageContent"] ul { padding-left:1.1rem; margin:.2rem 0 .6rem; }

.hint { color:var(--muted); font-size:.85rem; margin:1.25rem 0 .4rem; text-transform:uppercase; letter-spacing:.06em; }
div[data-testid="stButton"] button[kind="secondary"] {
    background:transparent; border:1px solid var(--line); border-radius:999px; color:var(--ink);
    font-size:.9rem; padding:.3rem .9rem; }
div[data-testid="stButton"] button[kind="secondary"]:hover { border-color:var(--accent); color:var(--accent); }

section[data-testid="stSidebar"] { background:#f1ede5; border-right:1px solid var(--line); }
.side-title { font-family:'Libre Caslon Text', Georgia, serif; font-size:1.25rem; margin:0; color:var(--ink); }
.side-date { color:var(--muted); font-size:.85rem; margin:.15rem 0 1rem; }
.dish { padding:.7rem 0; border-top:1px solid var(--line); }
.dish:last-child { border-bottom:1px solid var(--line); }
.dish-row { display:flex; justify-content:space-between; gap:.75rem; align-items:baseline; }
.dish-name { color:var(--ink); font-weight:500; }
.dish-price { color:var(--ink); font-variant-numeric:tabular-nums; white-space:nowrap; }
.dish-meta { color:var(--muted); font-size:.82rem; margin-top:.1rem; }
section[data-testid="stSidebar"] p.side-note { color:var(--muted); font-size:.78rem; margin-top:1rem; line-height:1.5; }
</style>
""", unsafe_allow_html=True)

st.session_state.setdefault("dil", "tr")
if "bot" not in st.session_state:
    st.session_state.bot = RestoranBot(ollama=ollama_baglan(), dil=st.session_state.dil)
    st.session_state.mesajlar = []


def dil_degisti():
    if st.session_state.dil_secimi:
        st.session_state.dil = st.session_state.dil_secimi.lower()
        st.session_state.bot.dil = st.session_state.dil


st.session_state.dil_secimi = st.session_state.dil.upper()
baslik, secici = st.columns([4, 1], vertical_alignment="bottom")
with secici:
    st.segmented_control("Dil / Language", ["TR", "EN"], label_visibility="collapsed",
                         key="dil_secimi", on_change=dil_degisti)
dil = st.session_state.dil
t = UI[dil]

with baslik:
    st.markdown(f'<div class="masthead"><h1>{escape(RESTORAN_ADI)}</h1><p>{t["alt"]}</p></div>',
                unsafe_allow_html=True)
st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

bugun = dt.date.today()
tarih = (f'{bugun.day} {t["aylar"][bugun.month - 1]}, {t["gunler"][bugun.weekday()]}' if dil == "tr"
         else f'{t["gunler"][bugun.weekday()]}, {bugun.day} {t["aylar"][bugun.month - 1]}')
with st.sidebar:
    satirlar = "".join(
        f'<div class="dish"><div class="dish-row"><span class="dish-name">{escape(ad(y, dil))}</span>'
        f'<span class="dish-price">{y["fiyat_tl"]} ₺</span></div>'
        f'<div class="dish-meta">{escape(cevir(y["kategori"], dil))} · {y["kalori"]} kcal</div></div>'
        for y in gunun_yemekleri()
    )
    st.markdown(f'<p class="side-title">{t["gunun"]}</p><p class="side-date">{tarih}</p>{satirlar}'
                f'<p class="side-note">{t["not"]}</p>', unsafe_allow_html=True)
    st.write("")
    if st.button(t["yeni"], type="tertiary"):
        dil_sakla = st.session_state.dil
        st.session_state.clear()
        st.session_state.dil = dil_sakla
        st.rerun()


def gonder(soru: str):
    cevap = st.session_state.bot.cevapla(soru)
    st.session_state.dil = st.session_state.bot.dil
    st.session_state.mesajlar += [{"role": "user", "content": soru}, {"role": "assistant", "content": cevap}]


if not st.session_state.mesajlar:
    st.markdown(f'<p class="hint">{t["ornek_baslik"]}</p>', unsafe_allow_html=True)
    sutunlar = st.columns(2)
    for i, ornek in enumerate(t["ornekler"]):
        if sutunlar[i % 2].button(ornek, key=f"ornek{dil}{i}", use_container_width=True):
            gonder(ornek)
            st.rerun()

for m in st.session_state.mesajlar:
    st.chat_message(m["role"]).markdown(m["content"])

if soru := st.chat_input(t["giris"]):
    gonder(soru)
    st.rerun()
