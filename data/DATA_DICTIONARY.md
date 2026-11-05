# Data dictionary

## partner_monthly.csv  (one row per partner and month; 42 partners x 14 months, 588 rows)

| column | type | meaning |
|---|---|---|
| `partner_id` | string `P01`..`P42` | pseudonymised buyer identifier. The mapping to commercial names is kept in `data/private/partner_names.csv`, which is git-ignored and never published |
| `month` | `YYYY-MM` | calendar month, January 2025 to February 2026 (14 months) |
| `requests` | integer | leads offered ("pinged") to the partner in the month |
| `accepted` | integer | leads accepted by the partner (`accepted <= requests`) |
| `sales` | integer | sales reported by the partner on accepted leads (0 when the partner pays per accepted lead and reports no sales) |
| `revenue_eur` | decimal | revenue paid by the partner for the month, in euros |

Derived quantities used by the model: acceptance rate `a = accepted / requests`, earnings per lead `EPL = revenue_eur / accepted`, reach `q = requests / N_ref` (see README).

Integrity rules checked by `tests/test_model.py`: `requests >= accepted >= sales >= 0`, `revenue_eur >= 0`, 42 partners, no commercial names in the file.

## Origin and anonymisation
Anonymised data sources: partner-level monthly reporting aggregates. Partner identifiers are pseudonymised and shuffled, no campaign, user or account identifiers are present, and the commercial-name mapping is never committed. Treat the file as confidential even though it is anonymised.

## params.json
Every parameter used by the Python model, the HTML prototype and the paper (aggregation months, volatility window, minimum accepted leads, number of offers, Monte Carlo sims and seed, backtest settings). Change a value here and rerun `make all`.
