"""Menu data and lookups. All prices, calories and sorting are computed here."""
import csv
import datetime as dt
import json
import random
import re
import unicodedata
from pathlib import Path

DATA = Path(__file__).parent / "data"
MENU_PATH = DATA / "menu.csv"
GUNUN_PATH = DATA / "gunun_yemekleri.json"

GUNLER = ["pazartesi", "sali", "carsamba", "persembe", "cuma", "cumartesi", "pazar"]
KATEGORI_SIRASI = ["Çorba", "Başlangıç", "Salata", "Ana Yemek", "Tatlı"]

EN = {
    "Çorba": "Soup", "Başlangıç": "Starter", "Salata": "Salad", "Ana Yemek": "Main course", "Tatlı": "Dessert",
    "Türk": "Turkish", "Asya": "Asian", "Akdeniz": "Mediterranean", "Amerikan": "American",
    "Japon": "Japanese", "Çin": "Chinese", "Tay": "Thai", "Hint": "Indian", "Kore": "Korean",
    "Vietnam": "Vietnamese", "İtalyan": "Italian", "Yunan": "Greek",
}


def cevir(deger: str, dil: str) -> str:
    return EN.get(deger, deger) if dil == "en" else deger


def ad(r: dict, dil: str) -> str:
    return r["ad_en"] if dil == "en" else r["ad"]


def icerik(r: dict, dil: str) -> str:
    return r["icerik_en"] if dil == "en" else r["icerik"]


def normalize(text: str) -> str:
    text = str(text).replace("I", "ı").replace("İ", "i").lower().replace("ı", "i")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_menu(path: Path = MENU_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["porsiyon_gr"] = int(r["porsiyon_gr"])
        r["fiyat_tl"] = int(r["fiyat_tl"])
        r["kalori_100g"] = float(r["kalori_100g"])
        r["protein_100g"] = float(r["protein_100g"])
        r["vejetaryen"] = r["vejetaryen"].strip().lower() == "evet"
        r["kalori"] = round(r["kalori_100g"] * r["porsiyon_gr"] / 100)
        r["protein"] = round(r["protein_100g"] * r["porsiyon_gr"] / 100)
        adlar = [r["ad"], r["ad_en"], r["id"].replace("_", " ")]
        adlar += [re.sub(r"\(.*?\)", "", a) for a in (r["ad"], r["ad_en"])]
        adlar += [a for a in r["diger_adlar"].split("|") if a]
        r["_adlar"] = sorted({normalize(a) for a in adlar if normalize(a)}, key=len, reverse=True)
    return rows


MENU = load_menu()
BY_ID = {r["id"]: r for r in MENU}


def besin(yemek: dict, gram=None) -> dict:
    gram = gram or yemek["porsiyon_gr"]
    return {
        "gram": gram,
        "kalori": round(yemek["kalori_100g"] * gram / 100),
        "protein": round(yemek["protein_100g"] * gram / 100, 1),
    }


def yemekleri_bul(metin: str):
    """Dishes mentioned in the text, longest name matched first."""
    n = f" {normalize(metin)} "
    adaylar = sorted(((a, r) for r in MENU for a in r["_adlar"]), key=lambda x: len(x[0]), reverse=True)
    bulunan = []
    for a, r in adaylar:
        if f" {a} " in n and r not in bulunan:
            bulunan.append(r)
            n = n.replace(f" {a} ", " # ")
    return bulunan


def ara(mutfak=None, mutfak_grubu=None, kategori=None, max_fiyat=None, max_kalori=None,
        vejetaryen=False, sirala="fiyat_artan"):
    rows = MENU
    if mutfak:
        rows = [r for r in rows if r["mutfak"] == mutfak]
    if mutfak_grubu:
        rows = [r for r in rows if r["mutfak_grubu"] == mutfak_grubu]
    if kategori:
        rows = [r for r in rows if r["kategori"] == kategori]
    if max_fiyat is not None:
        rows = [r for r in rows if r["fiyat_tl"] <= max_fiyat]
    if max_kalori is not None:
        rows = [r for r in rows if r["kalori"] <= max_kalori]
    if vejetaryen:
        rows = [r for r in rows if r["vejetaryen"]]
    anahtarlar = {
        "fiyat_artan": (lambda r: r["fiyat_tl"], False),
        "fiyat_azalan": (lambda r: r["fiyat_tl"], True),
        "kalori_artan": (lambda r: r["kalori"], False),
        "kalori_azalan": (lambda r: r["kalori"], True),
        "protein_azalan": (lambda r: r["protein"], True),
    }
    key, reverse = anahtarlar.get(sirala, anahtarlar["fiyat_artan"])
    return sorted(rows, key=key, reverse=reverse)


def gunun_yemekleri(tarih=None):
    """Today's dishes from gunun_yemekleri.json, or a fixed pick based on the date."""
    tarih = tarih or dt.date.today()
    gun = GUNLER[tarih.weekday()]
    secim = []
    if GUNUN_PATH.exists():
        plan = json.loads(GUNUN_PATH.read_text(encoding="utf-8"))
        secim = [BY_ID[i] for i in plan.get(gun, []) if i in BY_ID]
    if not secim:
        rnd = random.Random(tarih.toordinal())
        for kat in ("Çorba", "Ana Yemek", "Ana Yemek", "Tatlı"):
            secim.append(rnd.choice([r for r in MENU if r["kategori"] == kat and r not in secim]))
    return secim
