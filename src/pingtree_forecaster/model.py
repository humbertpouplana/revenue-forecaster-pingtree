"""Sequential-flow pingtree model.

Leads reaching position i:  L_i = N * prod_{j<i} (1 - a_j)
Revenue:                    R   = N * sum_i a_i e_i prod_{j<i} (1 - a_j)

With `reach=True` each partner is only queried for a fraction q_i = min(1, R_i / N_ref)
of the leads that reach it (N_ref = sum over months of the largest request volume),
which is what reconciles the model with realised revenue (see backtest.py).
"""
from __future__ import annotations
import math

M32 = 0xFFFFFFFF


# ---------------------------------------------------------------- RNG (bit-exact port of the prototype's mulberry32)
def _imul(a: int, b: int) -> int:
    return (a * b) & M32


def mulberry32(seed: int):
    a = seed & M32

    def rnd() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & M32
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & M32) ^ t
        return ((t ^ (t >> 14)) & M32) / 4294967296

    return rnd


def gauss(r) -> float:
    u = v = 0.0
    while u == 0:
        u = r()
    while v == 0:
        v = r()
    return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)


# ---------------------------------------------------------------- aggregation
def agg_partner(p: dict, months: list[str]) -> dict:
    R = A = S = V = 0
    for m in months:
        x = p["m"].get(m)
        if x:
            R += x[0]; A += x[1]; S += x[2]; V += x[3]
    return {"R": R, "A": A, "S": S, "V": V}


def n_ref(partners: list[dict], months: list[str]) -> float:
    """Reference lead volume: sum over months of the largest partner request volume."""
    tot = 0
    for m in months:
        tot += max((p["m"][m][0] for p in partners if m in p["m"]), default=0)
    return tot


def monthly_cv(p: dict, start: str, params: dict) -> tuple[float, float]:
    mc = params["monte_carlo"]
    acc, epl = [], []
    for m in sorted(p["m"]):
        if m < start:
            continue
        x = p["m"][m]
        if x[0] > 0 and x[1] > 0 and x[3] > 0:
            acc.append(x[1] / x[0]); epl.append(x[3] / x[1])

    def cv(a):
        if len(a) < 2:
            return mc["cv_default"]
        mu = sum(a) / len(a)
        sd = math.sqrt(sum((v - mu) ** 2 for v in a) / (len(a) - 1))
        return min(mc["cv_cap"], max(mc["cv_floor"], sd / mu))

    return cv(acc), cv(epl)


def default_cfg(params: dict) -> dict:
    return {"months": list(params["aggregation_months"]), "min_acc": params["min_accepted"], "ovr": {}, "excl": set(),
            "kA": params["acceptance_multiplier"], "kE": params["epl_multiplier"], "leads": params["leads"],
            "n": params["offers"], "pen": params["position_penalty"], "reach": False,
            "acc_mul": 1.0, "epl_mul": 1.0}


# ---------------------------------------------------------------- pool and flow
def build_pool(partners: list[dict], cfg: dict, params: dict) -> list[dict]:
    pool = []
    nref = n_ref(partners, cfg["months"])
    for p in partners:
        g = agg_partner(p, cfg["months"])
        if g["V"] <= 0 or g["A"] < cfg["min_acc"] or g["R"] <= 0 or p["name"] in cfg["excl"]:
            continue
        o = cfg["ovr"].get(p["name"], {})
        acc_h = g["A"] / g["R"]
        epl_h = g["V"] / g["A"]
        sold_per_acc = min(1.0, g["S"] / g["A"]) if g["A"] else 0.0
        acc = o["acc"] if o.get("acc") is not None else min(1.0, acc_h * cfg["kA"])
        epl = o["epl"] if o.get("epl") is not None else epl_h * cfg["kE"]
        cva, cve = monthly_cv(p, params["volatility_from"], params)
        pool.append({"name": p["name"], "R": g["R"], "A": g["A"], "S": g["S"], "V": g["V"], "accH": acc_h, "eplH": epl_h,
                     "soldPerAcc": sold_per_acc, "hasSold": g["S"] > 0, "acc": acc, "epl": epl,
                     "q": min(1.0, g["R"] / nref) if nref else 1.0, "cvA": cva, "cvE": cve, "m": p["m"]})
    return pool


def run_flow(pool: list[dict], leads: float, pen: float = 0.0, acc_mul: float = 1.0, epl_mul: float = 1.0, reach: bool = False) -> dict:
    rem = leads
    rows = []
    n = len(pool)
    for i, p in enumerate(pool):
        f = 1 - pen * (i / (n - 1)) if n > 1 else 1
        acc = max(0.0, min(1.0, p["acc"] * f * acc_mul * (p["q"] if reach else 1.0)))
        inn = rem
        accepted = inn * acc
        rev = accepted * p["epl"] * epl_mul
        sold = accepted * p["soldPerAcc"]
        rem = inn - accepted
        rows.append({**p, "pos": i + 1, "accEff": acc, "eplEff": p["epl"] * epl_mul, "in": inn, "accepted": accepted, "rev": rev, "sold": sold, "rem": rem})
    rev = sum(r["rev"] for r in rows); accepted = sum(r["accepted"] for r in rows); sold = sum(r["sold"] for r in rows)
    return {"rows": rows, "rev": rev, "accepted": accepted, "sold": sold, "left": rem,
            "perLead": rev / leads if leads else 0.0, "coverage": accepted / leads if leads else 0.0,
            "eplAvg": rev / accepted if accepted else 0.0}


def sorted_pool(partners, cfg, params):
    return sorted(build_pool(partners, cfg, params), key=lambda p: -p["epl"])


def forecast(partners: list[dict], cfg: dict, params: dict, **over) -> dict:
    c = {**cfg, **over}
    pool = sorted_pool(partners, c, params)
    out = run_flow(pool[: c["n"]], c["leads"], c["pen"], c.get("acc_mul", 1.0), c.get("epl_mul", 1.0), c.get("reach", False))
    return {"eligible": len(pool), **out}


# ---------------------------------------------------------------- uncertainty and concentration
def monte_carlo(rows: list[dict], leads: float, sims: int, seed: int) -> dict:
    r = mulberry32(seed)
    out = []
    for _ in range(sims):
        rem = leads
        rev = 0.0
        for p in rows:
            nA = math.exp(p["cvA"] * gauss(r) - p["cvA"] ** 2 / 2)
            nE = math.exp(p["cvE"] * gauss(r) - p["cvE"] ** 2 / 2)
            acc = min(1.0, p["accEff"] * nA)
            a = rem * acc + math.sqrt(max(0.0, rem * acc * (1 - acc))) * gauss(r)
            a = max(0.0, min(rem, a))
            rev += a * p["eplEff"] * nE
            rem -= a
        out.append(rev)
    out.sort()
    q = lambda f: out[min(len(out) - 1, int(f * len(out)))]
    return {"p10": q(0.1), "p50": q(0.5), "p90": q(0.9), "samples": out}


def hhi(rows: list[dict], total: float) -> float:
    return sum((r["rev"] / total if total else 0.0) ** 2 for r in rows) * 10000
