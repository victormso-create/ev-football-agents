#!/usr/bin/env python3
import os, json, csv
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from collections import defaultdict
from datetime import datetime

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
REGION_PARAM = os.getenv("REGION", "eu")              # aceita múltiplos: "eu,uk,us"
MARKETS_PRIMARY = os.getenv("MARKETS", "h2h,totals,btts")
SPORTS = [s.strip() for s in os.getenv("SPORTS","soccer_epl").split(",") if s.strip()]
ODDS_FORMAT = os.getenv("ODDS_FORMAT","decimal")

BASE = "https://api.the-odds-api.com/v4/sports/{sport}/odds"

def fetch(sport, regions, markets):
    qs = {
        "regions": regions,
        "markets": markets,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": "iso",
        "apiKey": ODDS_API_KEY
    }
    url = BASE.format(sport=sport) + "?" + urlencode(qs)
    req = Request(url, headers={"User-Agent":"ev-agents/1.0"})
    with urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8")
    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[{sport}] JSON error:", e, raw[:200])
        return []
    return data if isinstance(data, list) else []

def main():
    if not ODDS_API_KEY:
        raise SystemExit("Missing ODDS_API_KEY secret")

    all_rows = []
    total_events = 0

    for sp in SPORTS:
        print(f"=== Fetching {sp} | regions={REGION_PARAM} | markets={MARKETS_PRIMARY}")
        data = fetch(sp, REGION_PARAM, MARKETS_PRIMARY)
        if not data:
            # Fallback 1: só H2H
            print(f"[{sp}] Empty with {MARKETS_PRIMARY}. Retrying with markets=h2h …")
            data = fetch(sp, REGION_PARAM, "h2h")
        if not data:
            # Fallback 2: regiões alargadas
            print(f"[{sp}] Still empty. Retrying with regions=eu,uk,us,au & markets=h2h …")
            data = fetch(sp, "eu,uk,us,au", "h2h")

        print(f"[{sp}] events:", len(data))
        total_events += len(data)

        for ev in data:
            league = sp
            evt = ev.get("commence_time","")
            home = ev.get("home_team") or ev.get("home") or ""
            away = ev.get("away_team") or ev.get("away") or ""
            eid  = ev.get("id","")
            for bm in ev.get("bookmakers",[]):
                bookmaker = bm.get("title") or bm.get("key")
                for mk in bm.get("markets",[]):
                    market = mk.get("key")
                    for oc in mk.get("outcomes",[]):
                        outcome = oc.get("name") or oc.get("outcome")
                        price = oc.get("price") or oc.get("odds")
                        point = oc.get("point", "")
                        all_rows.append([league,eid,evt,home,away,bookmaker,market,outcome,price,point])

    # Escrever odds_raw
    os.makedirs("data", exist_ok=True)
    with open("data/odds_raw.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["league","event_id","commence_time","home","away","bookmaker","market","outcome","price","point"])
        w.writerows(all_rows)

    # Agregar H2H (avg/best)
    agg = defaultdict(lambda: {"Home":[], "Draw":[], "Away":[]})
    for row in all_rows:
        league,eid,evt,home,away,bm,market,outcome,price,point = row
        if market == "h2h" and outcome in ("Home","Draw","Away"):
            try:
                agg[(league,evt,home,away)][outcome].append(float(price))
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
        out2.append([league,evt,home,away,avg_home,avg_draw,avg_away,best_home,best_draw,best_away, datetime.utcnow().isoformat()+"Z"])

    with open("data/agg_h2h.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["league","commence_time","home","away","avg_home","avg_draw","avg_away","best_home","best_draw","best_away","ts"])
        w.writerows(out2)

    print("DONE fetch_odds — rows odds_raw:", len(all_rows), "| rows agg_h2h:", len(out2), "| total events:", total_events)

if __name__ == "__main__":
    main()
