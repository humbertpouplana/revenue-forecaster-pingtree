"""Build prototype/index.html from template.html + data/ + data/params.json.

    python prototype/build_prototype.py            # anonymised partner ids (default, safe to publish)
    python prototype/build_prototype.py --named    # uses data/private/partner_names.csv if present (never commit the output)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pingtree_forecaster import data  # noqa: E402


def main(named: bool = False, out: Path | None = None) -> Path:
    params = data.load_params()
    names = data.load_private_names() if named else {}
    d = data.load_partners(names=names)
    payload = {"months": d["months"], "partners": [{"name": p["name"], "m": p["m"]} for p in d["partners"]], "source": "Fuentes anonimizadas de datos"}
    tpl = (ROOT / "prototype" / "template.html").read_text(encoding="utf-8")
    html = (tpl.replace("__DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
               .replace("__PARAMS__", json.dumps(params, separators=(",", ":")))
               .replace("__AGG_MONTHS__", " y ".join(params["aggregation_months"]))
               .replace("__VOL_FROM__", params["volatility_from"]))
    out = out or ROOT / "prototype" / ("index.named.html" if named else "index.html")
    out.write_text(html, encoding="utf-8")
    print("built", out, len(html), "bytes")
    return out


if __name__ == "__main__":
    main("--named" in sys.argv)
