# pak1_photos_unsplash.py — красивые фоны для пака «Дорогу осилит идущий» из Unsplash.
# Unsplash — свободная лицензия, авторство показываем на странице выбора.
# Запуск: C:/Users/ADMIN/AppData/Local/Programs/Python/Python313/python.exe otladka/mudrost/pak1_photos_unsplash.py
# Выход:  otladka/mudrost/bg_src/uN_<slug>.jpg (+ manifest.json с авторами)
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

OUT = Path(__file__).resolve().parent / "bg_src"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) walk-cards-pick bg/1.0"}

# запросы = 6 настроений пути; с каждого — 2 лучших фото
QUERIES = [
    "foggy forest path morning light",
    "winding mountain road sunrise",
    "old street lantern night cozy",
    "meadow path golden hour",
    "autumn park path mist",
    "snowy winter path forest light",
]

NAPI = "https://unsplash.com/napi/search/photos?per_page=6&query={q}"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main() -> None:
    manifest = []
    idx = 0
    for q in QUERIES:
        try:
            data = json.loads(fetch(NAPI.format(q=urllib.parse.quote(q))).decode("utf-8"))
        except Exception as e:
            print(f"[ERR] запрос «{q}»: {e}")
            continue
        results = data.get("results", [])
        if not results:
            print(f"[WARN] пусто: {q}")
            continue
        for hit in results[:2]:
            idx += 1
            raw = hit.get("urls", {}).get("raw", "")
            if not raw:
                continue
            sep = "&" if "?" in raw else "?"
            url = raw + f"{sep}fit=crop&crop=entropy&w=900&h=1350&q=82&fm=jpg"
            slug = q.split()[0].lower()
            fname = f"u{idx:02d}_{slug}.jpg"
            try:
                (OUT / fname).write_bytes(fetch(url))
            except Exception as e:
                print(f"[ERR] скачивание {fname}: {e}")
                idx -= 1
                continue
            user = (hit.get("user") or {})
            manifest.append({
                "file": fname,
                "query": q,
                "author": user.get("name", ""),
                "link": hit.get("links", {}).get("html", ""),
                "desc": (hit.get("alt_description") or "")[:80],
            })
            print(f"[OK] {fname}  —  {user.get('name','')}")

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[DONE] {len(manifest)} шт. в {OUT}")


if __name__ == "__main__":
    import urllib.parse
    main()
