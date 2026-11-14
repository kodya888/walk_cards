# pak1_view_25d.py — ЭКСПЕРИМЕНТ: вариация кадрирования Эльбруса
# (6 вариантов зум/сдвиг по циклу), чтобы 25 карточек не выглядели одним фото.
# Чекпоинт-верстка без вариации: pak1_view_25c.py (коммит ed03f04).
# Откат: python pak1_view_25c.py — и index.html снова прежний.
# Выход: bg_src/index.html (PAGEVER 28a).
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

D = Path(__file__).resolve().parent / "bg_src"
PAGEVER = "29a"

PHRASES = [
    (["Дорогу осилит", "идущий"], ""),
    (["Чтобы дойти до цели,", "надо прежде всего идти."], "Оноре де Бальзак"),
    (["Когда достигаешь цели,", "понимаешь, что путь", "и был целью."], "Поль Валери"),
    (["Не оборачивается", "тот, кто устремлен", "к звездам."], "Леонардо да Винчи"),
    (["Начало — самая", "сложная часть", "любой работы."], "Платон"),
    (["Ты никогда не будешь", "«достаточно» готов.", "Так что просто начни."], ""),
    (["Самый эффективный", "способ что-либо", "сделать — сделать это."], "Амелия Эрхарт"),
    (["Два секрета успеха:", "1. Начать", "2. Довести до конца"], ""),
    (["Делай, что можешь,", "с тем, что имеешь,", "там, где ты есть."], "Теодор Рузвельт"),
    (["Из тысячи тех, кто", "говорит красиво,", "я выберу того,", "кто молча делает дела."], ""),
    (["Неудачная попытка", "в 100 раз лучше", "бездействия."], ""),
    (["Ничто так сильно", "не разрушает человека,", "как продолжительное", "бездействие."], "Аристотель"),
    (["Боишься — не делай!", "Делаешь — не бойся!"], ""),
    (["Страх останавливает", "действие. Действие", "останавливает страх."], ""),
    (["Раз уж начал —", "побеждай!"], ""),
    (["Кто не стучится —", "тому не открывают.", "Кто не пробует —", "у того не получается."], ""),
    (["Неудача — это", "просто возможность", "начать снова.", "Но уже более мудро."], "Генри Форд"),
    (["Успех — это когда", "ты девять раз упал,", "но десять раз поднялся"], ""),
    (["Капля точит камень", "не силой,", "а частым падением."], ""),
    (["Тот, который", "передвигает горы,", "сначала убирает", "маленькие камешки"], "Конфуций"),
    (["Целым овладевают", "по частям"], "Луций Анней Сенека"),
    (["Если нет ветра,", "беритесь за вёсла"], "латинская пословица"),
    (["Кто сильно желает", "подняться наверх,", "тот придумает лестницу"], "японская пословица"),
    (["Не опускай руки.", "Так сложнее", "дотянуться до вершин"], ""),
    (["Делай сегодня то,", "что другие не хотят.", "Завтра будешь жить так,", "как другие не могут."], ""),
]

# Кадрирование: (object-position X%, зум, origin). Вершина Эльбруса на ~55% ширины
# фото; карточка 2:3 из альбомного 4:3 вырезает половину ширины — X двигает окно:
# X≈30 → гора справа, X≈55 → по центру, X≈70 → гора слева.
# Зум через transform scale: origin сверху — гора крупнее и ниже (небо растёт);
# origin снизу — гора крупнее, неба чуть меньше.
# Соседние карточки гарантированно разные (широкую и крупную чередуем).
CROPS = [
    ("55%", 1.00, "50% 0%"),
    ("30%", 1.16, "50% 0%"),
    ("70%", 1.00, "50% 0%"),
    ("55%", 1.22, "50% 0%"),
    ("24%", 1.00, "50% 0%"),
    ("66%", 1.20, "50% 0%"),
    ("47%", 1.08, "50% 0%"),
    ("62%", 1.14, "50% 0%"),
    ("34%", 1.06, "50% 100%"),
]

BG = {"h08": ("h08_elbrus.jpg", "27%", "sky")}


def quote_size(lines) -> int:
    maxlen = max(len(s) for s in lines)
    s = round(236 / (0.47 * maxlen))
    return max(22, min(34, s))


cards = []
for i, (lines, author) in enumerate(PHRASES, 1):
    fname, top, scrim = BG["h08"]
    posx, zoom, origin = CROPS[(i - 1) % len(CROPS)]
    author_html = f'<div class="author">{author}</div>' if author else ""
    quote = "<br>".join(lines)
    zoom_css = f" transform:scale({zoom}); transform-origin:{origin};" if zoom != 1 else ""
    cards.append(f"""
    <div class="item">
      <div class="card">
        <img src="{fname}?v={PAGEVER}" alt="" style="object-position:{posx} 0%;{zoom_css}">
        <div class="scrim {scrim}"></div>
        <div class="qblock" style="top:{top}">
          <div class="quote" style="font-size:{quote_size(lines)}px">{quote}</div>
          {author_html}
        </div>
      </div>
      <div class="cap">№{i} · X {posx} · z{zoom:.2f}</div>
    </div>""")

page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Мотиваторы_1 — эксперимент: вариация кадрирования</title>
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
  .scrim.sky {{
    background:
      radial-gradient(150% 46% at 50% 26%, rgba(28,17,24,.30), rgba(28,17,24,0) 64%),
      linear-gradient(180deg, rgba(28,17,24,.36) 0%, rgba(28,17,24,.06) 24%,
                      rgba(28,17,24,0) 44%, rgba(13,10,20,.46) 100%);
  }}
  .qblock {{
    position:absolute; left:28px; right:28px; text-align:center; transform:translateY(-50%);
  }}
  .quote {{
    font-family:Cormorant, serif; font-weight:550; line-height:1.2; letter-spacing:.01em;
    color:#fffdf7;
    text-shadow:0 2px 18px rgba(0,0,0,.55), 0 1px 3px rgba(0,0,0,.35);
  }}
  .author {{
    margin-top:17px; font-family:Montserrat, sans-serif;
    font-size:9.5px; font-weight:600; letter-spacing:.26em; text-transform:uppercase;
    color:#ffd98a; opacity:.95; text-shadow:0 1px 8px rgba(0,0,0,.7);
  }}
  .cap {{ font-size:11px; color:#7d76a8; margin-top:9px; text-align:center; }}
</style>
</head>
<body>
<h1>Мотиваторы_1 — эксперимент: 9 кадров Эльбруса по циклу</h1>
<div class="hint">Один фон, 9 кадров: сдвиг окна (X 24–70%), зум 1.0–1.22, у №9 зум от низа.
Соседние карточки всегда разные. Чекпоинт без вариации: pak1_view_25c.py (коммит ed03f04).</div>
<div class="row">{''.join(cards)}
</div>
</body>
</html>"""

(D / "index.html").write_text(page, encoding="utf-8")
print("[DONE] эксперимент-вариация записан, карточек:", len(cards))
