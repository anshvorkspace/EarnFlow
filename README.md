# Income Studio — Irregular Income Planner

A dark, browser-based cash-flow planner for freelancers, creators, contractors and gig workers.

## Features
- Guided monthly dashboard with plain-language explanations and recent activity
- One-click demo data so new users can understand the dashboard before entering real transactions
- Remove demo transactions with one click
- Income tracker for clients, creator payouts and gig platforms
- Expense tracker with paid/unpaid status
- Customizable reserve allocations (tax, emergency savings, business buffer)
- Low-income scenario simulator
- CSV export for transaction backup
- Local SQLite storage

## Run locally (Windows)
1. Install Python 3.10 or newer.
2. Extract this ZIP folder.
3. Open Command Prompt in the extracted folder.
4. Run:
   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
5. The app opens in your browser, usually at `http://localhost:8501`.

## Run locally (macOS/Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
For a public demo, push `app.py` and `requirements.txt` to a GitHub repository and deploy through Streamlit Community Cloud.

**Important before selling:** this is a starter MVP, not a production multi-user SaaS. It currently uses a local SQLite database without login or tenant isolation. For a paid product, add authentication, per-user cloud storage (for example Supabase), backups, privacy disclosures, and test all calculations with independent test cases. Never deploy this version with real customer financial data as-is.

## Calculation notes
Safe-to-spend = opening cash + received income − paid expenses − unpaid expenses − configured reserves.
Pending income is excluded until marked Received. Reserves are calculated as percentages of received income. Personal pay is the remaining share after configured reserves.

## Brand assets
- `EarnFlow_Logo_Banner.png` is the generated brand banner for marketing/cover use.
- The app header uses a lightweight inline vector-inspired flow mark and the exact EarnFlow wordmark.
