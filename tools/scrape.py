"""公式カードリスト(onepiece-cardgame.com)から全収録弾のカード(パラレル含む)を取得して cards.json を作る。"""
import re, json, time, html, urllib.request, sys, os

BASE = "https://www.onepiece-cardgame.com/cardlist/"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh)"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")

def clean(s):
    s = re.sub(r"<br[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()

def field(block, cls):
    m = re.search(r'<div class="%s">\s*<h3>.*?</h3>(.*?)</div>' % cls, block, re.S)
    return clean(m.group(1)) if m else ""

top = get(BASE)
series = []
for v, label in re.findall(r'<option value="(55\d{4})"\s*(?:selected)?>(.*?)<', top):
    label = clean(html.unescape(label)).replace("\n", " ")
    label = re.sub(r"\s+", " ", label)
    series.append((v, label))
print(len(series), "series", file=sys.stderr)

cards, sets = [], []
for v, label in series:
    page = get(BASE + "?search=true&series=" + v)
    m = re.search(r"【(.+?)】", label)
    short = m.group(1) if m else label
    sets.append({"id": v, "name": label, "short": short})
    n = 0
    for cid, body in re.findall(r'<dl class="modalCol" id="([^"]+)">(.*?)</dl>', page, re.S):
        spans = re.findall(r"<span>(.*?)</span>", body)
        code, rarity, ctype = (spans + ["", "", ""])[:3]
        name = clean(re.search(r'<div class="cardName">(.*?)</div>', body, re.S).group(1))
        img = re.search(r'data-src="\.\./images/cardlist/card/([^"?]+)', body).group(1)
        attr = re.search(r'<div class="attribute">.*?alt="([^"]*)"', body, re.S)
        pm = re.search(r"_p(\d+)$", cid)
        cards.append({
            "id": cid, "code": code, "name": name, "rarity": rarity, "type": "CHARACTER" if ctype.startswith("キャラ") else ctype,
            "cost": field(body, "cost"), "power": field(body, "power"),
            "counter": field(body, "counter"), "color": field(body, "color"),
            "attr": attr.group(1) if attr else "", "feature": field(body, "feature"),
            "text": field(body, "text"), "trigger": field(body, "trigger"),
            "img": img, "set": v, "parallel": int(pm.group(1)) if pm else 0,
        })
        if cards[-1]["type"] != "LEADER" and cards[-1]["cost"] in ("-", ""):
            cards[-1]["cost"] = "0"  # 公式サイトはコスト0を「-」と表記する
        n += 1
    print(v, short, n, file=sys.stderr)
    time.sleep(1)

out = os.path.join(os.path.dirname(__file__), "..", "cards.json")
json.dump({"updated": time.strftime("%Y-%m-%d"), "sets": sets, "cards": cards},
          open(out, "w"), ensure_ascii=False, separators=(",", ":"))
js = os.path.join(os.path.dirname(__file__), "..", "cards.js")
open(js, "w").write("window.CARD_DATA=" + open(out).read() + ";")
print("total", len(cards), file=sys.stderr)
