"""İsteğe bağlı Ollama modu (ücretsiz, bilgisayarınızda yerel çalışır).

Kuralların anlamadığı mesajlar yerel modele gönderilir. Model sayıları kendisi
uydurmaz; menüyü yalnızca aşağıdaki fonksiyonlarla (tool calling) okuyabilir.
Model hiçbir fonksiyon çağırmadan cevap verirse mesaj konu dışı sayılır.

Kurulum:  https://ollama.com  ->  ollama pull qwen2.5:3b
Kapatmak: USE_OLLAMA=0 python bot.py
"""
import json
import os
import urllib.request

from menu import ara, besin, gunun_yemekleri, yemekleri_bul

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

SYSTEM = """Sen bir restoranın menü asistanısın. Türkçe, kısa ve samimi cevap ver.
Sadece menüdeki yemekler, fiyatlar, kaloriler ve öneriler hakkında konuş.
Yemek, fiyat veya kalori bilgisini ASLA kendin uydurma; her zaman fonksiyonları çağır.
Soru menüyle ilgili değilse hiçbir fonksiyon çağırma ve sadece KONU_DISI yaz."""


def _ozet(r):
    return {"ad": r["ad"], "mutfak": r["mutfak"], "kategori": r["kategori"], "fiyat_tl": r["fiyat_tl"],
            "kalori": r["kalori"], "protein_g": r["protein"], "vejetaryen": r["vejetaryen"]}


def _menu_ara(mutfak_grubu=None, kategori=None, max_fiyat=None, vejetaryen=False, sirala="fiyat_artan"):
    return [_ozet(r) for r in ara(mutfak_grubu=mutfak_grubu, kategori=kategori, max_fiyat=max_fiyat,
                                  vejetaryen=bool(vejetaryen), sirala=sirala)[:8]]


def _yemek_detay(ad, gram=None):
    bulunan = yemekleri_bul(ad)
    if not bulunan:
        return {"hata": "Bu yemek menüde yok."}
    r = bulunan[0]
    return {**_ozet(r), "icerik": r["icerik"], **besin(r, int(gram) if gram else None)}


FONKSIYONLAR = {
    "menu_ara": _menu_ara,
    "yemek_detay": _yemek_detay,
    "gunun_yemekleri": lambda: [_ozet(r) for r in gunun_yemekleri()],
}

TOOLS = [
    {"type": "function", "function": {
        "name": "menu_ara", "description": "Menüde filtreleyerek ve sıralayarak yemek arar.",
        "parameters": {"type": "object", "properties": {
            "mutfak_grubu": {"type": "string", "enum": ["Türk", "Asya", "Akdeniz", "Amerikan"]},
            "kategori": {"type": "string", "enum": ["Çorba", "Başlangıç", "Salata", "Ana Yemek", "Tatlı"]},
            "max_fiyat": {"type": "integer"},
            "vejetaryen": {"type": "boolean"},
            "sirala": {"type": "string", "enum": ["fiyat_artan", "fiyat_azalan", "kalori_artan", "protein_azalan"]},
        }}}},
    {"type": "function", "function": {
        "name": "yemek_detay", "description": "Bir yemeğin fiyat, içerik, kalori ve protein bilgisi.",
        "parameters": {"type": "object", "properties": {
            "ad": {"type": "string"}, "gram": {"type": "integer"}}, "required": ["ad"]}}},
    {"type": "function", "function": {
        "name": "gunun_yemekleri", "description": "Bugünün önerilen yemekleri.",
        "parameters": {"type": "object", "properties": {}}}},
]


def _post(path, body, timeout):
    req = urllib.request.Request(OLLAMA_URL + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


class OllamaAsistan:
    def __init__(self, model=OLLAMA_MODEL, post=_post):
        self.model = model
        self._post = post

    def cevapla(self, mesaj: str):
        """Cevap metni döndürür; konu dışıysa veya hata olursa None döndürür."""
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": mesaj}]
        try:
            for adim in range(4):
                yanit = self._post("/api/chat", {"model": self.model, "messages": messages, "tools": TOOLS,
                                                 "stream": False, "options": {"temperature": 0}}, timeout=60)
                msg = yanit["message"]
                cagrilar = msg.get("tool_calls") or []
                if not cagrilar:
                    icerik = (msg.get("content") or "").strip()
                    # Hiç fonksiyon çağırmadan verilen cevap = konu dışı (uydurma riskini de önler)
                    if adim == 0 or not icerik or "KONU_DISI" in icerik:
                        return None
                    return icerik
                messages.append(msg)
                for c in cagrilar:
                    fn = FONKSIYONLAR.get(c["function"]["name"])
                    args = c["function"].get("arguments") or {}
                    try:
                        sonuc = fn(**args) if fn else {"hata": "bilinmeyen fonksiyon"}
                    except Exception as e:
                        sonuc = {"hata": str(e)}
                    messages.append({"role": "tool", "content": json.dumps(sonuc, ensure_ascii=False)})
        except Exception:
            return None
        return None


def ollama_baglan():
    """Ollama çalışıyor ve model yüklüyse asistanı döndürür, değilse None."""
    if os.environ.get("USE_OLLAMA", "1") == "0":
        return None
    try:
        req = urllib.request.Request(OLLAMA_URL + "/api/tags")
        with urllib.request.urlopen(req, timeout=1) as r:
            modeller = [m["name"] for m in json.loads(r.read()).get("models", [])]
    except Exception:
        return None
    return OllamaAsistan() if any(m.startswith(OLLAMA_MODEL) for m in modeller) else None
