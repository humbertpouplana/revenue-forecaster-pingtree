"""Reconciliation with realised revenue and walk-forward backtest.

Actual revenue of a month is the sum over partners of the revenue column of the dataset.
Lead volume N_t of a month is the largest request volume received by any partner that month
(the first position of a pingtree sees every lead). It is an *input* of the forecast, as in the tool.
"""
from __future__ import annotations
import statistics
from . import model


def actual_revenue(partners, month):
    return sum(p["m"][month][3] for p in partners if month in p["m"])


def lead_volume(partners, month):
    return max((p["m"][month][0] for p in partners if month in p["m"]), default=0)


def _ordered(pool, order):
    key = (lambda p: -p["epl"]) if order == "epl" else (lambda p: -p["R"])
    return sorted(pool, key=key)


def predict(partners, params, train, target, reach=True, order="epl", min_acc=None):
    cfg = model.default_cfg(params)
    cfg.update(months=list(train), min_acc=params["backtest"]["min_accepted"] if min_acc is None else min_acc, reach=reach)
    pool = _ordered(model.build_pool(partners, cfg, params), order)
    n = lead_volume(partners, target)
    return model.run_flow(pool, n, 0.0, 1.0, 1.0, reach)["rev"]


def in_sample(data, params, order="requests"):
    """Month by month: the model fed with the same month's rates versus that month's realised revenue."""
    P = data["partners"]
    out = []
    for m in data["months"]:
        a = actual_revenue(P, m)
        f = predict(P, params, [m], m, True, order, 0)
        out.append({"month": m, "actual": a, "model": f, "ratio": f / a if a else None})
    return out


def walk_forward(data, params, reach=True, order="epl"):
    P = data["partners"]; ms = data["months"]; k = params["backtest"]["train_months"]
    out = []
    for i in range(k, len(ms)):
        tr, t = ms[i - k:i], ms[i]
        a = actual_revenue(P, t)
        f = predict(P, params, tr, t, reach, order)
        prev = sum(actual_revenue(P, x) for x in tr); prev_n = sum(lead_volume(P, x) for x in tr)
        naive = prev / prev_n * lead_volume(P, t) if prev_n else None
        out.append({"month": t, "actual": a, "model": f, "naive": naive})
    return out


def summarize(rows, key="model"):
    err = [(r[key] - r["actual"]) / r["actual"] for r in rows if r[key] is not None and r["actual"]]
    return {"mape": statistics.mean(abs(e) for e in err), "bias": statistics.mean(err), "n": len(err)}


def run(data, params):
    wf = walk_forward(data, params)
    wf_full = walk_forward(data, params, reach=False)
    ins = in_sample(data, params)
    return {
        "in_sample": ins,
        "in_sample_ratio_mean": statistics.mean(r["ratio"] for r in ins),
        "walk_forward": wf,
        "walk_forward_summary": {"reach_adjusted": summarize(wf), "naive_run_rate": summarize(wf, "naive"),
                                  "full_reach": summarize(wf_full)},
        "full_reach_median_ratio": statistics.median(r["model"] / r["actual"] for r in wf_full),
    }
