# pak1_view_page.py — макет карточек пака «Дорогу осилит идущий» (тема: гора).
# Дизайн: Cormorant для цитаты, Montserrat для служебных подписей, золотые акценты.
# Выход: bg_src/index.html; сервер: python -m http.server 8791 в bg_src (уже запущен).
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

D = Path(__file__).resolve().parent / "bg_src"
PAGEVER = "8"   # при каждой перезагенерации меняется, чтобы сбрасывать кэш картинок

# pos — object-position кадра; top — % высоты, где центр текстового блока
PHOTOS = [
    ("f01", "50% 72%", "34%"),   # гребень с людьми, рассветное небо
    ("f02", "50% 66%", "35%"),   # силуэты на хребте, сумеречный градиент
    ("f10", "74% 40%", "32%"),   # вершина над морем облаков (вертик.)
    ("f09", "50% 42%", "40%"),   # вид с горы на море облаков
    ("f05", "50% 72%", "30%"),   # тропа в гору, идущие люди
]


def photo_html(pref: str, pos: str, top: str, quote: str, author: str,
               variant: str = "") -> str:
    f = next((p for p in sorted(D.glob("*.jpg")) if p.name.startswith(pref + "_")), None)
    if not f:
        print(f"[WARN] нет файла для {pref}")
        return ""
    author_html = f'<div class="author">{author}</div>' if author else ""
    ink = " ink" if variant == "ink" else ""
    scrim = "scrim light" if variant == "ink" else "scrim"
    scrim = "scrim strong" if variant == "strong" else scrim
    cap = f"{f.name}{' — тёмный текст' if variant == 'ink' else ''}"
    return f"""
    <div class="item">
      <div class="card">
        <img src="{f.name}?v=PAGEVER" alt="" style="object-position:{pos}">
        <div class="{scrim}"></div>
        <div class="qblock{ink}" style="top:{top}">
          <div class="quote">{quote}</div>
          {author_html}
        </div>
      </div>
      <div class="cap">{cap}</div>
    </div>"""


cards = [
    # Маттерхорн с отражением в Риффельзее (вертик., ровная зона — верхнее небо)
    photo_html("h07", "50% 50%", "26%", "Дорогу осилит идущий", ""),
    # Эльбрус на рассвете: чистое оранжевое небо сверху
    photo_html("h08", "50% 52%", "34%", "Дорогу осилит идущий", ""),
    # «Портрет Эльбруса»: панорама, вершина в центре
    photo_html("h09", "50% 50%", "24%", "Дорогу осилит идущий", ""),
    # соляная равнина Уюни на закате: тёмное верхнее небо
    photo_html("e03", "50% 50%", "50%", "Дорогу осилит идущий", "", "strong"),
]

page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Пак «В путь» — макет карточек (гора)</title>
<style>
  @font-face {{
    font-family: 'Cormorant';
    src: url('fonts/Cormorant.ttf') format('truetype');
    font-weight: 300 700;
  }}
  @font-face {{
    font-family: 'Cormorant';
    src: url('fonts/CormorantItalic.ttf') format('truetype');
    font-style: italic;
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
  .scrim {{
    position:absolute; inset:0;
    background:
      radial-gradient(90% 55% at 50% 34%, rgba(12,9,26,.30), rgba(12,9,26,0) 62%),
      linear-gradient(180deg, rgba(12,9,26,.42) 0%, rgba(12,9,26,0) 30%,
                      rgba(12,9,26,0) 62%, rgba(12,9,26,.50) 100%);
  }}
  .scrim.light {{
    background:
      radial-gradient(90% 55% at 50% 34%, rgba(12,9,26,.14), rgba(12,9,26,0) 62%),
      linear-gradient(180deg, rgba(12,9,26,.20) 0%, rgba(12,9,26,0) 30%,
                      rgba(12,9,26,0) 62%, rgba(12,9,26,.24) 100%);
  }}
  .scrim.strong {{
    background:
      radial-gradient(85% 42% at 50% 50%, rgba(12,9,26,.74), rgba(12,9,26,0) 70%),
      linear-gradient(180deg, rgba(12,9,26,.45) 0%, rgba(12,9,26,0) 30%,
                      rgba(12,9,26,0) 62%, rgba(12,9,26,.50) 100%);
  }}
  .qblock.ink .quote {{
    color:#2e273f; text-shadow:0 1px 12px rgba(255,255,255,.5);
  }}
  .qblock.ink .qmark {{
    color:#8a6c2f; text-shadow:none;
  }}
  .qblock.ink .divider i {{ background:linear-gradient(90deg, rgba(122,92,38,0), #8a6c2f); }}
  .qblock.ink .divider b {{ color:#8a6c2f; }}
  .qblock.ink .author {{
    color:#5d5327; text-shadow:0 1px 6px rgba(255,255,255,.4);
  }}
  .qblock {{
    position:absolute; left:30px; right:30px; text-align:center; transform:translateY(-50%);
  }}
  .qmark {{
    font-family:Cormorant, serif; font-weight:600; font-size:66px; line-height:.4;
    color:#ffd98a; opacity:.9; margin-bottom:26px; text-shadow:0 2px 10px rgba(0,0,0,.4);
  }}
  .quote {{
    font-family:Cormorant, serif; font-weight:550; font-size:33px;
    line-height:1.22; letter-spacing:.015em; color:#fffdf7;
    text-shadow:0 1px 14px rgba(0,0,0,.55);
  }}
  .divider {{
    display:flex; align-items:center; justify-content:center; gap:10px; margin-top:20px;
    opacity:.85;
  }}
  .divider i {{ display:block; width:26px; height:1px; background:linear-gradient(90deg, rgba(255,214,130,0), #ffcf7d); }}
  .divider i:last-child {{ transform:scaleX(-1); }}
  .divider b {{
    font-family:Montserrat, sans-serif; font-weight:400; font-size:9px;
    color:#ffd98a; transform:scale(1.15);
  }}
  .author {{
    margin-top:14px; font-family:Montserrat, sans-serif;
    font-size:10px; font-weight:600; letter-spacing:.22em; text-transform:uppercase;
    color:#ffe4ad; opacity:.9; text-shadow:0 1px 8px rgba(0,0,0,.6);
  }}
  .packchip {{
    position:absolute; top:16px; left:50%; transform:translateX(-50%);
    font-size:9.5px; font-weight:600; letter-spacing:.3em; text-transform:uppercase;
    color:#ffe9b8; background:rgba(16,11,32,.35); border:1px solid rgba(255,204,80,.5);
    padding:6px 14px 5px 17px; border-radius:999px; backdrop-filter:blur(2px);
  }}
  .cap {{ font-size:11.5px; color:#7d76a8; margin-top:9px; text-align:center; }}
</style>
</head>
<body>
<h1>Пак «В путь» — макет карточек: тема горы</h1>
<div class="hint">Шрифт цитаты — Cormorant (антиква с кириллицей), служебные подписи — Montserrat.
Фото: h07 — Маттерхорн, h08 — Эльбрус на рассвете, h09 — «Портрет Эльбруса».
Дальше: если такой макет годится — генерирую остальные 22 карточки пака на выбранном фоне.</div>
<div class="row">{''.join(cards)}
</div>
</body>
</html>"""

(D / "index.html").write_text(page, encoding="utf-8")
print("[DONE] index.html перезаписан, макетов:", len([c for c in cards if c]))
