"""Optional local Ollama mode (free).

The model reads the menu only through the functions below (tool calling).
If it answers without calling a function, the message is treated as off-topic.

Setup: https://ollama.com, then `ollama pull qwen2.5:3b`. Disable with USE_OLLAMA=0.
"""
import json
import os
import urllib.request

from menu import ad, ara, besin, cevir, gunun_yemekleri, icerik, yemekleri_bul

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

SYSTEM = {
    "tr": "Sen bir restoranın menü asistanısın. Türkçe, kısa ve samimi cevap ver. "
          "Sadece menüdeki yemekler, fiyatlar, kaloriler ve öneriler hakkında konuş. "
          "Yemek, fiyat veya kalori bilgisini asla kendin uydurma; her zaman fonksiyonları çağır. "
          "Soru menüyle ilgili değilse hiçbir fonksiyon çağırma ve sadece KONU_DISI yaz.",
    "en": "You are a restaurant's menu assistant. Reply in English, briefly and warmly. "
          "Only talk about the dishes on the menu, prices, calories and recommendations. "
          "Never make up dishes, prices or calories; always call the functions. "
          "If the question is not about the menu, call no function and reply only KONU_DISI.",
}


def _ozet(r, dil):
    return {"ad": ad(r, dil), "mutfak": cevir(r["mutfak"], dil), "kategori": cevir(r["kategori"], dil),
            "fiyat_tl": r["fiyat_tl"], "kalori": r["kalori"], "protein_g": r["protein"], "vejetaryen": r["vejetaryen"]}


def _fonksiyonlar(dil):
    def menu_ara(mutfak_grubu=None, kategori=None, max_fiyat=None, vejetaryen=False, sirala="fiyat_artan"):
        rows = ara(mutfak_grubu=mutfak_grubu, kategori=kategori, max_fiyat=max_fiyat,
                   vejetaryen=bool(vejetaryen), sirala=sirala)
        return [_ozet(r, dil) for r in rows[:8]]

    def yemek_detay(ad_, gram=None):
        bulunan = yemekleri_bul(ad_)
        if not bulunan:
            return {"hata": "not on the menu"}
        r = bulunan[0]
        return {**_ozet(r, dil), "icerik": icerik(r, dil), **besin(r, int(gram) if gram else None)}

    return {
        "menu_ara": menu_ara,
        "yemek_detay": lambda ad=None, gram=None: yemek_detay(ad or "", gram),
        "gunun_yemekleri": lambda: [_ozet(r, dil) for r in gunun_yemekleri()],
    }


TOOLS = [
    {"type": "function", "function": {
        "name": "menu_ara", "description": "Search the menu with filters and sorting.",
        "parameters": {"type": "object", "properties": {
            "mutfak_grubu": {"type": "string", "enum": ["Türk", "Asya", "Akdeniz", "Amerikan"]},
            "kategori": {"type": "string", "enum": ["Çorba", "Başlangıç", "Salata", "Ana Yemek", "Tatlı"]},
            "max_fiyat": {"type": "integer"},
            "vejetaryen": {"type": "boolean"},
            "sirala": {"type": "string", "enum": ["fiyat_artan", "fiyat_azalan", "kalori_artan", "protein_azalan"]},
        }}}},
    {"type": "function", "function": {
        "name": "yemek_detay", "description": "Price, ingredients, calories and protein of one dish.",
        "parameters": {"type": "object", "properties": {
            "ad": {"type": "string"}, "gram": {"type": "integer"}}, "required": ["ad"]}}},
    {"type": "function", "function": {
        "name": "gunun_yemekleri", "description": "Today's recommended dishes.",
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

    def cevapla(self, mesaj: str, dil: str = "tr"):
        """Returns the answer text, or None if off-topic or on error."""
        fonksiyonlar = _fonksiyonlar(dil)
        messages = [{"role": "system", "content": SYSTEM[dil]}, {"role": "user", "content": mesaj}]
        try:
            for adim in range(4):
                yanit = self._post("/api/chat", {"model": self.model, "messages": messages, "tools": TOOLS,
                                                 "stream": False, "options": {"temperature": 0}}, timeout=60)
                msg = yanit["message"]
                cagrilar = msg.get("tool_calls") or []
                if not cagrilar:
                    metin = (msg.get("content") or "").strip()
                    if adim == 0 or not metin or "KONU_DISI" in metin:
                        return None
                    return metin
                messages.append(msg)
                for c in cagrilar:
                    fn = fonksiyonlar.get(c["function"]["name"])
                    try:
                        sonuc = fn(**(c["function"].get("arguments") or {})) if fn else {"hata": "unknown function"}
                    except Exception as e:
                        sonuc = {"hata": str(e)}
                    messages.append({"role": "tool", "content": json.dumps(sonuc, ensure_ascii=False)})
        except Exception:
            return None
        return None


def ollama_baglan():
    """Returns an assistant if Ollama is running with the model installed, otherwise None."""
    if os.environ.get("USE_OLLAMA", "1") == "0":
        return None
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=1) as r:
            modeller = [m["name"] for m in json.loads(r.read()).get("models", [])]
    except Exception:
        return None
    return OllamaAsistan() if any(m.startswith(OLLAMA_MODEL) for m in modeller) else None
