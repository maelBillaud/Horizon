#!/usr/bin/env python3
"""Vérifie les flux RSS/Atom de data/config.newsletter.json (bibliothèque standard uniquement).

Usage :
  python tools/check_feeds.py                 # teste les flux activés
  python tools/check_feeds.py --all           # teste aussi les flux désactivés
  python tools/check_feeds.py --enable-ok     # active les flux valides et récents (7 jours)
"""
import argparse
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = "Mozilla/5.0 (compatible; horizon-poc-checker/1.0)"
ACCEPT = "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.5"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": ACCEPT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def parse_date(text):
    if not text or not text.strip():
        return None
    text = text.strip()
    try:
        d = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d is None:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def parse_feed(data):
    """Retourne (titre, nombre d'articles, date la plus récente ou None)."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"XML invalide ({exc})")
    kind = _local(root.tag)
    if kind == "rss":
        entries = [e for e in root.iter() if _local(e.tag) == "item"]
    elif kind in ("feed", "RDF"):
        wanted = "entry" if kind == "feed" else "item"
        entries = [e for e in root if _local(e.tag) == wanted]
    else:
        raise ValueError(f"racine inattendue <{kind}>")
    title = ""
    for e in root.iter():
        if _local(e.tag) == "title" and e.text:
            title = e.text.strip()
            break
    newest = None
    for entry in entries:
        for child in entry:
            if _local(child.tag) in ("pubDate", "published", "updated", "date"):
                d = parse_date(child.text)
                if d and (newest is None or d > newest):
                    newest = d
                break
    return title, len(entries), newest


def check(url):
    status, data = fetch(url)
    title, count, newest = parse_feed(data)
    return {"status": status, "title": title, "count": count, "newest": newest}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="data/config.newsletter.json")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--enable-ok", action="store_true")
    args = ap.parse_args()
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    now = datetime.now(timezone.utc)
    failures = 0
    for feed in cfg.get("sources", {}).get("rss", []):
        if not feed.get("enabled", True) and not args.all:
            continue
        try:
            r = check(feed["url"])
            age = (now - r["newest"]) if r["newest"] else None
            fresh = age is not None and age <= timedelta(days=7)
            age_txt = f"{age.days} j {age.seconds // 3600} h" if age is not None else "date inconnue"
            flag = "OK " if r["count"] and fresh else "?? "
            print(f"{flag}{feed['name']}: {r['count']} articles, dernier il y a {age_txt}")
            if args.enable_ok and r["count"] and fresh:
                feed["enabled"] = True
        except Exception as exc:  # réseau, HTTP, XML
            print(f"KO {feed['name']}: {exc}")
            if feed.get("enabled", True):
                failures += 1
    if args.enable_ok:
        with open(args.config, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
            f.write("\n")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
