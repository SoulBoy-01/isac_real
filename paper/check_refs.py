"""核验开题报告参考文献：DOI -> Crossref，arXiv -> arXiv API。"""
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from difflib import SequenceMatcher

REFS = r"D:\isac\tmp\refs.txt"
OUT = r"D:\isac\tmp\refs_check.txt"
UA = "RefCheck/1.0 (mailto:check@example.org)"


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


def check_doi(doi, title):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    try:
        data = json.loads(fetch(url))
        msg = data["message"]
        ct = (msg.get("title") or [""])[0]
        year = None
        for k in ("published-print", "published-online", "issued", "created"):
            if k in msg and msg[k].get("date-parts"):
                year = msg[k]["date-parts"][0][0]
                break
        container = (msg.get("container-title") or [""])[0]
        return dict(ok=True, title=ct, year=year, container=container,
                    r=ratio(title, ct) if ct else 0.0)
    except Exception as e:
        return dict(ok=False, err=str(e)[:80])


def check_arxiv(aid, title):
    url = "http://export.arxiv.org/api/query?id_list=" + aid
    try:
        xml = fetch(url)
        m = re.search(r"<entry>.*?<title>(.*?)</title>", xml, re.S)
        if not m:
            return dict(ok=False, err="not found in arXiv API")
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        d = re.search(r"<published>(\d{4})", xml)
        return dict(ok=True, title=t, year=d.group(1) if d else None, r=ratio(title, t))
    except Exception as e:
        return dict(ok=False, err=str(e)[:80])


def main():
    lines = [l.strip() for l in open(REFS, encoding="utf-8") if l.strip()]
    results = []
    for line in lines:
        m = re.match(r"\[(\d+)\]\s*(.*)", line)
        if not m:
            continue
        num, body = int(m.group(1)), m.group(2)
        title = body
        mt = re.match(r"^[^.]*\.\s*(.+?)\[", body)
        if mt:
            title = mt.group(1)
        else:
            mt2 = re.match(r"^[^.]*\.\s*(.+?)\.\s", body)
            if mt2:
                title = mt2.group(1)

        doi = re.search(r"10\.\d{4,9}/[^\s\],;]+", body)
        aid = re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", body)
        rec = dict(num=num, body=body, title=title)
        if doi:
            d = doi.group(0).rstrip(".")
            rec["doi"] = d
            rec.update(check_doi(d, title))
            rec["kind"] = "doi"
            time.sleep(0.4)
        elif aid:
            rec["arxiv"] = aid.group(1)
            rec.update(check_arxiv(aid.group(1), title))
            rec["kind"] = "arxiv"
            time.sleep(0.4)
        else:
            rec.update(ok=None, kind="manual")
        results.append(rec)
        flag = "?" if rec.get("ok") is None else ("OK" if rec["ok"] else "FAIL")
        print(f"[{num:2d}] {flag:4s} {rec.get('r', 0):.2f}  {rec.get('title', '')[:60]}", flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("saved:", OUT)


if __name__ == "__main__":
    main()
