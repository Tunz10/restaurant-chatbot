"""Menü verisi ve menü üzerinde çalışan fonksiyonlar.

Fiyat, kalori, protein ve sıralama gibi sayısal işlerin hepsi burada yapılır.
"""
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


def normalize(text: str) -> str:
    """Küçük harf, Türkçe karakterleri sadeleştir, noktalama işaretlerini boşluk yap."""
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
        adlar = [r["ad"], re.sub(r"\(.*?\)", "", r["ad"]), r["id"].replace("_", " ")]
        adlar += [a for a in r["diger_adlar"].split("|") if a]
        r["_adlar"] = sorted({normalize(a) for a in adlar if normalize(a)}, key=len, reverse=True)
    return rows


MENU = load_menu()
BY_ID = {r["id"]: r for r in MENU}


def besin(yemek: dict, gram=None) -> dict:
    """Verilen gramaj için (yoksa porsiyon için) kalori ve protein hesaplar."""
    gram = gram or yemek["porsiyon_gr"]
    return {
        "gram": gram,
        "kalori": round(yemek["kalori_100g"] * gram / 100),
        "protein": round(yemek["protein_100g"] * gram / 100, 1),
    }


def yemekleri_bul(metin: str):
    """Mesajda geçen menü yemeklerini bulur (en uzun ad önce eşleşir)."""
    n = f" {normalize(metin)} "
    adaylar = sorted(((ad, r) for r in MENU for ad in r["_adlar"]), key=lambda x: len(x[0]), reverse=True)
    bulunan = []
    for ad, r in adaylar:
        if f" {ad} " in n and r not in bulunan:
            bulunan.append(r)
            n = n.replace(f" {ad} ", " # ")  # aynı kelime ikinci kez eşleşmesin
    return bulunan


def ara(mutfak=None, mutfak_grubu=None, kategori=None, max_fiyat=None, max_kalori=None,
        vejetaryen=False, sirala="fiyat_artan"):
    """Menüyü filtreler ve sıralar."""
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
    """data/gunun_yemekleri.json'daki günün listesi; yoksa tarihe göre sabit bir seçim."""
    tarih = tarih or dt.date.today()
    gun = GUNLER[tarih.weekday()]
    secim = []
    if GUNUN_PATH.exists():
        plan = json.loads(GUNUN_PATH.read_text(encoding="utf-8"))
        secim = [BY_ID[i] for i in plan.get(gun, []) if i in BY_ID]
    if not secim:
        rnd = random.Random(tarih.toordinal())  # aynı gün hep aynı seçim
        for kat in ("Çorba", "Ana Yemek", "Ana Yemek", "Tatlı"):
            secim.append(rnd.choice([r for r in MENU if r["kategori"] == kat and r not in secim]))
    return secim
