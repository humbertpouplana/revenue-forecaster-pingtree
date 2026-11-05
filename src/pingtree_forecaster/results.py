"""Compute every number used by the paper, the README and the tests; write results/results.json.

Run:  python -m pingtree_forecaster.results
"""
from __future__ import annotations
import json
from pathlib import Path
from . import data as D, model as M, backtest as B, __version__


def build(partners_data: dict, params: dict) -> dict:
    P = partners_data["partners"]
    cfg = M.default_cfg(params)
    N = cfg["leads"]
    F = M.forecast(P, cfg, params)
    pool = M.sorted_pool(P, cfg, params)
    mcp = params["monte_carlo"]
    mc = M.monte_carlo(F["rows"], N, mcp["sims"], mcp["seed"])
    out = {"model_version": __version__, "params": params}
    p1 = {
        "rev": F["rev"], "perLead": F["perLead"], "cov": F["coverage"], "eplAvg": F["eplAvg"], "left": F["left"],
        "accepted": F["accepted"], "eligible": F["eligible"],
        "rows": [{"pos": r["pos"], "acc": r["accEff"], "epl": r["eplEff"], "in": r["in"], "accepted": r["accepted"], "rev": r["rev"], "A": r["A"]} for r in F["rows"]],
        "marg": [M.run_flow(pool[: i + 1], N, 0.0)["rev"] for i in range(min(30, len(pool)))],
        "hhi": M.hhi(F["rows"], F["rev"]),
        "mc": {"p10": mc["p10"], "p50": mc["p50"], "p90": mc["p90"], "samples": mc["samples"][::10]},
    }
    cut = pool[: cfg["n"]]
    by = lambda g, d: M.run_flow(sorted(cut, key=lambda p: -d * g(p)), N, 0.0)["rev"]
    rnd = M.mulberry32(params["random_order"]["seed"])
    acc = 0.0
    runs = params["random_order"]["runs"]
    for _ in range(runs):
        a = list(cut)
        for i in range(len(a) - 1, 0, -1):
            j = int(rnd() * (i + 1))
            a[i], a[j] = a[j], a[i]
        acc += M.run_flow(a, N, 0.0)["rev"]
    p1["order"] = {"epl_desc": by(lambda p: p["epl"], 1), "acc_desc": by(lambda p: p["acc"], 1), "rev_hist": by(lambda p: p["V"], 1),
                   "random": acc / runs, "epl_asc": by(lambda p: p["epl"], -1)}
    base = F["rev"]
    d = lambda **o: (M.forecast(P, cfg, params, **o)["rev"] - base) / base * 100
    p1["sens"] = {"acc_up": d(acc_mul=1.1), "acc_dn": d(acc_mul=0.9), "epl_up": d(epl_mul=1.1), "epl_dn": d(epl_mul=0.9),
                  "pen30": d(pen=0.3), "n10": d(n=10), "n30": d(n=30)}
    p1["pen"] = [[p, M.forecast(P, cfg, params, pen=p)["rev"]] for p in [0, .1, .2, .3, .4, .5]]
    p1["nsweep"] = [[n, M.forecast(P, cfg, params, n=n)["rev"]] for n in [5, 10, 15, 20, 25, 30]]
    p1["minsweep"] = [[m, (x := M.forecast(P, cfg, params, min_acc=m))["rev"], x["eligible"]] for m in [0, 50, 200, 1000]]
    p1["months"] = [M.forecast(P, cfg, params, months=[m])["rev"] for m in cfg["months"]]
    # reach-adjusted (calibrated) scenario
    Fr = M.forecast(P, cfg, params, reach=True)
    mcr = M.monte_carlo(Fr["rows"], N, mcp["sims"], mcp["seed"])
    p1["reach"] = {"rev": Fr["rev"], "perLead": Fr["perLead"], "p10": mcr["p10"], "p50": mcr["p50"], "p90": mcr["p90"],
                   "coverage": Fr["coverage"], "ceiling_ratio": F["rev"] / Fr["rev"]}
    p1["backtest"] = B.run(partners_data, params)
    out["p1"] = p1
    return out


def main(out: str | Path | None = None) -> dict:
    params = D.load_params()
    res = build(D.load_partners(), params)
    path = Path(out) if out else D.ROOT / "results" / "results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"results written to {path}: baseline {res['p1']['rev']:,.0f} EUR, reach-adjusted {res['p1']['reach']['rev']:,.0f} EUR")
    return res


if __name__ == "__main__":
    main()
