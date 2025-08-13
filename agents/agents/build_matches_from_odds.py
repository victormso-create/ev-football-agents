import pandas as pd
from datetime import datetime, timedelta
import os

# Caminhos
odds_path = "data/odds_raw.csv"
matches_path = "data/matches.csv"

if not os.path.exists(odds_path):
    print("Nenhum odds_raw.csv encontrado — nada para fazer.")
    exit()

# Ler odds
df = pd.read_csv(odds_path)

# Verifica colunas mínimas
required_cols = {"home_team", "away_team", "commence_time", "sport_key"}
if not required_cols.issubset(df.columns):
    print(f"Faltam colunas obrigatórias: {required_cols - set(df.columns)}")
    exit()

# Criar matches.csv básico
matches = []
for _, row in df.iterrows():
    try:
        utc_date = datetime.strptime(row["commence_time"], "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        continue

    matches.append({
        "league": row["sport_key"],
        "utc_date": utc_date.strftime("%Y-%m-%d %H:%M:%S"),
        "home": row["home_team"],
        "away": row["away_team"],
        "match_id": f"{row['sport_key']}_{row['home_team']}_{row['away_team']}_{utc_date.strftime('%Y%m%d%H%M')}",
        "round": ""
    })

matches_df = pd.DataFrame(matches)

# Salvar
matches_df.to_csv(matches_path, index=False)
print(f"{len(matches_df)} jogos gravados em {matches_path}")
