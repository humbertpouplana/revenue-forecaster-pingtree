"""The HTML prototype keeps a JavaScript mirror of the model so it runs standalone in a browser.
This test guarantees the mirror and the Python reference give the same numbers."""
import json
import shutil
import subprocess
import pytest
from pingtree_forecaster import data, model

ROOT = data.ROOT


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_prototype_matches_python():
    html = ROOT / "prototype" / "index.html"
    if not html.exists():
        pytest.skip("run `make prototype` first")
    out = json.loads(subprocess.run(["node", str(ROOT / "tests" / "js_parity.js"), str(html)], capture_output=True, text=True, check=True).stdout)
    P, D = data.load_params(), data.load_partners()
    cfg = model.default_cfg(P)
    F = model.forecast(D["partners"], cfg, P)
    Fr = model.forecast(D["partners"], cfg, P, reach=True)
    mc = model.monte_carlo(F["rows"], cfg["leads"], P["monte_carlo"]["sims"], P["monte_carlo"]["seed"])
    assert out["rev"] == pytest.approx(F["rev"], rel=1e-9)
    assert out["reach"] == pytest.approx(Fr["rev"], rel=1e-9)
    assert out["p10"] == pytest.approx(mc["p10"], rel=1e-9) and out["p90"] == pytest.approx(mc["p90"], rel=1e-9)
    assert out["eligible"] == F["eligible"]
