# Football Analytics with Python + BigQuery

A personal project built to practice SQL, Python, cloud tools, and machine learning, using football data as the subject because it's genuinely interesting to work with. The broader goal behind it is developing skills that carry over into data analytics and data management work, football just happens to be the dataset that made learning it fun.

## Project Goal

Build a complete data pipeline from raw CSVs to a working chatbot, while picking up real skills along the way:

- Loading and structuring data in a cloud data warehouse
- Writing and practicing SQL, from basics through joins and aggregations
- Connecting Python to that data for analysis
- Building and evaluating a machine learning model
- Building a working AI chatbot on top of it all

## Tech Stack

- **Google BigQuery** (Sandbox / free tier), dataset region: asia-south1 (Mumbai)
- **Python 3.14**, with `google-cloud-bigquery`, `pandas`, `scikit-learn`
- **Power BI Desktop**, connected live to BigQuery
- **Google Gemini API**, for natural language to SQL
- **Streamlit**, for the chatbot's web interface

## Data Source

Kaggle dataset: `davidcariboo/player-scores` (Transfermarkt data), covering players, clubs, games, competitions, player valuations, appearances, and match events.

---

## Stage 1: Data Loading

All 9 source tables loaded into BigQuery: `players`, `games`, `clubs`, `competitions`, `player_valuations`, `appearances`, `club games`, `game events`, `game lineups`.

Note: three of these tables have spaces in their names (`club games`, `game events`, `game lineups`) and must always be wrapped in backticks in SQL, for example:

```sql
`football-analytics-507017.football_data.club games`
```

## Stage 2: SQL Practice

Practiced `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, `JOIN`, `LEFT JOIN`, `GROUP BY`, and aggregate functions (`SUM`, `COUNT`, `AVG`) directly in BigQuery, along with basic data quality checks for missing or mismatched values.

## Stage 3: Python + BigQuery

Connected Python to BigQuery using `google-cloud-bigquery`, pulled data into pandas, and practiced filtering, grouping, and basic data cleaning.

One cleaning example: 38 clubs in the `clubs` table had `squad_size = 0`, which also meant missing `average_age` values. These were treated as inactive or defunct clubs and filtered out for analysis:

```python
df = df[df["squad_size"] > 0]
```

## Stage 4: Power BI Dashboard

Built a two page dashboard connected live to BigQuery:

- **Club Overview**: games played, goals scored, home vs away wins, with a club name slicer
- **Financial Insight**: average player valuation by club

Average valuation was used instead of total valuation, since total is skewed by how many historical valuation records a club happens to have, rather than reflecting real player value.

## Stage 5: Match Outcome Prediction

Built a machine learning model to predict match outcomes (`home_win`, `away_win`, `draw`) using historical club valuation, historical win rate, and recent form (points from each club's last 5 matches).

**Key lesson learned**: the first version of this model used historical features calculated from the *entire* dataset, including matches that happened after the one being predicted. This is a data leakage problem, since a real prediction system would never have access to future results. Once features were rebuilt using only information available before each match, and the data was split chronologically (train on past matches, test on future ones) instead of randomly, accuracy dropped, which was expected and is actually a sign the earlier numbers were too optimistic.

Models compared:

| Model | Accuracy | Macro F1 | Draw Recall |
|---|---:|---:|---:|
| Scaled Logistic Regression, random split | 53.86% | 0.39 | 0.00 |
| Balanced Logistic Regression, random split | 48.81% | 0.47 | 0.33 |
| Chronological Logistic Regression | 50.63% | 0.36 | 0.00 |
| Balanced Chronological Logistic Regression | 46.05% | 0.44 | 0.30 |
| Random Forest (chronological) | 49.20% | 0.40 | 0.09 |

**Final model**: Balanced Chronological Logistic Regression. It has lower raw accuracy than some others, but this is a three class problem, and a model can get decent accuracy just by predicting "home win" most of the time. Macro F1 and draw recall matter more here, and this model handles all three outcomes more fairly than the others tested.

This is a learning project, not a production betting or prediction system. It doesn't account for injuries, lineups, tactics, or other real world context.

## Stage 6: GenAI Chatbot

A natural language chatbot that answers questions about the football database, built as a web app with Streamlit.

**How it works:**

1. The app reads the live schema of all tables directly from BigQuery, so it's always accurate even if tables change later
2. Your question, the schema, and the last few questions asked (for follow up context) are sent to Google's Gemini model, which writes a BigQuery SQL query
3. The query is checked to make sure it only reads data (`SELECT` only, nothing that could modify or delete anything)
4. The query runs against BigQuery and the real result comes back
5. Gemini turns that raw result into a plain, readable sentence
6. The last few question and answer pairs are remembered, so follow up questions like "now just show the top 10" or "from those, only players over 30" work correctly

**Known limitations:**

- Follow up memory only keeps the last 3 exchanges, to stay within free tier token limits
- The model occasionally chooses a different table than expected when more than one reasonable path exists to answer a question (for example, using `players.current_club_domestic_competition_id` versus `appearances.competition_id`, which don't always mean exactly the same thing)
- Google changed or retired the underlying Gemini model name several times during development (moved through `gemini-2.0-flash`, `gemini-3.6-flash`, `gemini-2.5-flash-lite`, and finally `gemini-3.5-flash-lite`). Free tier daily request limits also vary a lot between models, so the model name in the code may need updating again in the future if this happens again
- This is not a validated, production grade tool. Generated SQL should be treated as a best effort answer, not a guaranteed correct one

**Setup:**

1. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com)
2. Create a file named `.env.football` in this folder containing:
   ```
   GEMINI_API_KEY=your_key_here
   ```
3. Install dependencies:
   ```
   python -m pip install google-genai google-cloud-bigquery streamlit python-dotenv
   ```
4. Run the chatbot:
   ```
   python -m streamlit run app.py
   ```

`.env.football` is excluded from version control via `.gitignore` and should never be shared or uploaded.

---

## Project Status

| Stage | Status |
|---|---|
| 1. Data Loading | Done |
| 2. SQL Practice | Done |
| 3. Python + BigQuery | Done |
| 4. Power BI Dashboard | Done |
| 5. Match Outcome Prediction | Done |
| 6. GenAI Chatbot | Done |

## Files in This Project

- `stage5_match_prediction.ipynb`: full notebook for the machine learning stage, including all model comparisons
- `ask_football.py`: core chatbot logic (schema reading, SQL generation, safety checks, query execution, answer generation)
- `app.py`: Streamlit web interface, imports its logic from `ask_football.py`
- `.env.football`: holds the Gemini API key (not included in version control)
- `.gitignore`: excludes `.env` and `.env.football` from version control
