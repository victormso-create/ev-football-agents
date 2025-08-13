# EV Agents — Starter (Victor)

Automação na cloud (GitHub Actions) para:
- Puxar **odds** (The Odds API).
- Gerar **probabilidades e odd justa** (modelo Poisson baseline com forma/segmentos).
- Exportar CSVs que o teu **Excel/Sheets** lê direto.

## 1) Preparar o repositório
1. Cria um repositório no GitHub (público ou privado).
2. Faz upload de **todos** os ficheiros deste pacote.
3. Em **Settings → Actions → General**: permite ações no repositório.
4. Em **Settings → Secrets and variables → Actions → New repository secret**, cria:
   - `ODDS_API_KEY` — a tua chave da The Odds API.
   - (Opcional) `REGION` (default `eu`), `MARKETS` (default `h2h,totals,btts`), `SPORTS` (default `soccer_epl,soccer_spain_la_liga,soccer_portugal_primeira_liga`).

## 2) Estrutura de dados esperada (CSV em /data)
- `matches.csv` — jogos futuros (league,utc_date,home,away,match_id,round).
- `results.csv` — histórico com golos (league,utc_date,home,away,home_goals,away_goals).
- `segments.csv` — golos por bin de 10/15 min (league,team,bin_start_min,gf_per90_bin,ga_per90_bin).
- (Opcional) `recent_form.csv` — métricas *gf_wavg_home, ga_wavg_home, gf_wavg_away, ga_wavg_away* por (league,team).

> Podes alimentar estes CSVs por Power Query (API-Football) ou manual (export de site permitido).  
> Se não tiveres `results.csv` ainda, o modelo cai em *defaults* seguros.

## 3) Como funciona a execução
O workflow `.github/workflows/agents.yml` corre **a cada 30 min** (e on-demand) e faz:
- `agents/fetch_odds.py` → `data/odds_raw.csv` + `data/agg_h2h.csv` (avg/best).
- `agents/build_model_poisson.py` → `data/model_input.csv` (probabilidades e fair odds).
- `agents/ensemble.py` → `data/export_for_excel.csv` (tudo num só).
- Faz commit automático dos CSVs na branch principal (`contents: write`).

## 4) Ligar no Excel/Sheets
- **Excel (Power Query):** Dados → De Web → URL do ficheiro bruto, por ex.:  
  `https://raw.githubusercontent.com/<teu-username>/<repo>/main/data/export_for_excel.csv`
- **Google Sheets:** `=IMPORTDATA("https://raw.githubusercontent.com/.../data/export_for_excel.csv")`

## 5) Ajustes
- Edita `SPORTS`, `MARKETS`, `REGION` em **Secrets** ou no workflow.
- Troca o *schedule* no YAML se quiseres outra cadência.
- Quando adicionarmos ML/ensemble avançado, o export mantém o **mesmo formato**.

## 6) Legal/TOS
Usa apenas APIs/sites conforme os respetivos termos. Este projeto não automatiza apostas; apenas produz dados/estimativas.

Boa sorte e bons sinais EV+! :)
