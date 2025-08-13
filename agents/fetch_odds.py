#!/usr/bin/env python3
import os, json, csv, time, datetime as dt
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from common import ensure_dir, write_csv, match_key, now_iso

ODDS_API_KEY = os.getenv("ODDS_API_KEY","")
REGION = os.getenv("REGION","eu")
MARKETS = os.getenv("MARKETS","h2h,totals,btts")
ODDS_FORMAT = os.getenv("ODDS_FORMAT","decimal")
SPORTS = [s.strip() for s in os.getenv("SPORTS","soccer_epl,soccer_spain_la_liga,soccer_portugal_primeira_liga").split(",") if s.strip()]

BASE = "https://api.the-odds-api.com/v4/sports/{sport}/odds"

def fetch_sport(sport):
    qs = {
        "regions": REGION,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": "iso",
        "apiKey": ODDS_API_KEY
    }
    url = BASE.format(sport=sport) + "?" + urlencode(qs)
    req = Request(url, headers={"User-Agent":"ev-agents/1.0"})
    with urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    rows = []
    for ev in data:
        league = sport
        evt = ev.get("commence_time","")
        home = ev.get("home_team","")
        away = ev.get("away_team","")
        eid = ev.get("id","")
        for bm in ev.get("bookmakers",[]):
            bookmaker = bm.get("title") or bm.get("key")
            for mk in bm.get("markets",[]):
                market = mk.get("key")
                for oc in mk.get("outcomes",[]):
                    outcome = oc.get("name") or oc.get("outcome")
                    price = oc.get("price") or oc.get("odds")
                    point = oc.get("point", "")
                    rows.append([league,eid,evt,home,away,bookmaker,market,outcome,price,point])
    return rows

def main():
    if not ODDS_API_KEY:
        raise SystemExit("Missing ODDS_API_KEY secret")
    all_rows = []
    for sp in SPORTS:
        try:
            rows = fetch_sport(sp)
            all_rows.extend(rows)
        except Exception as e:
            print("ERROR fetching", sp, e)
    header = ["league","event_id","commence_time","home","away","bookmaker","market","outcome","price","point"]
    write_csv("data/odds_raw.csv", all_rows, header)
    # Aggregate avg/best for H2H (Home/Draw/Away)
    from collections import defaultdict
    agg = defaultdict(lambda: {"Home":[], "Draw":[], "Away":[]})
    for row in all_rows:
        league,eid,evt,home,away,bm,market,outcome,price,point = row
        if market == "h2h" and outcome in ("Home","Draw","Away"):
            key = (league,evt,home,away)
            try:
                p = float(price)
                agg[key][outcome].append(p)
            except:
                pass
    out2 = []
    for (league,evt,home,away), d in agg.items():
        avg_home = sum(d["Home"])/len(d["Home"]) if d["Home"] else ""
        avg_draw = sum(d["Draw"])/len(d["Draw"]) if d["Draw"] else ""
        avg_away = sum(d["Away"])/len(d["Away"]) if d["Away"] else ""
        best_home = max(d["Home"]) if d["Home"] else ""
        best_draw = max(d["Draw"]) if d["Draw"] else ""
        best_away = max(d["Away"]) if d["Away"] else ""
        out2.append([league,evt,home,away,avg_home,avg_draw,avg_away,best_home,best_draw,best_away, now_iso()])
    write_csv("data/agg_h2h.csv", out2, ["league","commence_time","home","away","avg_home","avg_draw","avg_away","best_home","best_draw","best_away","ts"])
    print("OK fetch_odds; rows:", len(all_rows))

if __name__ == "__main__":
    main()
