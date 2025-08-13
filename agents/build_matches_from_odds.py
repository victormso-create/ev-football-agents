#!/usr/bin/env python3
import csv, os

SRC = "data/odds_raw.csv"
DST = "data/matches.csv"

if not os.path.exists(SRC):
    print("Sem data/odds_raw.csv — nada a fazer.")
    # ainda assim, garante cabeçalho para o modelo não falhar
    os.makedirs("data", exist_ok=True)
    with open(DST, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["league","utc_date","home","away","match_id","round"])
    raise SystemExit(0)

seen = set()
rows = []
with open(SRC, newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for d in r:
        league = d.get("league","")
        utc    = d.get("commence_time","")
        home   = d.get("home","")
        away   = d.get("away","")
        key = (league, utc, home, away)
        if all(key) and key not in seen:
            seen.add(key)
            match_id = f"{league}_{home}_{away}_{utc.replace(':','').replace('-','')}"
            rows.append([league, utc, home, away, match_id, ""])

os.makedirs("data", exist_ok=True)
with open(DST, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["league","utc_date","home","away","match_id","round"])
    w.writerows(rows)

print(f"matches.csv rows: {len(rows)}")
