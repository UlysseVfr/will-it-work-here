# Will It Work Here?

An interactive tool to explore **where the results of cash transfer RCTs are likely to generalize**.
Pick a study and see which countries have the most similar context, or pick a country and find
the studies run in contexts most like it. Users choose which context factors matter, and the
similarity scores update live.

> Status: early development (milestone 1, country data pipeline).

## Project structure

```
studies/     One YAML file per cash transfer study, reviewed by the research lead
ingestion/   Python scripts that download raw data (World Bank, WGI, ...)
dbt/         Data models that clean and combine the raw data (coming next)
site/        The public website (coming later)
tests/       Automated tests
data/raw/    Downloaded data (not committed to git)
```

## Run it locally

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

pytest                          # run the tests
python -m ingestion.world_bank  # download country data into data/raw/
```

## Contributing a study

1. Copy `studies/_TEMPLATE.yaml` and name it like `author-2016-ken.yaml`.
2. Fill in the fields (you can do this directly in the GitHub web editor).
3. Open a pull request. Automatic checks tell you if a field is missing or invalid.

Questions, ideas and error reports go in [Issues](../../issues).

## Data sources

- World Bank, World Development Indicators (WDI)
- World Bank, Worldwide Governance Indicators (WGI)
- Global Findex (via WDI)

## Roadmap

1. Country data pipeline (ingestion + dbt models + tests)
2. Study catalogue of cash transfer RCTs
3. Similarity engine with adjustable weights
4. Website v1
5. "How it's built" page and launch
