#!/usr/bin/env python3
# Simple merger: combine model_input with aggregated odds (avg/best) for convenience.
import csv, os
from common import write_csv

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)

def main():
    preds = read_csv("data/model_input.csv")
    agg = read_csv("data/agg_h2h.csv")
    agg_map = {(d["league"], d["commence_time"], d["home"], d["away"]): d for d in agg}
    rows = []
    for p in preds:
        key = (p["league"], p["utc_date"], p["home"], p["away"])
        a = agg_map.get(key, {})
        rows.append([
            p["match_key"], p["league"], p["utc_date"], p["home"], p["away"],
            p["p_home"], p["p_draw"], p["p_away"],
            p["our_fair_home"], p["our_fair_draw"], p["our_fair_away"],
            a.get("avg_home",""), a.get("avg_draw",""), a.get("avg_away",""),
            a.get("best_home",""), a.get("best_draw",""), a.get("best_away","")
        ])
    header = ["match_key","league","utc_date","home","away",
              "p_home","p_draw","p_away",
              "our_fair_home","our_fair_draw","our_fair_away",
              "avg_home","avg_draw","avg_away",
              "best_home","best_draw","best_away"]
    write_csv("data/export_for_excel.csv", rows, header)
    print("OK export rows:", len(rows))

if __name__ == "__main__":
    main()
