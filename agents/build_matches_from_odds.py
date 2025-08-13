#!/usr/bin/env python3
import csv, os

SRC = "data/odds_raw.csv"
DST = "data/matches.csv"

seen = set()
rows = []

if os.path.exists(SRC):
    with open(SRC, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            league = d["league"]
            utc = d["commence_time"]
            home = d["home"]
            away = d["away"]
            key = (league, utc, home, away)
            if all(key) and key not in seen:
                seen.add(key)
                rows.append([league, utc, home, away, "", ""])  # match_id, round vazios

# garante cabeçalho mesmo sem odds
os.makedirs("data", exist_ok=True)
with open(DST, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["league","utc_date","home","away","match_id","round"])
    for r in rows:
        w.writerow(r)

print("matches.csv rows:", len(rows))
