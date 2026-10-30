#!/usr/bin/env python3
"""Cherche les flux RSS/Atom des médias listés dans tools/media.json.

Pour chaque page, lit les balises <link rel="alternate"> puis teste quelques chemins
courants. Seuls les flux qui répondent et sont valides sont retenus.
Avec --apply, ils sont ajoutés à data/config.newsletter.json avec "enabled": false.
Ensuite : python tools/check_feeds.py --all --enable-ok
"""
import argparse
import json
import re
import urllib.parse

from check_feeds import check, fetch

LINK_TAG = re.compile(r"<link\b[^>]*>", re.I)
FALLBACKS = ["/feed", "/feed/", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", "/flux-rss"]


def find_alternates(html, base):
    found = []
    for tag in LINK_TAG.findall(html):
        if re.search(r"rel=[\"']?alternate", tag, re.I) and re.search(
            r"type=[\"']?application/(rss|atom)\+xml", tag, re.I
        ):
            m = re.search(r"href=[\"']([^\"']+)", tag, re.I)
            if m:
                found.append(urllib.parse.urljoin(base, m.group(1).replace("&amp;", "&")))
    return list(dict.fromkeys(u for u in found if "comment" not in u.lower()))


def discover(page_url, limit=3):
    status, raw = fetch(page_url)
    html = raw.decode("utf-8", errors="replace")
    candidates = find_alternates(html, page_url)
    root = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(page_url))
    candidates += [root + p for p in FALLBACKS]
    valid = []
    for url in dict.fromkeys(candidates):
        try:
            info = check(url)
        except Exception:
            continue
        if info["count"]:
            valid.append((url, info))
        if len(valid) >= limit:
            break
    return valid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", default="tools/media.json")
    ap.add_argument("--config", default="data/config.newsletter.json")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    media = json.load(open(args.media, encoding="utf-8"))
    cfg = json.load(open(args.config, encoding="utf-8"))
    rss = cfg["sources"]["rss"]
    known = {f["url"] for f in rss}
    for m in media:
        try:
            valid = discover(m["page"])
        except Exception as exc:
            print(f"KO {m['name']} ({m['page']}): {exc}")
            continue
        if not valid:
            print(f"-- {m['name']}: aucun flux trouvé sur {m['page']}")
        for url, info in valid:
            print(f"OK {m['name']}: {url} ({info['count']} articles)")
            if args.apply and url not in known:
                rss.append({
                    "name": f"{m['name']} - {info['title'] or 'flux'}"[:80],
                    "url": url,
                    "enabled": False,
                    "category": m["category"],
                    "profile": m["profile"],
                    "content_extractor": "trafilatura",
                })
                known.add(url)
    if args.apply:
        with open(args.config, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
