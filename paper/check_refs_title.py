"""对没有 DOI / arXiv 的条目，用 Crossref 书目检索按标题找最接近的记录。"""
import json
import re
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

REFS = r"D:\isac\tmp\refs.txt"
UA = "RefCheck/1.0 (mailto:check@example.org)"
TARGETS = [8, 9, 15, 23, 24, 25, 28, 29, 30, 31]


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def norm(s):
    s = s.lower()
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[^a-z0-9\u4e00-\u9fa5 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def ratio(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


lines = [l.strip() for l in open(REFS, encoding="utf-8") if l.strip()]
refmap = {}
for line in lines:
    m = re.match(r"\[(\d+)\]\s*(.*)", line)
    if m:
        refmap[int(m.group(1))] = m.group(2)

for num in TARGETS:
    body = refmap.get(num, "")
    mt = re.match(r"^[^.]*\.\s*(.+?)\[", body)
    title = mt.group(1) if mt else body
    q = urllib.parse.quote(title)
    url = f"https://api.crossref.org/works?query.bibliographic={q}&rows=3&select=title,DOI,container-title,issued,author"
    try:
        data = json.loads(fetch(url))
        items = data["message"]["items"]
    except Exception as e:
        print(f"[{num}] 查询失败: {e}")
        continue
    print(f"=== [{num}] 声称: {title[:70]}")
    best = None
    for it in items:
        ct = (it.get("title") or [""])[0]
        r = ratio(title, ct)
        cont = (it.get("container-title") or [""])[0]
        yr = None
        if it.get("issued", {}).get("date-parts"):
            yr = it["issued"]["date-parts"][0][0]
        if best is None or r > best[0]:
            best = (r, ct, it.get("DOI"), cont, yr)
        print(f"    {r:.2f}  {ct[:70]} | {cont[:40]} {yr} | {it.get('DOI')}")
    if best:
        verdict = "命中" if best[0] > 0.85 else ("疑似但不同" if best[0] > 0.55 else "查无此文")
        print(f"    -> 判定: {verdict}（最佳 {best[0]:.2f}）")
    time.sleep(0.6)
