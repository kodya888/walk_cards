# pak1_view_25.py — выкладка 25 карточек пака «Дорогу осилит идущий»
# на двух утверждённых фонах: h08_elbrus (гора + небо под текст) и e03_salar
# (лед, текст ниже — на тёмном льду). Выход: bg_src/index.html.
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

D = Path(__file__).resolve().parent / "bg_src"
PAGEVER = "25a"  # при каждой перегенерации менять (кэш браузера)

# --- фразы пака 1 (25 шт) ---
PHRASES = [
    ("Дорогу осилит идущий", ""),
    ("Чтобы дойти до цели, надо прежде всего идти.", "Оноре де Бальзак"),
    ("Когда достигаешь цели, понимаешь, что путь и был целью.", "Поль Валери"),
    ("Не оборачивается тот, кто устремлен к звездам.", "Леонардо да Винчи"),
    ("Начало — самая сложная часть любой работы.", "Платон"),
    ("Ты никогда не будешь «достаточно» готов. Так что просто начни.", ""),
    ("Самый эффективный способ что-либо сделать — сделать это.", "Амелия Эрхарт"),
    ("Два секрета успеха: 1. Начать 2. Довести до конца", ""),
    ("Делай, что можешь, с тем, что имеешь, там, где ты есть.", "Теодор Рузвельт"),
    ("Из тысячи тех, кто говорит красиво, я выберу того, кто молча делает дела.", ""),
    ("Неудачная попытка в 100 раз лучше бездействия.", ""),
    ("Ничто так сильно не разрушает человека, как продолжительное бездействие.", "Аристотель"),
    ("Боишься — не делай! Делаешь — не бойся!", ""),
    ("Страх останавливает действие. Действие останавливает страх.", ""),
    ("Раз уж начал — побеждай!", ""),
    ("Кто не стучится — тому не открывают. Кто не пробует — у того не получается.", ""),
    ("Неудача — это просто возможность начать снова. Но уже более мудро.", "Генри Форд"),
    ("Успех — это когда ты девять раз упал, но десять раз поднялся", ""),
    ("Капля точит камень не силой, а частым падением.", ""),
    ("Тот, который передвигает горы, сначала убирает маленькие камешки", "Конфуций"),
    ("Целым овладевают по частям", "Луций Анней Сенека"),
    ("Если нет ветра, беритесь за вёсла", "латинская пословица"),
    ("Кто сильно желает подняться наверх, тот придумает лестницу", "японская пословица"),
    ("Не опускай руки. Так сложнее дотянуться до вершин", ""),
    ("Делай сегодня то, что другие не хотят. Завтра будешь жить так, как другие не могут.", ""),
]

# --- распределение по фонам ---
# h08 = Эльбрус (небо, текст вверху); e03 = солончак (лед, текст внизу).
# Горные/вершинные фразы оставляю на Эльбрусе.
BG_PLAN = ["h08", "e03"] * 12 + ["h08"]          # №1..24 чередуются, №25 — лед
for i in (19, 22, 23):                            # №20 горы, №23 наверх, №24 вершины (0-based)
    BG_PLAN[i] = "h08"

BG = {
    # имя: (файл, object-position img, top текста %, класс скрима)
    "h08": ("h08_elbrus.jpg", "50% 0%", "27%", "sky"),
    "e03": ("e03_salar.jpg",  "50% 88%", "64%", "ice"),
}


def quote_class(text: str) -> str:
    n = len(text)
    if n <= 30:
        return "s1"        # до ~2 коротких строк — крупно
    if n <= 55:
        return "s2"
    if n <= 72:
        return "s3"
    return "s4"            # самые длинные — мельче


cards = []
for i, (quote, author) in enumerate(PHRASES, 1):
    fname, pos, top, scrim = BG[BG_PLAN[i - 1]]
    author_html = f'<div class="author">{author}</div>' if author else ""
    cards.append(f"""
    <div class="item">
      <div class="card">
        <img src="{fname}?v={PAGEVER}" alt="" style="object-position:{pos}">
        <div class="scrim {scrim}"></div>
        <div class="qblock" style="top:{top}">
          <div class="quote {quote_class(quote)}">{quote}</div>
          {author_html}
        </div>
      </div>
      <div class="cap">№{i} · {BG_PLAN[i - 1]}</div>
    </div>""")

page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Пак «Дорогу осилит идущий» — 25 карточек, 2 фона</title>
<style>
  @font-face {{
    font-family: 'Cormorant';
    src: url('fonts/Cormorant.ttf') format('truetype');
    font-weight: 300 700;
  }}
  @font-face {{
    font-family: 'Montserrat';
    src: url('fonts/Montserrat.ttf') format('truetype');
    font-weight: 100 900;
  }}
  html {{ background:#141126; color:#eee; font-family: Montserrat, 'Segoe UI', sans-serif; }}
  body {{ margin:0; padding:30px; }}
  h1 {{ font-size:18px; font-weight:600; letter-spacing:.04em; margin:0 0 6px; }}
  .hint {{ color:#8f88bd; font-size:12.5px; margin-bottom:26px; max-width:760px; line-height:1.5; }}
  .row {{ display:flex; flex-wrap:wrap; gap:30px; }}
  .item {{ width:300px; }}
  .card {{
    position:relative; width:300px; aspect-ratio:2/3;
    border-radius:16px; overflow:hidden;
    box-shadow:0 14px 36px rgba(0,0,0,.55), 0 0 0 1px rgba(255,213,128,.16);
    background:#221e3a;
  }}
  .card img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
  .scrim {{ position:absolute; inset:0; }}
  /* Эльбрус: затемнение в небе над горой (текст ~27%) */
  .scrim.sky {{
    background:
      radial-gradient(95% 34% at 50% 27%, rgba(24,14,26,.42), rgba(24,14,26,0) 68%),
      linear-gradient(180deg, rgba(24,14,26,.18) 0%, rgba(24,14,26,0) 22%,
                      rgba(24,14,26,0) 60%, rgba(24,14,26,.40) 100%);
  }}
  /* Солончак: затемнение на льду ниже центра (текст ~64%) */
  .scrim.ice {{
    background:
      radial-gradient(92% 30% at 50% 64%, rgba(8,12,26,.60), rgba(8,12,26,0) 70%),
      linear-gradient(180deg, rgba(8,12,26,.28) 0%, rgba(8,12,26,0) 18%,
                      rgba(8,12,26,0) 48%, rgba(8,12,26,.48) 100%);
  }}
  .qblock {{
    position:absolute; left:30px; right:30px; text-align:center; transform:translateY(-50%);
  }}
  .quote {{
    font-family:Cormorant, serif; font-weight:550; line-height:1.22; letter-spacing:.015em;
    color:#fffdf7; text-shadow:0 1px 14px rgba(0,0,0,.65);
  }}
  .quote.s1 {{ font-size:33px; }}
  .quote.s2 {{ font-size:29px; }}
  .quote.s3 {{ font-size:26px; }}
  .quote.s4 {{ font-size:23px; }}
  .author {{
    margin-top:14px; font-family:Montserrat, sans-serif;
    font-size:10px; font-weight:600; letter-spacing:.22em; text-transform:uppercase;
    color:#ffe4ad; opacity:.92; text-shadow:0 1px 8px rgba(0,0,0,.7);
  }}
  .cap {{ font-size:11.5px; color:#7d76a8; margin-top:9px; text-align:center; }}
</style>
</head>
<body>
<h1>Пак «Дорогу осилит идущий» — 25 карточек на двух фонах</h1>
<div class="hint">h08 — Эльбрус: текст в небе над горой. e03 — солончак Уюни: текст ниже,
на тёмном льду. Скрим (затемнение) подогнан под зону текста каждого фона.
Размер шрифта цитаты подгоняется под длину фразы.</div>
<div class="row">{''.join(cards)}
</div>
</body>
</html>"""

(D / "index.html").write_text(page, encoding="utf-8")
print("[DONE] index.html перезаписан, карточек:", len(cards))
