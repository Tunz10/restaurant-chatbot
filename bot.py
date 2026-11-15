"""Kural tabanlı restoran chatbotu (ücretsiz, internet veya API gerektirmez).

İsteğe bağlı: bilgisayarınızda Ollama çalışıyorsa, kuralların anlamadığı mesajlar
yerel bir modele sorulur (bkz. ollama_mod.py). Ollama yoksa bot yine çalışır.
"""
import re

from menu import KATEGORI_SIRASI, MENU, ara, besin, gunun_yemekleri, normalize, yemekleri_bul

RESTORAN_ADI = "Lezzet Durağı"

# ---- Anahtar kelimeler (normalize edilmiş metin üzerinde aranır) ----
MUTFAKLAR = [  # (regex, alan, değer)
    (r"\b(asya|asyali|uzak ?dogu)", "mutfak_grubu", "Asya"),
    (r"\bakdeniz", "mutfak_grubu", "Akdeniz"),
    (r"\bamerika", "mutfak_grubu", "Amerikan"),
    (r"\bturk\b|\bturk (mutfa|yemek)", "mutfak_grubu", "Türk"),
    (r"\bjapon", "mutfak", "Japon"),
    (r"\bcin\b|\bcin (mutfa|yemek)", "mutfak", "Çin"),
    (r"\btay\b|\btayland", "mutfak", "Tay"),
    (r"\bhint", "mutfak", "Hint"),
    (r"\bkore", "mutfak", "Kore"),
    (r"\bvietnam", "mutfak", "Vietnam"),
    (r"\bitalya", "mutfak", "İtalyan"),
    (r"\byunan", "mutfak", "Yunan"),
]
KATEGORILER = [
    (r"\bcorba", "Çorba"),
    (r"\btatli", "Tatlı"),
    (r"\bsalata", "Salata"),
    (r"\b(baslangic|aperatif|atistirma|meze)", "Başlangıç"),
    (r"\bana yemek", "Ana Yemek"),
]
KONU_DISI = (  # bunlar geçerse menü sorusu sayılmaz
    r"\b(tarif|nasil yapilir|hava\b|kod|python|java|program|odev|futbol|mac|siyaset|"
    r"film|dizi|sarki|borsa|bitcoin|kripto|doviz|telefon|araba|bilgisayar|haber|fikra|siir)"
)

DESEN = {
    "selam": r"\b(merhaba|selam|selamlar|iyi gunler|iyi aksamlar|gunaydin|hey|slm)\b",
    "tesekkur": r"\b(tesekkur|sagol|sag ol|eyvallah|tsk)",
    "veda": r"\b(gorusuruz|hosca kal|iyi geceler|bye)\b",
    "ucuz": r"\b(ucuz|uygun fiyat|ekonomik|hesapli)",
    "pahali": r"\b(pahali|en luks)",
    "hafif": r"\b(hafif|dusuk kalori|az kalori|diyet|en az kalori)",
    "kalorili": r"\b(en kalorili|yuksek kalori|en cok kalori|en fazla kalori|doyurucu)",
    "protein": r"\b(yuksek protein|en cok protein|en fazla protein|proteinli|protein (orani )?yuksek|en proteinli)",
    "vejetaryen": r"\b(vejetaryen|vejeteryan|vegan|etsiz|et yemiyorum|et yemeyen)",
    "besin": r"\b(kalori|kcal|protein|besin degeri|kac gram)",
    "fiyat": r"\b(fiyat|kac para|kac tl|kac lira|ne kadar|ucret)",
    "oneri": r"\b(oner|tavsiye|ne yesem|ne yiyeyim|ne yiyebilirim|ne yiyelim|ne alsam|ne alayim|aciktim)",
    "gunun": r"\b(gunun|bugun|gunluk)",
    "menu": r"\b(menu|neler var|ne var|yemekler|listele|cesit)",
    "mutfak_listesi": r"\b(hangi mutfak|mutfaklar|hangi ulke)",
    "baska": r"\b(baska|daha fazla|devam|diger)",
    "en": r"\ben\b",
}


def _tl(x):
    return f"{x} ₺"


def _g(x):
    return f"{x:.0f}" if float(x).is_integer() else f"{x:.1f}"


def _satir(r):
    return f"- **{r['ad']}** — {_tl(r['fiyat_tl'])} · {r['kalori']} kcal · {r['protein']} g protein"


def _liste(rows):
    return "\n".join(_satir(r) for r in rows)


def konu_disi_cevap():
    return ("Üzgünüm, bu konuda yetkin değilim; yalnızca menümüz, fiyatlarımız ve kaloriler "
            "hakkında yardımcı olabilirim. 😊\n\nSize günün yemeklerini önerebilirim:\n\n"
            + _liste(gunun_yemekleri()))


def sayilari_ayikla(n: str):
    """Gram, kalori sınırı ve bütçeyi mesajdan ayırır."""
    sonuc = {"gram": None, "max_kalori": None, "max_fiyat": None}
    m = re.search(r"(\d+)\s*(g|gr|gram)\b", n)
    if m:
        sonuc["gram"] = int(m.group(1))
        n = n.replace(m.group(0), " ")
    m = re.search(r"(\d+)\s*(kcal|kalori)", n)
    if m:
        sonuc["max_kalori"] = int(m.group(1))
        n = n.replace(m.group(0), " ")
    for p in (r"(\d+)\s*(tl|lira)\b", r"butce\w*\D{0,12}(\d+)", r"(\d+)\D{0,6}(alti|altinda|kadar|en fazla)"):
        m = re.search(p, n)
        if m:
            sonuc["max_fiyat"] = int(m.group(1))
            break
    return sonuc


class RestoranBot:
    def __init__(self, ollama=None):
        self.ollama = ollama          # isteğe bağlı, bkz. ollama_mod.py
        self.son_sonuc = []           # "başka?" soruları için
        self.gosterilen = 0

    # ---- Ana giriş noktası ----
    def cevapla(self, mesaj: str) -> str:
        n = normalize(str(mesaj).replace("₺", " tl "))[:500]
        if not n:
            return "Size nasıl yardımcı olabilirim? Örneğin: “Asya mutfağından ne önerirsiniz?”"
        if re.search(KONU_DISI, n):
            return konu_disi_cevap()

        cevap = self._kural_cevabi(n)
        if cevap:
            return cevap
        if self.ollama:
            return self.ollama.cevapla(mesaj) or konu_disi_cevap()
        return konu_disi_cevap()

    # ---- Kurallar ----
    def _kural_cevabi(self, n: str):
        var = {k: bool(re.search(p, n)) for k, p in DESEN.items()}
        sayi = sayilari_ayikla(n)
        yemekler = yemekleri_bul(n)
        filtre = {"mutfak": None, "mutfak_grubu": None, "kategori": None}
        for p, alan, deger in MUTFAKLAR:
            if re.search(p, n):
                filtre[alan] = deger
                break
        for p, kat in KATEGORILER:
            if re.search(p, n):
                filtre["kategori"] = kat
                break

        # 1) Belirli yemek(ler) soruldu
        if len(yemekler) >= 2:
            return "Karşılaştırma:\n\n" + _liste(yemekler) + "\n\nKaloriler porsiyon başına yaklaşık değerlerdir."
        if yemekler:
            return self._yemek_cevabi(yemekler[0], sayi["gram"], var)
        if sayi["gram"] or (var["besin"] and not any([var["hafif"], var["kalorili"], var["protein"]])
                            and not any(filtre.values()) and not sayi["max_kalori"]):
            return ("Bu yemek menümüzde bulunmuyor. Menümüzdeki bir yemeğin adını yazarsanız kalori ve "
                    "protein değerini söyleyebilirim. Örneğin: “250 gr tavuk göğsü kaç kalori?”")

        # 2) "Başka var mı?" -> önceki listenin devamı
        if var["baska"] and not any(filtre.values()) and self.son_sonuc:
            kalan = self.son_sonuc[self.gosterilen:self.gosterilen + 5]
            if not kalan:
                return "Bu kriterlere uyan başka yemeğimiz yok. 😊 Farklı bir mutfak veya kategori sorabilirsiniz."
            self.gosterilen += len(kalan)
            return "Diğer seçenekler:\n\n" + _liste(kalan)

        # 3) Filtreli / sıralı listeler
        sirala = ("fiyat_azalan" if var["pahali"] else "kalori_artan" if var["hafif"]
                  else "kalori_azalan" if var["kalorili"] else "protein_azalan" if var["protein"]
                  else "fiyat_artan")
        siralama_var = any(var[k] for k in ("ucuz", "pahali", "hafif", "kalorili", "protein"))
        filtre_var = any(filtre.values()) or var["vejetaryen"] or sayi["max_fiyat"] or sayi["max_kalori"]

        if filtre_var or siralama_var:
            rows = ara(**filtre, max_fiyat=sayi["max_fiyat"], max_kalori=sayi["max_kalori"],
                       vejetaryen=var["vejetaryen"], sirala=sirala)
            if not rows:
                return "Üzgünüm, bu kriterlere uygun bir yemek bulamadım. 😔\n\nGünün yemeklerimiz:\n\n" + _liste(gunun_yemekleri())
            baslik = self._baslik(filtre, sayi, var)
            if siralama_var and var["en"]:  # "en ucuz", "en hafif"...
                return f"{baslik}:\n\n{_satir(rows[0])}"
            if var["oneri"] and not siralama_var:
                rows = self._oneri_sirasi(rows)
            return self._listele(baslik, rows, limit=3 if var["oneri"] else 5)

        # 4) Diğer sorular
        if var["gunun"] or var["oneri"]:
            return "Bugün sizin için önerilerimiz: 👨‍🍳\n\n" + _liste(gunun_yemekleri())
        if var["mutfak_listesi"]:
            gruplar = sorted({r["mutfak_grubu"] for r in MENU}, key=normalize)
            ulkeler = sorted({r["mutfak"] for r in MENU} - set(gruplar), key=normalize)
            return f"Menümüzde {', '.join(gruplar)} mutfakları var ({', '.join(ulkeler)})."
        if var["menu"]:
            parcalar = []
            for kat in KATEGORI_SIRASI:
                rows = [r for r in MENU if r["kategori"] == kat]
                parcalar.append(f"**{kat}**: " + ", ".join(f"{r['ad']} ({_tl(r['fiyat_tl'])})" for r in rows))
            return "Menümüz:\n\n" + "\n\n".join(parcalar)
        if var["fiyat"]:
            return "Hangi yemeğin fiyatını öğrenmek istersiniz? Örneğin: “Pad Thai ne kadar?”"
        if var["selam"]:
            return (f"Merhaba, {RESTORAN_ADI}'na hoş geldiniz! 👋 Yemek önerisi, fiyat ve kalori "
                    "sorularınızda yardımcı olabilirim. Örneğin: “Asya mutfağından ne önerirsiniz?”")
        if var["tesekkur"]:
            return "Rica ederim, afiyet olsun! 😊"
        if var["veda"]:
            return "Görüşmek üzere, afiyet olsun! 👋"
        return None

    def _yemek_cevabi(self, r, gram, var):
        b = besin(r, gram)
        if gram:
            return (f"{r['ad']} – {b['gram']} g: yaklaşık **{b['kalori']} kcal** ve **{_g(b['protein'])} g protein**.\n\n"
                    f"Bir porsiyonumuz {r['porsiyon_gr']} g, {_tl(r['fiyat_tl'])}.")
        if var["besin"] and not var["fiyat"]:
            return (f"{r['ad']} bir porsiyon ({r['porsiyon_gr']} g): yaklaşık **{b['kalori']} kcal**, "
                    f"**{_g(b['protein'])} g protein**. (100 g'da {r['kalori_100g']:.0f} kcal)")
        if var["fiyat"] and not var["besin"]:
            return f"{r['ad']} fiyatı **{_tl(r['fiyat_tl'])}** (porsiyon {r['porsiyon_gr']} g)."
        veg = "\n- 🌱 Vejetaryen" if r["vejetaryen"] else ""
        return (f"**{r['ad']}** ({r['mutfak']} mutfağı, {r['kategori']})\n"
                f"- Fiyat: {_tl(r['fiyat_tl'])}\n- Porsiyon: {r['porsiyon_gr']} g\n"
                f"- Kalori: yaklaşık {b['kalori']} kcal · Protein: {_g(b['protein'])} g\n"
                f"- İçindekiler: {r['icerik']}{veg}")

    def _listele(self, baslik, rows, limit):
        self.son_sonuc, self.gosterilen = rows, min(limit, len(rows))
        ek = f"\n\nToplam {len(rows)} seçenek var. Devamı için “başka” yazabilirsiniz." if len(rows) > limit else ""
        return f"{baslik}:\n\n{_liste(rows[:limit])}{ek}"

    @staticmethod
    def _oneri_sirasi(rows):
        gunun = [r for r in gunun_yemekleri() if r in rows]
        return gunun + [r for r in rows if r not in gunun and r["kategori"] == "Ana Yemek"] + \
            [r for r in rows if r not in gunun and r["kategori"] != "Ana Yemek"]

    @staticmethod
    def _baslik(filtre, sayi, var):
        parca = []
        if filtre["mutfak_grubu"] or filtre["mutfak"]:
            parca.append(f"{filtre['mutfak_grubu'] or filtre['mutfak']} mutfağından")
        if var["vejetaryen"]:
            parca.append("vejetaryen")
        if filtre["kategori"]:
            parca.append(filtre["kategori"].lower())
        if sayi["max_fiyat"]:
            parca.append(f"{_tl(sayi['max_fiyat'])} ve altı")
        if sayi["max_kalori"]:
            parca.append(f"{sayi['max_kalori']} kcal altı")
        ne = " ".join(parca) or "menümüzden"
        if var["ucuz"]:
            return f"{ne.capitalize()} en uygun fiyatlı seçenek" + ("" if var["en"] else "ler")
        if var["pahali"]:
            return f"{ne.capitalize()} en pahalı seçenek" + ("" if var["en"] else "ler")
        if var["hafif"]:
            return f"{ne.capitalize()} en hafif seçenek" + ("" if var["en"] else "ler")
        if var["kalorili"]:
            return f"{ne.capitalize()} en kalorili seçenek" + ("" if var["en"] else "ler")
        if var["protein"]:
            return f"{ne.capitalize()} protein değeri en yüksek seçenek" + ("" if var["en"] else "ler")
        if var["oneri"]:
            return f"{ne.capitalize()} önerilerimiz 👨‍🍳"
        return ne.capitalize() + " seçenekler"


if __name__ == "__main__":
    from ollama_mod import ollama_baglan

    bot = RestoranBot(ollama=ollama_baglan())
    print(f"🍽️  {RESTORAN_ADI} asistanı" + (" (Ollama açık)" if bot.ollama else "") + " — çıkmak için 'q'\n")
    while True:
        try:
            m = input("Siz: ")
        except (EOFError, KeyboardInterrupt):
            break
        if m.strip().lower() in ("q", "quit", "exit", "çıkış"):
            break
        print(f"\nAsistan: {bot.cevapla(m)}\n")
