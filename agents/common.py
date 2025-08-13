#!/usr/bin/env python3
import os, csv, json, time, math, itertools, datetime as dt
from collections import defaultdict, Counter

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def write_csv(path, rows, header):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam**k) / math.factorial(k)

def match_key(league, dt_iso, home, away):
    return f"{league}|{dt_iso}|{home}|{away}"

def now_iso():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
