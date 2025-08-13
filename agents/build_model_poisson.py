#!/usr/bin/env python3
# Baseline Poisson model (no external deps) using historical Results + optional segment stats & recent form.
# Outputs model_input.csv with our probabilities and fair odds.
import os, csv, math, datetime as dt
from collections import defaultdict, Counter
from common import ensure_dir, write_csv, poisson_pmf, match_key, now_iso

MAX_GOALS = int(os.getenv("MAX_GOALS","10"))

def load_results(path="data/results.csv"):
    rows = []
    if not os.path.exists(path): return rows
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            rows.append(d)
    return rows

def load_recent_form(path="data/recent_form.csv"):
    m = {}
    if not os.path.exists(path): return m
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            key = (d["league"], d["team"], d["metric"])
            m[key] = float(d["value"])
    return m

def load_segments(path="data/segments.csv"):
    rows = []
    if not os.path.exists(path): return rows
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            rows.append(d)
    return rows

def load_matches(path="data/matches.csv"):
    rows = []
    if not os.path.exists(path): return rows
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            rows.append(d)
    return rows

def league_baselines(results):
    by_lg = defaultdict(lambda: {"home_g":[], "away_g":[]})
    for d in results:
        by_lg[d["league"]]["home_g"].append(float(d["home_goals"]))
        by_lg[d["league"]]["away_g"].append(float(d["away_goals"]))
    out = {}
    for lg,vals in by_lg.items():
        mu_home = sum(vals["home_g"])/len(vals["home_g"]) if vals["home_g"] else 1.5
        mu_away = sum(vals["away_g"])/len(vals["away_g"]) if vals["away_g"] else 1.2
        out[lg] = (mu_home, mu_away)
    return out

def segment_multiplier(seg_rows, league, team, for_scored=True, early_cut=30):
    # Compute share of early goals vs league
    t_vals = []
    for d in seg_rows:
        if d["league"] != league: continue
    l_vals = []
    for d in seg_rows:
        if d["league"] != league: continue
        val = d["gf_per90_bin"] if for_scored else d["ga_per90_bin"]
        if val == "" or val is None: continue
        v = float(val); l_vals.append(v)
    if not l_vals:
        return 1.0
    team_early = sum([float(d["gf_per90_bin"] if for_scored else d["ga_per90_bin"]) for d in seg_rows if d["league"]==league and d["team"]==team and int(d["bin_start_min"])<=30 and (d["gf_per90_bin"] if for_scored else d["ga_per90_bin"])!=""]) or 0.0001
    team_total = sum([float(d["gf_per90_bin"] if for_scored else d["ga_per90_bin"]) for d in seg_rows if d["league"]==league and d["team"]==team and (d["gf_per90_bin"] if for_scored else d["ga_per90_bin"])!=""]) or 0.0001
    lg_early = sum([float(d["gf_per90_bin"] if for_scored else d["ga_per90_bin"]) for d in seg_rows if d["league"]==league and int(d["bin_start_min"])<=30 and (d["gf_per90_bin"] if for_scored else d["ga_per90_bin"])!=""]) or 0.0001
    lg_total = sum([float(d["gf_per90_bin"] if for_scored else d["ga_per90_bin"]) for d in seg_rows if d["league"]==league and (d["gf_per90_bin"] if for_scored else d["ga_per90_bin"])!=""]) or 0.0001
    share_t = team_early/team_total
    share_l = lg_early/lg_total
    ratio = max(0.8, min(1.2, share_t/share_l))  # clamp +/-20%
    return ratio**0.5  # smooth

def probs_from_lambdas(lh, la):
    # Compute p_home, p_draw, p_away, p_over25, p_btts
    p_home = 0.0; p_draw = 0.0; p_away = 0.0; p_over25 = 0.0; p_btts = 0.0
    for i in range(0, MAX_GOALS+1):
        for j in range(0, MAX_GOALS+1):
            ph = poisson_pmf(i, lh)
            pa = poisson_pmf(j, la)
            p = ph*pa
            if i>j: p_home += p
            elif i==j: p_draw += p
            else: p_away += p
            if i+j > 2: p_over25 += p
            if i>0 and j>0: p_btts += p
    p_under25 = 1-p_over25
    p_btts_n = 1-p_btts
    return p_home, p_draw, p_away, p_over25, p_under25, p_btts, p_btts_n

def main():
    results = load_results("data/results.csv")
    matches = load_matches("data/matches.csv")
    recent = load_recent_form("data/recent_form.csv")
    segments = load_segments("data/segments.csv")
    baselines = league_baselines(results)
    out_rows = []
    for m in matches:
        lg = m["league"]; dts = m["utc_date"]; home = m["home"]; away = m["away"]
        mu_h, mu_a = baselines.get(lg, (1.5,1.2))
        # Recent form modifiers
        gf_h = recent.get((lg, home, "gf_wavg_home"), mu_h)
        ga_h = recent.get((lg, home, "ga_wavg_home"), mu_h)
        gf_a = recent.get((lg, away, "gf_wavg_away"), mu_a)
        ga_a = recent.get((lg, away, "ga_wavg_away"), mu_a)
        # League avgs (fallback)
        lg_gf_h = sum([float(r["home_goals"]) for r in results if r["league"]==lg])/max(1,len([1 for r in results if r["league"]==lg])) if results else mu_h
        lg_ga_h = lg_gf_h
        lg_gf_a = sum([float(r["away_goals"]) for r in results if r["league"]==lg])/max(1,len([1 for r in results if r["league"]==lg])) if results else mu_a
        lg_ga_a = lg_gf_a
        lam_h = mu_h * (gf_h/max(0.001,lg_gf_h)) * (ga_a/max(0.001,lg_gf_a))
        lam_a = mu_a * (gf_a/max(0.001,lg_gf_a)) * (ga_h/max(0.001,lg_ga_h))
        # Segment multipliers
        mh = segment_multiplier(segments, lg, home, True, early_cut=30)
        ma = segment_multiplier(segments, lg, away, False, early_cut=30)
        lam_h_adj = lam_h * mh
        lam_a_adj = lam_a * ma
        p_home, p_draw, p_away, p_over25, p_under25, p_btts, p_btts_n = probs_from_lambdas(lam_h_adj, lam_a_adj)
        fair_home = 1/p_home if p_home>0 else ""
        fair_draw = 1/p_draw if p_draw>0 else ""
        fair_away = 1/p_away if p_away>0 else ""
        mk = match_key(lg, dts, home, away)
        out_rows.append([mk, lg, dts, home, away, lam_h_adj, lam_a_adj, p_home, p_draw, p_away, p_over25, p_under25, p_btts, p_btts_n, fair_home, fair_draw, fair_away])
    header = ["match_key","league","utc_date","home","away","lambda_home","lambda_away","p_home","p_draw","p_away","p_over25","p_under25","p_btts_y","p_btts_n","our_fair_home","our_fair_draw","our_fair_away"]
    write_csv("data/model_input.csv", out_rows, header)
    print("OK model_input rows:", len(out_rows))

if __name__ == "__main__":
    main()
