# 🍽️ Restoran Menü Chatbotu

[English](README.md) | **Türkçe**

Müşterilerin yemek, fiyat, kalori ve protein sorularını yanıtlayan iki dilli (Türkçe ve İngilizce) bir chatbot.
**Ücretsizdir; API anahtarı veya internet bağlantısı gerektirmez.**

```
> Asya mutfağından ne önerirsiniz?
Asya mutfağından önerilerimiz 👨‍🍳:
- Sebzeli Kızarmış Pilav — 280 ₺ · 595 kcal · 16 g protein
...

> 250 gr tavuk kaç kalori?
Izgara Tavuk Göğsü – 250 g: yaklaşık 412 kcal ve 77.5 g protein.

> Bana python kodu yaz
Üzgünüm, bu konuda yetkin değilim; yalnızca menümüz, fiyatlarımız ve kaloriler hakkında yardımcı olabilirim.
Size günün yemeklerini önerebilirim: ...
```

## Neler yapabilir?
- Mesaj hangi dilde yazıldıysa o dilde (Türkçe veya İngilizce) cevap verir
- Yemek önerisi ve günün yemekleri
- Mutfağa göre arama: Türk, Asya (Japon, Çin, Tay, Hint, Kore, Vietnam), Akdeniz (İtalyan, Yunan), Amerikan
- Kategoriye göre arama: çorba, başlangıç, salata, ana yemek, tatlı
- En ucuz, en pahalı, en hafif ve proteini en yüksek yemek
- Bütçe (“300 TL'ye kadar”) ve kalori sınırı (“500 kalorinin altında”)
- Vejetaryen seçenekler
- Gramaja göre kalori ve protein (“100 gram baklava kaç kalori?”)
- İki yemeği karşılaştırma (“sushi mi ramen mi?”)
- Konu dışı her mesajı reddedip günün yemeklerini önerme

## Kurulum
```bash
git clone https://github.com/Tunz10/restaurant-chatbot.git
cd restaurant-chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Çalıştırma
```bash
streamlit run app.py      # web arayüzü
python bot.py             # terminalde sohbet
python test_chatbot.py    # testler
```

## Nasıl çalışır?
| Dosya | Görevi |
|---|---|
| `data/menu.csv` | Menü: Türkçe ve İngilizce adlar, fiyat, porsiyon gramajı, 100 g başına kalori ve protein |
| `data/gunun_yemekleri.json` | Her gün için günün yemekleri (boş günler otomatik seçilir) |
| `menu.py` | Menüyü okur; arama, sıralama, kalori ve protein hesabı yapar |
| `bot.py` | Kural tabanlı chatbot: dili algılar, mesajı anlar, cevabı `menu.py` ile üretir |
| `ollama_mod.py` | İsteğe bağlı yerel yapay zekâ modu |
| `app.py` | TR/EN seçimli Streamlit web arayüzü |

Bütün sayılar (fiyat, kalori, protein, sıralama) koddan gelir, hiçbir sayı uydurulmaz.
Bot anlamadığı ya da menüyle ilgisi olmayan her mesajı reddeder.

### İsteğe bağlı: Ollama ile daha akıllı cevaplar (yine ücretsiz)
Bilgisayarınızda [Ollama](https://ollama.com) çalışıyorsa, kuralların anlamadığı mesajlar yerel bir modele gönderilir:
```bash
ollama pull qwen2.5:3b
streamlit run app.py      # Ollama'yı otomatik algılar
```
Model menüyü yalnızca fonksiyonlar (tool calling) üzerinden okuyabilir. Hiçbir fonksiyon çağırmadan cevap verirse,
mesaj konu dışı sayılır. Ollama kapalıysa bot kural modunda çalışmaya devam eder.
Farklı bir model için `OLLAMA_MODEL=qwen2.5:7b`, kapatmak için `USE_OLLAMA=0` kullanılabilir.

## Kendi restoranınıza uyarlama
1. `data/menu.csv` dosyasını kendi yemekleriniz ve fiyatlarınızla düzenleyin.
   `diger_adlar` sütununa müşterilerin kullanabileceği diğer adları `|` ile ayırarak yazın.
2. `data/gunun_yemekleri.json` dosyasına günün yemeklerinin `id` değerlerini yazın.
3. Restoranın adını `bot.py` içindeki `RESTORAN_ADI` değişkeninden değiştirin.

## Veri hakkında not
Menüdeki fiyatlar örnektir. Kalori ve protein değerleri,
[USDA FoodData Central](https://fdc.nal.usda.gov/) ve yaygın besin referanslarına dayanan **yaklaşık** değerlerdir.
Tarife ve porsiyona göre değişebilir. Tıbbi veya diyet tavsiyesi değildir.

## Lisans
[MIT](LICENSE)
