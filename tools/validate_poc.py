#!/usr/bin/env python3
"""Contrôle hors ligne de la cohérence config / profils, d'après la doc de Horizon."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
errors, warnings = [], []


def err(msg):
    errors.append(msg)


def main():
    cfg = json.load(open(os.path.join(ROOT, "data/config.newsletter.json"), encoding="utf-8"))
    for key in ("ai", "sources"):
        if key not in cfg:
            err(f"bloc « {key} » manquant")
    proc = cfg.get("processing", {})
    pdir = os.path.join(ROOT, proc.get("profiles_dir", "profiles"))
    profiles = {}
    for name in sorted(os.listdir(pdir)):
        d = os.path.join(pdir, name)
        if not os.path.isdir(d):
            continue
        for f in ("profile.json", "match.md", "analysis.md", "enrichment.md"):
            if not os.path.isfile(os.path.join(d, f)):
                err(f"{name}: fichier {f} manquant")
        pj = json.load(open(os.path.join(d, "profile.json"), encoding="utf-8"))
        if pj.get("id") != name or not ID_RE.match(pj.get("id", "")):
            err(f"{name}: id invalide ou différent du dossier")
        allowed = {"id", "name", "display_names", "match", "analysis", "content", "enrichment"}
        extra = set(pj) - allowed
        if extra:
            err(f"{name}: champs inconnus {sorted(extra)}")
        c = pj.get("content", {})
        for k in ("analysis_max_chars", "enrichment_max_chars"):
            if not 500 <= c.get(k, 0) <= 100000:
                err(f"{name}: content.{k} hors de 500-100000")
        if c.get("sampling") not in ("prefix", "head-middle-tail"):
            err(f"{name}: sampling invalide")
        blocks = pj.get("enrichment", {}).get("blocks", [])
        ids = [b.get("id") for b in blocks]
        if not blocks or len(ids) != len(set(ids)):
            err(f"{name}: blocs absents ou en double")
        if sum(1 for b in blocks if b.get("primary")) > 1:
            err(f"{name}: plus d'un bloc primary")
        for b in blocks:
            if b.get("type") != "section" or "tools" not in b:
                err(f"{name}: bloc {b.get('id')} doit avoir type=section et tools")
            for t in b.get("tools", []):
                if t not in ("web_search", "history_search"):
                    err(f"{name}: outil inconnu {t}")
        profiles[name] = pj
    if proc.get("default_profile") not in profiles:
        err("default_profile inconnu")
    for pid, s in proc.get("profile_settings", {}).items():
        if pid not in profiles:
            err(f"profile_settings: profil inconnu {pid}")
        t = s.get("threshold")
        if t is not None and not 0 <= t <= 10:
            err(f"{pid}: threshold hors de 0-10")
    dg = cfg.get("digest", {})
    order = dg.get("profile_order", [])
    if len(order) != len(set(order)) or any(p not in profiles for p in order):
        err("digest.profile_order: doublon ou profil inconnu")
    groups = dg.get("category_groups", {})
    seen = {}
    for g, v in groups.items():
        if v.get("limit", 0) <= 0 or not v.get("categories"):
            err(f"groupe {g}: limit > 0 et categories non vide requis")
        for c in v.get("categories", []):
            if c in seen:
                err(f"catégorie {c} présente dans {seen[c]} et {g}")
            seen[c] = g
    used = set()
    for s in cfg.get("sources", {}).get("rss", []):
        for k in ("name", "url", "profile"):
            if not s.get(k):
                err(f"flux sans {k}: {s}")
        if s.get("profile") not in profiles:
            err(f"flux {s.get('name')}: profil inconnu {s.get('profile')}")
        if not re.match(r"^(https?://|\$\{)", s.get("url", "")):
            err(f"flux {s.get('name')}: URL invalide")
        if s.get("category"):
            used.add(s["category"])
            if s["category"] not in seen:
                warnings.append(f"catégorie {s['category']} sans groupe (limite « other »)")
        else:
            warnings.append(f"flux {s.get('name')} sans catégorie")
    for c, g in seen.items():
        if c not in used:
            warnings.append(f"groupe {g}: aucune source active pour la catégorie {c} pour l'instant")
    for w in warnings:
        print("AVERTISSEMENT", w)
    for e in errors:
        print("ERREUR", e)
    print(f"{len(profiles)} profils, {len(cfg['sources']['rss'])} flux, {len(errors)} erreur(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
