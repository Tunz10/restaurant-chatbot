"""Rule-based restaurant chatbot (Turkish and English). Free, no API needed.

If Ollama is running locally, messages the rules don't understand are passed to it (see ollama_mod.py).
"""
import re

from menu import KATEGORI_SIRASI, MENU, ad, ara, besin, cevir, gunun_yemekleri, icerik, normalize, yemekleri_bul

RESTORAN_ADI = "Lezzet Durağı"

MUTFAKLAR = [
    (r"\b(asya|asyali|uzak ?dogu|asian|asia|far east)", "mutfak_grubu", "Asya"),
    (r"\b(akdeniz|mediterranean)", "mutfak_grubu", "Akdeniz"),
    (r"\bamerica|\bamerika", "mutfak_grubu", "Amerikan"),
    (r"\bturk\b|\bturk (mutfa|yemek)|\bturkish", "mutfak_grubu", "Türk"),
    (r"\bjapon|\bjapan", "mutfak", "Japon"),
    (r"\bcin\b|\bcin (mutfa|yemek)|\bchinese|\bchina", "mutfak", "Çin"),
    (r"\btay\b|\btayland|\bthai", "mutfak", "Tay"),
    (r"\bhint|\bindian\b|\bindia\b", "mutfak", "Hint"),
    (r"\bkore", "mutfak", "Kore"),
    (r"\bvietnam", "mutfak", "Vietnam"),
    (r"\bitalya|\bitalian|\bitaly", "mutfak", "İtalyan"),
    (r"\byunan|\bgreek|\bgreece", "mutfak", "Yunan"),
]
KATEGORILER = [
    (r"\b(corba|soup)", "Çorba"),
    (r"\b(tatli|dessert|sweet)", "Tatlı"),
    (r"\b(salata|salad)", "Salata"),
    (r"\b(baslangic|aperatif|atistirma|meze|starter|appetizer|snack|side)", "Başlangıç"),
    (r"\b(ana yemek|main)", "Ana Yemek"),
]
KONU_DISI = (
    r"\b(tarif|nasil yapilir|hava\b|kod|python|java|program|odev|futbol|mac\b|siyaset|film|dizi|sarki|borsa|"
    r"bitcoin|kripto|doviz|telefon|araba|bilgisayar|haber|fikra|siir|recipe|how to make|how do i make|"
    r"weather|code|coding|homework|football|soccer|politic|election|movie|song|lyrics|stock market|crypto|"
    r"exchange rate|phone|car\b|computer|news|joke|poem|ignore|translate|essay)"
)

DESEN = {
    "selam": r"\b(merhaba|selam|selamlar|iyi gunler|iyi aksamlar|gunaydin|slm|hi|hello|hey|good morning|good evening)\b",
    "tesekkur": r"\b(tesekkur|sagol|sag ol|eyvallah|tsk|thank|thx|cheers)",
    "veda": r"\b(gorusuruz|hosca kal|iyi geceler|bye|goodbye|see you)\b",
    "ucuz": r"\b(ucuz|uygun fiyat|ekonomik|hesapli|cheap|affordable|inexpensive|budget friendly)",
    "pahali": r"\b(pahali|en luks|expensive|priciest)",
    "hafif": r"\b(hafif|dusuk kalori|az kalori|diyet|en az kalori|light|low cal|least calori|fewest calori|diet)",
    "kalorili": r"\b(en kalorili|yuksek kalori|en cok kalori|en fazla kalori|doyurucu|most calori|highest calori|high calori|filling)",
    "protein": r"\b(yuksek protein|en cok protein|en fazla protein|proteinli|protein (orani )?yuksek|en proteinli|"
               r"high protein|most protein|highest protein|protein rich)",
    "vejetaryen": r"\b(vejetaryen|vejeteryan|vegan|etsiz|et yemiyorum|et yemeyen|vegetarian|meatless|no meat|plant based)",
    "besin": r"\b(kalori|kcal|protein|besin degeri|kac gram|calori|nutrition)",
    "fiyat": r"\b(fiyat|kac para|kac tl|kac lira|ne kadar|ucret|price|cost|how much)",
    "fiyat_acik": r"\b(fiyat|kac para|kac tl|kac lira|ucret|price|cost)",
    "oneri": r"\b(oner|tavsiye|ne yesem|ne yiyeyim|ne yiyebilirim|ne yiyelim|ne alsam|ne alayim|aciktim|"
             r"recommend|suggest|what should i (eat|order|have|get)|what to eat|hungry)",
    "gunun": r"\b(gunun|bugun|gunluk|today|daily|special)",
    "menu": r"\b(menu|neler var|ne var|yemekler|listele|cesit|what do you have|dishes|options)",
    "mutfak_listesi": r"\b(hangi mutfak|mutfaklar|hangi ulke|cuisines|which cuisine|what cuisine)",
    "baska": r"\b(baska|daha fazla|devam|diger|other|more|else|another)",
    "en": r"\ben\b|\b(cheapest|priciest|lightest|most|least|highest|lowest)\b",
}

TR_ISARET = (r"\b(ne|neler|kac|mi|mu|var|yok|yemek\w*|en|icin|bana|hangi|merhaba|selam|oner\w*|fiyat\w*|kalori\w*|"
             r"ucuz|pahali|bugun\w*|gunun|tesekkur\w*|lutfen|ve|ile|mutfag\w*|tatli|corba\w*|salata\w*|"
             r"istiyorum|nedir|olan|kadar|altinda|baska)\b")
EN_ISARET = (r"\b(the|what|which|is|are|how|much|many|do|does|you|your|have|any|i|me|my|for|with|under|cheap\w*|"
             r"recommend\w*|suggest\w*|calorie\w*|price\w*|cost\w*|dish\w*|food|today\w*|special\w*|hello|hi|"
             r"thanks|thank|please|vegetarian|soup\w*|dessert\w*|salad\w*|cuisine\w*|expensive|show|give|can|"
             r"should|eat|order|and|of|a|an|more|other|tell|about|write|want|need|like|ignore|previous)\b")

METIN = {
    "bos": {"tr": "Size nasıl yardımcı olabilirim? Örneğin: “Asya mutfağından ne önerirsiniz?”",
            "en": "How can I help? For example: “What do you recommend from Asian cuisine?”"},
    "konu_disi": {"tr": "Üzgünüm, bu konuda yetkin değilim; yalnızca menümüz, fiyatlarımız ve kaloriler hakkında "
                        "yardımcı olabilirim. 😊\n\nSize günün yemeklerini önerebilirim:\n\n",
                  "en": "Sorry, I can't help with that; I can only answer questions about our menu, prices and "
                        "calories. 😊\n\nHere are today's specials:\n\n"},
    "karsilastirma": {"tr": "Karşılaştırma:\n\n", "en": "Comparison:\n\n"},
    "kalori_not": {"tr": "Kaloriler porsiyon başına yaklaşık değerlerdir.", "en": "Calories are approximate, per portion."},
    "menude_yok": {"tr": "Bu yemek menümüzde bulunmuyor. Menümüzdeki bir yemeğin adını yazarsanız kalori ve protein "
                         "değerini söyleyebilirim. Örneğin: “250 gr tavuk göğsü kaç kalori?”",
                   "en": "That dish isn't on our menu. Tell me the name of a dish from our menu and I'll give you its "
                         "calories and protein. For example: “How many calories in 250 g chicken breast?”"},
    "baska_yok": {"tr": "Bu kriterlere uyan başka yemeğimiz yok. 😊 Farklı bir mutfak veya kategori sorabilirsiniz.",
                  "en": "That's everything matching those criteria. 😊 You can ask about another cuisine or category."},
    "diger": {"tr": "Diğer seçenekler:\n\n", "en": "More options:\n\n"},
    "bulunamadi": {"tr": "Üzgünüm, bu kriterlere uygun bir yemek bulamadım. 😔\n\nGünün yemeklerimiz:\n\n",
                   "en": "Sorry, I couldn't find a dish matching that. 😔\n\nToday's specials:\n\n"},
    "gunun": {"tr": "Bugün sizin için önerilerimiz: 👨‍🍳\n\n", "en": "Today's recommendations: 👨‍🍳\n\n"},
    "mutfaklar": {"tr": "Menümüzde {gruplar} mutfakları var ({ulkeler}).",
                  "en": "Our menu covers {gruplar} cuisine ({ulkeler})."},
    "menu": {"tr": "Menümüz:", "en": "Our menu:"},
    "fiyat_sor": {"tr": "Hangi yemeğin fiyatını öğrenmek istersiniz? Örneğin: “Pad Thai ne kadar?”",
                  "en": "Which dish would you like the price of? For example: “How much is Pad Thai?”"},
    "selam": {"tr": "Merhaba, {ad}'na hoş geldiniz! 👋 Yemek önerisi, fiyat ve kalori sorularınızda yardımcı "
                    "olabilirim. Örneğin: “Asya mutfağından ne önerirsiniz?”",
              "en": "Hello, welcome to {ad}! 👋 I can help with dish recommendations, prices and calories. "
                    "For example: “What do you recommend from Asian cuisine?”"},
    "tesekkur": {"tr": "Rica ederim, afiyet olsun! 😊", "en": "You're welcome, enjoy your meal! 😊"},
    "veda": {"tr": "Görüşmek üzere, afiyet olsun! 👋", "en": "See you soon, enjoy your meal! 👋"},
    "gram": {"tr": "{ad} – {gram} g: yaklaşık **{kcal} kcal** ve **{p} g protein**.\n\nBir porsiyonumuz {pg} g, {fiyat}.",
             "en": "{ad} – {gram} g: about **{kcal} kcal** and **{p} g protein**.\n\nOne portion is {pg} g, {fiyat}."},
    "porsiyon": {"tr": "{ad} bir porsiyon ({pg} g): yaklaşık **{kcal} kcal**, **{p} g protein**. (100 g'da {k100} kcal)",
                 "en": "{ad}, one portion ({pg} g): about **{kcal} kcal**, **{p} g protein**. ({k100} kcal per 100 g)"},
    "fiyat": {"tr": "{ad} fiyatı **{fiyat}** (porsiyon {pg} g).", "en": "{ad} costs **{fiyat}** (portion {pg} g)."},
    "detay": {"tr": "**{ad}** ({mutfak} mutfağı, {kat})\n- Fiyat: {fiyat}\n- Porsiyon: {pg} g\n"
                    "- Kalori: yaklaşık {kcal} kcal · Protein: {p} g\n- İçindekiler: {icerik}",
              "en": "**{ad}** ({mutfak} cuisine, {kat})\n- Price: {fiyat}\n- Portion: {pg} g\n"
                    "- Calories: about {kcal} kcal · Protein: {p} g\n- Ingredients: {icerik}"},
    "veg": {"tr": "\n- 🌱 Vejetaryen", "en": "\n- 🌱 Vegetarian"},
    "toplam": {"tr": "\n\nToplam {n} seçenek var. Devamı için “başka” yazabilirsiniz.",
               "en": "\n\nThere are {n} options in total. Type “more” to see the rest."},
}

EN_COGUL = {"soup": "soups", "starter": "starters", "salad": "salads", "main course": "main courses",
            "dessert": "desserts", "dish": "dishes"}


def dil_bul(mesaj: str, varsayilan: str = "tr") -> str:
    n = normalize(mesaj)
    tr = len(re.findall(TR_ISARET, n)) + (3 if re.search(r"[çğıöşüÇĞİÖŞÜ]", mesaj) else 0)
    en = len(re.findall(EN_ISARET, n))
    if tr == en:
        return varsayilan
    return "tr" if tr > en else "en"


def _tl(x):
    return f"{x} ₺"


def _g(x):
    return f"{x:.0f}" if float(x).is_integer() else f"{x:.1f}"


def _satir(r, dil):
    return f"- **{ad(r, dil)}** — {_tl(r['fiyat_tl'])} · {r['kalori']} kcal · {r['protein']} g protein"


def _liste(rows, dil):
    return "\n".join(_satir(r, dil) for r in rows)


def konu_disi_cevap(dil="tr"):
    return METIN["konu_disi"][dil] + _liste(gunun_yemekleri(), dil)


def sayilari_ayikla(n: str):
    """Pull grams, calorie limit and budget out of the message."""
    sonuc = {"gram": None, "max_kalori": None, "max_fiyat": None}
    m = re.search(r"(\d+)\s*(g|gr|gram|grams)\b", n)
    if m:
        sonuc["gram"] = int(m.group(1))
        n = n.replace(m.group(0), " ")
    m = re.search(r"(\d+)\s*(kcal|kalori|calori)", n)
    if m:
        sonuc["max_kalori"] = int(m.group(1))
        n = n.replace(m.group(0), " ")
    desenler = (r"(?P<x>\d+)\s*(tl|lira|try)\b",
                r"(butce\w*|budget\w*|under|below|less than|up to|max\w*|within)\D{0,12}(?P<x>\d+)",
                r"(?P<x>\d+)\D{0,6}(alti|altinda|kadar|en fazla)")
    for p in desenler:
        m = re.search(p, n)
        if m:
            sonuc["max_fiyat"] = int(m.group("x"))
            break
    return sonuc


class RestoranBot:
    def __init__(self, ollama=None, dil="tr"):
        self.ollama = ollama
        self.dil = dil
        self.son_sonuc = []
        self.gosterilen = 0

    def cevapla(self, mesaj: str) -> str:
        n = normalize(str(mesaj).replace("₺", " tl "))[:500]
        if not n:
            return METIN["bos"][self.dil]
        self.dil = dil_bul(mesaj, self.dil)
        if re.search(KONU_DISI, n):
            return konu_disi_cevap(self.dil)

        cevap = self._kural_cevabi(n)
        if cevap:
            return cevap
        if self.ollama:
            return self.ollama.cevapla(mesaj, self.dil) or konu_disi_cevap(self.dil)
        return konu_disi_cevap(self.dil)

    def _kural_cevabi(self, n: str):
        dil = self.dil
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

        if len(yemekler) >= 2:
            return METIN["karsilastirma"][dil] + _liste(yemekler, dil) + "\n\n" + METIN["kalori_not"][dil]
        if yemekler:
            return self._yemek_cevabi(yemekler[0], sayi["gram"], var)
        siralama_var = any(var[k] for k in ("ucuz", "pahali", "hafif", "kalorili", "protein"))
        if sayi["gram"] or (var["besin"] and not siralama_var and not any(filtre.values()) and not sayi["max_kalori"]):
            return METIN["menude_yok"][dil]

        if var["baska"] and not any(filtre.values()) and self.son_sonuc:
            kalan = self.son_sonuc[self.gosterilen:self.gosterilen + 5]
            if not kalan:
                return METIN["baska_yok"][dil]
            self.gosterilen += len(kalan)
            return METIN["diger"][dil] + _liste(kalan, dil)

        sirala = ("fiyat_azalan" if var["pahali"] else "kalori_artan" if var["hafif"]
                  else "kalori_azalan" if var["kalorili"] else "protein_azalan" if var["protein"]
                  else "fiyat_artan")
        filtre_var = any(filtre.values()) or var["vejetaryen"] or sayi["max_fiyat"] or sayi["max_kalori"]

        if filtre_var or siralama_var:
            rows = ara(**filtre, max_fiyat=sayi["max_fiyat"], max_kalori=sayi["max_kalori"],
                       vejetaryen=var["vejetaryen"], sirala=sirala)
            if not rows:
                return METIN["bulunamadi"][dil] + _liste(gunun_yemekleri(), dil)
            tek = siralama_var and var["en"]
            baslik = self._baslik(filtre, sayi, var, tek)
            if tek:
                return f"{baslik}:\n\n{_satir(rows[0], dil)}"
            if var["oneri"] and not siralama_var:
                rows = self._oneri_sirasi(rows)
            return self._listele(baslik, rows, limit=3 if var["oneri"] else 5)

        if var["gunun"] or var["oneri"]:
            return METIN["gunun"][dil] + _liste(gunun_yemekleri(), dil)
        if var["mutfak_listesi"]:
            gruplar = sorted({cevir(r["mutfak_grubu"], dil) for r in MENU}, key=normalize)
            ulkeler = sorted({cevir(r["mutfak"], dil) for r in MENU} - set(gruplar), key=normalize)
            return METIN["mutfaklar"][dil].format(gruplar=", ".join(gruplar), ulkeler=", ".join(ulkeler))
        if var["menu"]:
            parcalar = []
            for kat in KATEGORI_SIRASI:
                rows = [r for r in MENU if r["kategori"] == kat]
                parcalar.append(f"**{cevir(kat, dil)}**: " + ", ".join(f"{ad(r, dil)} ({_tl(r['fiyat_tl'])})" for r in rows))
            return METIN["menu"][dil] + "\n\n" + "\n\n".join(parcalar)
        if var["fiyat"]:
            return METIN["fiyat_sor"][dil]
        if var["selam"]:
            return METIN["selam"][dil].format(ad=RESTORAN_ADI)
        if var["tesekkur"]:
            return METIN["tesekkur"][dil]
        if var["veda"]:
            return METIN["veda"][dil]
        return None

    def _yemek_cevabi(self, r, gram, var):
        dil = self.dil
        b = besin(r, gram)
        alanlar = {"ad": ad(r, dil), "gram": b["gram"], "kcal": b["kalori"], "p": _g(b["protein"]),
                   "pg": r["porsiyon_gr"], "fiyat": _tl(r["fiyat_tl"]), "k100": f"{r['kalori_100g']:.0f}",
                   "mutfak": cevir(r["mutfak"], dil), "kat": cevir(r["kategori"], dil), "icerik": icerik(r, dil)}
        if gram:
            return METIN["gram"][dil].format(**alanlar)
        if var["besin"] and not var["fiyat_acik"]:
            return METIN["porsiyon"][dil].format(**alanlar)
        if var["fiyat"]:
            return METIN["fiyat"][dil].format(**alanlar)
        return METIN["detay"][dil].format(**alanlar) + (METIN["veg"][dil] if r["vejetaryen"] else "")

    def _listele(self, baslik, rows, limit):
        self.son_sonuc, self.gosterilen = rows, min(limit, len(rows))
        ek = METIN["toplam"][self.dil].format(n=len(rows)) if len(rows) > limit else ""
        return f"{baslik}:\n\n{_liste(rows[:limit], self.dil)}{ek}"

    @staticmethod
    def _oneri_sirasi(rows):
        gunun = [r for r in gunun_yemekleri() if r in rows]
        ana = [r for r in rows if r not in gunun and r["kategori"] == "Ana Yemek"]
        return gunun + ana + [r for r in rows if r not in gunun and r not in ana]

    def _baslik(self, filtre, sayi, var, tek):
        mutfak = filtre["mutfak_grubu"] or filtre["mutfak"]
        if self.dil == "en":
            return self._baslik_en(mutfak, filtre["kategori"], sayi, var, tek)
        parca = []
        if mutfak:
            parca.append(f"{mutfak} mutfağından")
        if var["vejetaryen"]:
            parca.append("vejetaryen")
        if filtre["kategori"]:
            parca.append(filtre["kategori"].lower())
        if sayi["max_fiyat"]:
            parca.append(f"{_tl(sayi['max_fiyat'])} ve altı")
        if sayi["max_kalori"]:
            parca.append(f"{sayi['max_kalori']} kcal altı")
        ne = (" ".join(parca) or "menümüzden").capitalize()
        ek = "" if tek else "ler"
        for k, ifade in (("ucuz", "en uygun fiyatlı"), ("pahali", "en pahalı"), ("hafif", "en hafif"),
                         ("kalorili", "en kalorili"), ("protein", "protein değeri en yüksek")):
            if var[k]:
                return f"{ne} {ifade} seçenek{ek}"
        if var["oneri"]:
            return f"{ne} önerilerimiz 👨‍🍳"
        return f"{ne} seçenekler"

    @staticmethod
    def _baslik_en(mutfak, kategori, sayi, var, tek):
        isim = cevir(kategori, "en").lower() if kategori else "dish"
        if not tek:
            isim = EN_COGUL.get(isim, isim + "s")
        sifat = " ".join(x for x in (cevir(mutfak, "en") if mutfak else "", "vegetarian" if var["vejetaryen"] else "") if x)
        on = ""
        for k, (tekil, cogul) in (("ucuz", ("Cheapest", "Most affordable")), ("pahali", ("Most expensive",) * 2),
                                  ("hafif", ("Lightest",) * 2), ("kalorili", ("Highest-calorie",) * 2),
                                  ("protein", ("Highest-protein",) * 2)):
            if var[k]:
                on = tekil if tek else cogul
                break
        if not on and var["oneri"]:
            on = "Recommended"
        baslik = " ".join(x for x in (on, sifat, isim) if x)
        if sayi["max_fiyat"]:
            baslik += f" up to {_tl(sayi['max_fiyat'])}"
        if sayi["max_kalori"]:
            baslik += f" under {sayi['max_kalori']} kcal"
        baslik = baslik[0].upper() + baslik[1:]
        return baslik + (" 👨‍🍳" if var["oneri"] and not on.startswith(("Cheap", "Most", "Light", "High")) else "")


if __name__ == "__main__":
    from ollama_mod import ollama_baglan

    bot = RestoranBot(ollama=ollama_baglan())
    print(f"🍽️  {RESTORAN_ADI}" + (" (Ollama)" if bot.ollama else "") + " — 'q' to quit / çıkmak için 'q'\n")
    while True:
        try:
            m = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if m.strip().lower() in ("q", "quit", "exit", "çıkış"):
            break
        print(f"\n{bot.cevapla(m)}\n")
