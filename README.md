# 🍽️ Restaurant Menu Chatbot

**English** | [Türkçe](README.tr.md)

A bilingual (English and Turkish) chatbot that answers customers' questions about dishes, prices, calories and protein.
**Free to run: no API key and no internet connection needed.**

```
> What do you recommend from Asian cuisine?
Recommended Asian dishes 👨‍🍳:
- Vegetable Fried Rice — 280 ₺ · 595 kcal · 16 g protein
...

> How many calories in 250 g chicken?
Grilled Chicken Breast – 250 g: about 412 kcal and 77.5 g protein.

> Write me python code
Sorry, I can't help with that; I can only answer questions about our menu, prices and calories.
Here are today's specials: ...
```

## Features
- Replies in the language of the message (English or Turkish)
- Dish recommendations and today's specials
- Search by cuisine: Turkish, Asian (Japanese, Chinese, Thai, Indian, Korean, Vietnamese), Mediterranean (Italian, Greek), American
- Search by category: soup, starter, salad, main course, dessert
- Cheapest, most expensive, lightest and highest-protein dishes
- Budget ("under 300") and calorie limits ("under 500 calories")
- Vegetarian options
- Calories and protein for a given weight ("100 g baklava")
- Compare two dishes ("sushi or ramen?")
- Turns down every off-topic message and suggests today's specials instead

## Installation
```bash
git clone https://github.com/Tunz10/restaurant-chatbot.git
cd restaurant-chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
streamlit run app.py      # web interface
python bot.py             # chat in the terminal
python test_chatbot.py    # tests
```

## How it works
| File | Purpose |
|---|---|
| `data/menu.csv` | The menu: Turkish and English names, price, portion size, calories and protein per 100 g |
| `data/gunun_yemekleri.json` | Today's dishes for each weekday (empty days are picked automatically) |
| `menu.py` | Loads the menu; searching, sorting, calorie and protein calculation |
| `bot.py` | Rule-based chatbot: detects the language, understands the message, answers using `menu.py` |
| `ollama_mod.py` | Optional local AI mode |
| `app.py` | Streamlit web interface with a TR/EN switch |

Every number (price, calories, protein, ranking) comes from the code; nothing is made up.
The bot turns down any message it doesn't understand or that isn't about the menu.

### Optional: smarter answers with Ollama (still free)
If [Ollama](https://ollama.com) is running on your computer, messages the rules don't understand are sent to a local model:
```bash
ollama pull qwen2.5:3b
streamlit run app.py      # Ollama is detected automatically
```
The model can read the menu only through functions (tool calling). If it answers without calling a function,
the message is treated as off-topic. If Ollama isn't running, the bot keeps working in rule mode.
Use `OLLAMA_MODEL=qwen2.5:7b` for another model, or `USE_OLLAMA=0` to turn it off.

## Adapting it to your restaurant
1. Edit `data/menu.csv` with your own dishes and prices. Put other names customers might use in the
   `diger_adlar` column, separated by `|`.
2. Put the `id` values of today's dishes in `data/gunun_yemekleri.json`.
3. Change the restaurant name in `RESTORAN_ADI` in `bot.py`.

## About the data
Menu prices are examples. Calorie and protein values are **approximate**, based on
[USDA FoodData Central](https://fdc.nal.usda.gov/) and common nutrition references.
They vary with recipe and portion and are not medical or dietary advice.

## License
[MIT](LICENSE)
