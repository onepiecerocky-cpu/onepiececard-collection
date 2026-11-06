"""cards.json の全カード画像を公式サイトから取得し、幅400pxのJPEGに変換して img/ に保存する(既存はスキップ)。"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "img")
os.makedirs(OUT, exist_ok=True)
URL = "https://www.onepiece-cardgame.com/images/cardlist/card/"
cards = json.load(open(os.path.join(ROOT, "cards.json")))["cards"]
tmp = tempfile.mkdtemp()

def job(c):
    dst = os.path.join(OUT, c["id"] + ".jpg")
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return "skip"
    src = os.path.join(tmp, c["img"])
    for attempt in range(3):
        try:
            req = urllib.request.Request(URL + c["img"], headers={"User-Agent": "Mozilla/5.0 (Macintosh)"})
            with urllib.request.urlopen(req, timeout=60) as r, open(src, "wb") as f:
                f.write(r.read())
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "78", "--resampleWidth", "400",
                            src, "--out", dst], check=True, capture_output=True)
            os.remove(src)
            return "ok"
        except Exception as e:
            err = e
            time.sleep(2)
    return "fail %s %s" % (c["id"], err)

done = 0
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(job, cards):
        done += 1
        if res.startswith("fail"):
            print(res, flush=True)
        if done % 250 == 0:
            print("progress", done, "/", len(cards), flush=True)
print("finished", done, flush=True)
