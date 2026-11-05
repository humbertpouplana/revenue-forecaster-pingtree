import math
import pytest
from pingtree_forecaster import data, model, backtest, results

P = data.load_params()
D = data.load_partners()
CFG = model.default_cfg(P)


def test_reproduces_headline_115371():
    F = model.forecast(D["partners"], CFG, P)
    assert round(F["rev"]) == 115371
    assert F["eligible"] == 40


def test_monte_carlo_range_matches_documented_values():
    F = model.forecast(D["partners"], CFG, P)
    mc = model.monte_carlo(F["rows"], CFG["leads"], P["monte_carlo"]["sims"], P["monte_carlo"]["seed"])
    assert round(mc["p10"]) == 102231 and round(mc["p90"]) == 129196


def test_flow_conserves_leads():
    F = model.forecast(D["partners"], CFG, P)
    assert math.isclose(F["accepted"] + F["left"], CFG["leads"], rel_tol=1e-12)


def test_epl_descending_order_is_optimal_vs_random_permutations():
    import random
    pool = model.sorted_pool(D["partners"], CFG, P)[: CFG["n"]]
    best = model.run_flow(pool, CFG["leads"])["rev"]
    rnd = random.Random(1)
    for _ in range(300):
        a = pool[:]; rnd.shuffle(a)
        assert model.run_flow(a, CFG["leads"])["rev"] <= best + 1e-6


def test_independent_closed_form():
    """Revenue formula N * sum a_i e_i prod_{j<i}(1-a_j) computed independently of run_flow."""
    pool = model.sorted_pool(D["partners"], CFG, P)[: CFG["n"]]
    surv, tot = 1.0, 0.0
    for p in pool:
        tot += surv * p["acc"] * p["epl"]; surv *= 1 - p["acc"]
    assert math.isclose(tot * CFG["leads"], model.run_flow(pool, CFG["leads"])["rev"], rel_tol=1e-12)


def test_mulberry32_is_deterministic_and_in_unit_interval():
    a = [model.mulberry32(7)() for _ in range(2)]
    assert a[0] == a[1]
    r = model.mulberry32(20261103)
    xs = [r() for _ in range(1000)]
    assert all(0 <= x < 1 for x in xs) and abs(sum(xs) / 1000 - 0.5) < 0.05


def test_params_are_single_source_of_truth():
    assert CFG["months"] == P["aggregation_months"]
    assert P["monte_carlo"]["sims"] == 2000


def test_dataset_integrity():
    assert len(D["partners"]) == 42
    for p in D["partners"]:
        for m, (r, a, s, v) in p["m"].items():
            assert r >= a >= 0 and a >= s >= 0 and v >= 0


def test_no_commercial_names_in_public_dataset():
    names = set(data.load_private_names().values())
    text = (data.DATA / "partner_monthly.csv").read_text(encoding="utf-8")
    assert all(n not in text for n in names)


# ------------------------------------------------------------------ reconciliation with realised revenue
def test_reach_adjusted_model_reconciles_with_actual_revenue_in_sample():
    rows = backtest.in_sample(D, P)
    ratios = [r["ratio"] for r in rows]
    assert all(0.85 <= x <= 1.05 for x in ratios), ratios


def test_walk_forward_error_within_tolerance_and_better_than_full_reach():
    wf = backtest.walk_forward(D, P)
    s = backtest.summarize(wf)
    assert s["mape"] <= P["backtest"]["tolerance_mape"]
    full = backtest.summarize(backtest.walk_forward(D, P, reach=False))
    assert full["mape"] > 10 * s["mape"]


def test_full_reach_headline_is_a_ceiling_not_a_forecast():
    full = model.forecast(D["partners"], CFG, P)["rev"]
    reach = model.forecast(D["partners"], CFG, P, reach=True)["rev"]
    assert full > 5 * reach


def test_results_json_is_current():
    import json
    res = json.loads((data.ROOT / "results" / "results.json").read_text(encoding="utf-8"))
    assert round(res["p1"]["rev"]) == round(model.forecast(D["partners"], CFG, P)["rev"])
    import pingtree_forecaster
    assert res["model_version"] == pingtree_forecaster.__version__


def test_readme_quotes_current_headline():
    readme = (data.ROOT / "README.md").read_text(encoding="utf-8")
    assert "115,371" in readme
