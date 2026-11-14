# pak1_view_25c.py — все карточки на Эльбрусе (v2-типографика) типографики: ручные переносы строк по смыслу,
# оптический кегль (от длины самой ДЛИННОЙ строки), мягкий скрим без края.
# Выход: bg_src/index.html (PAGEVER v26a).
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

D = Path(__file__).resolve().parent / "bg_src"
PAGEVER = "27a"

# (строки фразы, автор). Переносы ручные — вёрстка держит ритм строк.
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

# фон единый — Эльбрус на всех карточках
BG_PLAN = ["h08"] * 25

BG = {
    # имя: (файл, object-position, top текста %, класс скрима)
    "h08": ("h08_elbrus.jpg", "50% 0%", "27%", "sky"),
}


def quote_size(lines) -> int:
    """Оптический кегль: вписать самую длинную строку в 236px (карточка 300px)."""
    maxlen = max(len(s) for s in lines)
    s = round(236 / (0.47 * maxlen))
    return max(22, min(34, s))


cards = []
for i, (lines, author) in enumerate(PHRASES, 1):
    fname, pos, top, scrim = BG[BG_PLAN[i - 1]]
    author_html = f'<div class="author">{author}</div>' if author else ""
    quote = "<br>".join(lines)
    cards.append(f"""
    <div class="item">
      <div class="card">
        <img src="{fname}?v={PAGEVER}" alt="" style="object-position:{pos}">
        <div class="scrim {scrim}"></div>
        <div class="qblock" style="top:{top}">
          <div class="quote" style="font-size:{quote_size(lines)}px">{quote}</div>
          {author_html}
        </div>
      </div>
      <div class="cap">№{i} · {BG_PLAN[i-1]} · {quote_size(lines)}px</div>
    </div>""")

page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Пак «Дорогу осилит идущий» — v2 типографика (ручные переносы)</title>
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
  /* Эльбрус: широкий мягкий пиллар в небе, без видимого края */
  .scrim.sky {{
    background:
      radial-gradient(150% 46% at 50% 26%, rgba(28,17,24,.30), rgba(28,17,24,0) 64%),
      linear-gradient(180deg, rgba(28,17,24,.36) 0%, rgba(28,17,24,.06) 24%,
                      rgba(28,17,24,0) 44%, rgba(13,10,20,.46) 100%);
  }}
  /* Солончак: мягкий пиллар на льду */
  .scrim.ice {{
    background:
      radial-gradient(120% 36% at 50% 63%, rgba(8,11,24,.52), rgba(8,11,24,0) 72%),
      linear-gradient(180deg, rgba(8,11,24,.26) 0%, rgba(8,11,24,0) 20%,
                      rgba(8,11,24,0) 46%, rgba(7,9,18,.50) 100%);
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
<h1>Пак «Дорогу осилит идущий» — v2: ручные переносы + оптический кегль</h1>
<div class="hint">Каждая фраза разбита по смыслу вручную (никаких случайных переносов),
кегль считается от самой длинной строки (вписывается в ширину карточки), скрим мягче,
интерлиньяж плотнее, авторский блок раздвинут.</div>
<div class="row">{''.join(cards)}
</div>
</body>
</html>"""

(D / "index.html").write_text(page, encoding="utf-8")
print("[DONE] v2 записан, карточек:", len(cards))
