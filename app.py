"""Müşterilerin kullanacağı web arayüzü.  Çalıştırma:  streamlit run app.py"""
import datetime as dt
from html import escape

import streamlit as st

from bot import RESTORAN_ADI, RestoranBot
from menu import gunun_yemekleri
from ollama_mod import ollama_baglan

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
ORNEKLER = [
    "Asya mutfağından ne önerirsiniz?",
    "En ucuz yemek hangisi?",
    "250 gr tavuk kaç kalori?",
    "Vejetaryen ana yemekler",
]

st.set_page_config(page_title=RESTORAN_ADI, page_icon=":material/restaurant:", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:wght@400;700&display=swap');

:root { --ink:#26231f; --muted:#7b746a; --line:#e4ded3; --paper:#faf8f4; --accent:#8a3b24; }

#MainMenu, footer, [data-testid="stStatusWidget"], [data-testid="stDecoration"] { display:none; }
header[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:3rem; padding-bottom:6rem; max-width:720px; }

/* Başlık */
.masthead { border-bottom:1px solid var(--line); padding-bottom:1.1rem; margin-bottom:1.5rem; }
.masthead h1 { font-family:'Libre Caslon Text', Georgia, serif; font-weight:400; font-size:2.1rem;
               letter-spacing:-.01em; margin:0; padding:0; color:var(--ink); }
.masthead p { margin:.35rem 0 0; color:var(--muted); font-size:.95rem; }

/* Sohbet balonları: avatar yok, kullanıcı sağda */
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

/* Örnek sorular */
.hint { color:var(--muted); font-size:.85rem; margin:1.25rem 0 .4rem; text-transform:uppercase; letter-spacing:.06em; }
div[data-testid="stButton"] button[kind="secondary"] {
    background:transparent; border:1px solid var(--line); border-radius:999px; color:var(--ink);
    font-size:.9rem; padding:.3rem .9rem; }
div[data-testid="stButton"] button[kind="secondary"]:hover { border-color:var(--accent); color:var(--accent); }

/* Kenar çubuğu: günün menüsü */
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

if "bot" not in st.session_state:
    st.session_state.bot = RestoranBot(ollama=ollama_baglan())
    st.session_state.mesajlar = []

# ---- Kenar çubuğu: günün menüsü ----
bugun = dt.date.today()
with st.sidebar:
    satirlar = "".join(
        f'<div class="dish"><div class="dish-row"><span class="dish-name">{escape(y["ad"])}</span>'
        f'<span class="dish-price">{y["fiyat_tl"]} ₺</span></div>'
        f'<div class="dish-meta">{escape(y["kategori"])} · {y["kalori"]} kcal</div></div>'
        for y in gunun_yemekleri()
    )
    st.markdown(
        f'<p class="side-title">Günün menüsü</p>'
        f'<p class="side-date">{bugun.day} {AYLAR[bugun.month - 1]}, {GUNLER[bugun.weekday()]}</p>'
        f'{satirlar}'
        f'<p class="side-note">Kalori değerleri porsiyon başına yaklaşık değerlerdir.</p>',
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Yeni sohbet", type="tertiary"):
        st.session_state.clear()
        st.rerun()

# ---- Başlık ----
st.markdown(
    f'<div class="masthead"><h1>{escape(RESTORAN_ADI)}</h1>'
    f'<p>Menü, fiyatlar ve besin değerleri hakkında sorularınızı yanıtlıyoruz.</p></div>',
    unsafe_allow_html=True,
)


def gonder(soru: str):
    cevap = st.session_state.bot.cevapla(soru)
    st.session_state.mesajlar += [{"role": "user", "content": soru}, {"role": "assistant", "content": cevap}]


# ---- Boş ekran: örnek sorular ----
if not st.session_state.mesajlar:
    st.markdown('<p class="hint">Örnek sorular</p>', unsafe_allow_html=True)
    sutunlar = st.columns(2)
    for i, ornek in enumerate(ORNEKLER):
        if sutunlar[i % 2].button(ornek, key=f"ornek{i}", use_container_width=True):
            gonder(ornek)
            st.rerun()

# ---- Sohbet ----
for m in st.session_state.mesajlar:
    st.chat_message(m["role"]).markdown(m["content"])

if soru := st.chat_input("Bir soru yazın"):
    gonder(soru)
    st.rerun()
