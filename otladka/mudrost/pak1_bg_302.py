# pak1_bg_302.py — фоны для мотивационного пака «Дорогу осилит идущий»
# Модель: google/nano-banana-2/edit через 302.AI (та же, что рисовала котов и логотип)
# Ключ: AI302_API_KEY в ai_moi/3dtur/.env
#
# Запуск:  C:/Users/ADMIN/AppData/Local/Programs/Python/Python313/python.exe otladka/mudrost/pak1_bg_302.py
# Выход:   otladka/mudrost/bg/pak1_vN.png + _bg_contact.png
# Фон 2:3 (пропорции карточек в приложении), БЕЗ текста — цитату накладываем отдельно.
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent   # walk_cards
OUT = ROOT / "otladka" / "mudrost" / "bg"
ENV3DTUR = ROOT.parent / "3dtur" / ".env"              # ai_moi/3dtur/.env
ENDPOINT = "https://api.302.ai/ws/api/v3/google/nano-banana-2/edit"

# Общее для всех: вертикальный фон карточки, тихий верх (текст ляжет позже)
BASE = ("vertical collectible quote card BACKGROUND, portrait 2:3, no text, "
        "no letters, no words, no watermark, no signature. The upper two "
        "thirds are calm and nearly empty — plain soft ground where a quote "
        "text will be placed later. Palette fits a cozy walking-collecting "
        "app: deep indigo and purple shades, warm amber gold #ffc040 "
        "accents. Gentle vignette, soft light, premium card mood.")

PROMPTS = [
    # v1 — рассветная тропа: живописная дорожка к солнцу
    BASE + " Scene: a painterly winding dirt footpath through a quiet meadow "
           "leading to a rising golden sun on the far horizon, a few small "
           "golden footprints pressed into the path, thin morning mist, warm "
           "dawn glow, soft storybook gouache style.",
    # v2 — вечер, тёплые фонари и брусчатка
    BASE + " Scene: a cozy storybook watercolor evening alley in deep indigo "
           "shades, a row of warm glowing street lanterns, cobblestone path "
           "with a trail of small golden footprints walking away into the "
           "distance, night windows lit warm amber in the far background.",
    # v3 — минималистичный постер: тропа к вершине
    BASE + " Scene: minimalist flat travel poster: a thin winding trail climbs "
           "layered hills toward a high peak under a rising sun. Layered "
           "silhouette bands in deep indigo, purple and warm amber, large "
           "plain gradient sky with a single small sun disc, clean geometric "
           "shapes, no clutter.",
    # v4 — лёгкая акварель, почти чистый лист
    BASE + " Scene: very light airy watercolor wash on warm paper: soft "
           "gradient of dawn colors, a faint hand-painted path fading into "
           "the distance, three or four small gold-foil footprints, lots of "
           "empty paper texture, extremely minimalist and quiet, delicate.",
    # v5 — плоский дизайн: золотые вехи-ступени по диагонали
    BASE + " Scene: elegant minimal flat design on a deep indigo textured "
           "card ground with a thin gold border frame: a diagonal series of "
           "small golden milestone marks (tiny circles and footsteps) rising "
           "from bottom-left toward top-right, the last one a bright star, "
           "generous empty space, refined and quiet.",
    # v6 — мягкое фото: тропа через поле в золотой час
    BASE + " Scene: soft dreamy photograph, a narrow path through tall "
           "meadow grass at golden hour, path leading forward into warm "
           "haze, gentle bokeh, sun low ahead, calm and warm, slightly "
           "cinematic, mostly plain glowing sky in the upper part.",
]


def load_key() -> str:
    if ENV3DTUR.exists():
        for line in ENV3DTUR.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("AI302_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("[ERROR] AI302_API_KEY не найден в 3dtur/.env")


def post_json(payload: dict, key: str) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=data, method="POST",
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 "User-Agent": "walk-cards-pak1/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=360) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"[ERROR] HTTP {e.code}: {body[:800]}")


def extract_image(body: dict) -> str:
    d = body.get("data") if isinstance(body, dict) else None
    outs = d.get("outputs") if isinstance(d, dict) else None
    if isinstance(outs, list) and outs:
        o = outs[0]
        return o if isinstance(o, str) else o.get("url", "")
    outs2 = body.get("images") or body.get("output")
    if isinstance(outs2, list) and outs2:
        o = outs2[0]
        return o if isinstance(o, str) else o.get("url", "")
    return ""


def save_raw(raw: str, out: Path) -> None:
    if raw.startswith("http"):
        req = urllib.request.Request(raw, headers={"User-Agent": "walk-cards-pak1/1.0"})
        out.write_bytes(urllib.request.urlopen(req, timeout=180).read())
    else:
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[1]
        out.write_bytes(base64.b64decode(raw))


def main() -> None:
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    OUT.mkdir(parents=True, exist_ok=True)
    key = load_key()

    done = []
    for i, prompt in enumerate(PROMPTS, 1):
        if only and i not in only:
            continue
        out = OUT / f"pak1_v{i}.png"
        if out.exists():
            print(f"[SKIP] v{i} уже есть")
            done.append(out)
            continue
        print(f"[INFO] v{i} -> {out.name}")
        body = post_json({
            "prompt": prompt,
            "aspect_ratio": "2:3",
            "resolution": "1k",
            "enable_base64_output": True,
            "enable_sync_mode": True,
        }, key)
        raw = extract_image(body)
        if not raw:
            sys.exit(f"[ERROR] нет картинки в ответе: {json.dumps(body)[:500]}")
        save_raw(raw, out)
        done.append(out)
        print(f"[OK] {out.name}")

    if done:
        from PIL import Image
        imgs = [Image.open(p).convert("RGB") for p in done]
        w = max(im.width for im in imgs)
        h = max(im.height for im in imgs)
        n = len(imgs)
        sheet = Image.new("RGB", (w * n + 30 * (n + 1), h + 30), "#1a1630")
        for j, im in enumerate(imgs):
            sheet.paste(im, (30 + j * (w + 30), 15))
        sheet.save(OUT / "_bg_contact.png")
        print(f"[DONE] {n} шт. + _bg_contact.png в {OUT}")


if __name__ == "__main__":
    main()
