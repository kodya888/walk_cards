# pak1_photos_commons.py — вдохновляющие фото природы из Wikimedia Commons
# (свободная лицензия; у избранных фото качество проверено вручную).
# Запуск: C:/Users/ADMIN/AppData/Local/Programs/Python/Python313/python.exe otladka/mudrost/pak1_photos_commons.py
# Выход:  otladka/mudrost/bg_src/cN_<slug>.jpg + manifest.json
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

OUT = Path(__file__).resolve().parent / "bg_src"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "walk-cards-bg-picker/1.0 (local picking script)"}

# 6 настроений вдохновляющей природы под «Дорогу осилит идущий»
QUERIES = [
    "sea of clouds mountain summit",
    "mountains above clouds inversion",
    "snowy peak sunrise alpenglow",
    "Matterhorn sunrise",
    "Elbrus sunrise",
    "Mount Blanc mountain sunrise",
]

API = "https://commons.wikimedia.org/w/api.php"


def call_api(params: dict) -> dict:
    params = dict(params, format="json")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main() -> None:
    prefix = sys.argv[1] if len(sys.argv) > 1 else "c"   # префикс имени: uN_/cN_/dN_
    manifest = []
    idx = 0
    for q in QUERIES:
        try:
            data = call_api({
                "action": "query",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {q}",
                "gsrnamespace": "6",
                "gsrlimit": "20",
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": "1000",
            })
        except Exception as e:
            print(f"[ERR] запрос «{q}»: {e}")
            continue
        pages = (data.get("query") or {}).get("pages", {})
        # свежие широкие фото, вертикальные — приоритет
        cands = []
        for p in pages.values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii:
                continue
            w, h = ii.get("width", 0), ii.get("height", 0)
            if w < 1600 or h < 1200:      # мелкие и сканы не берём
                continue
            desc = (ii.get("extmetadata") or {}).get("ImageDescription", {}).get("value", "")
            cands.append({
                "title": p.get("title", "").replace("File:", ""),
                "thumb": ii.get("thumburl", ""),
                "desc": desc,
                "portrait": h >= w,       # вертикальные — в приоритет
                "ratio": (h / w) if w else 0,
            })
        if not cands:
            print(f"[WARN] пусто: {q}")
            continue
        cands.sort(key=lambda c: (-c["portrait"],))
        slug = q.split()[0].lower()
        taken = 0
        for c in cands:
            if taken >= 2:
                break
            if "|" in c["title"] or "/" in c["title"]:
                continue
            idx += 1
            fname = f"{prefix}{idx:02d}_{slug}.jpg"
            try:
                (OUT / fname).write_bytes(fetch(c["thumb"]))
            except Exception as e:
                print(f"[ERR] {fname}: {e}")
                idx -= 1
                continue
            taken += 1
            manifest.append({
                "file": fname,
                "query": q,
                "title": c["title"],
                "link": "https://commons.wikimedia.org/wiki/File:" +
                        urllib.parse.quote(c["title"]),
                "desc": c["desc"][:120],
                "portrait": c["portrait"],
            })
            note = "вертик." if c["portrait"] else "гориз."
            print(f"[OK] {fname} ({note}) — {c['title'][:60]}")

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[DONE] {len(manifest)} шт. в {OUT}")


if __name__ == "__main__":
    main()
