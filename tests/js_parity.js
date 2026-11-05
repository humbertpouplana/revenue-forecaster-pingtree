// Runs the calculation block embedded in the HTML prototype and prints a few results as JSON.
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const D = JSON.parse(html.match(/const D = (\{.*?\});\nconst PARAMS/s)[1]);
const PARAMS = JSON.parse(html.match(/const PARAMS = (\{.*?\});\n/s)[1]);
const calc = html.split('/*CALC*/')[1].split('/*ENDCALC*/')[0];
const f = new Function('PARAMS', calc + ';return {forecast,monteCarlo};')(PARAMS);
const cfg = {months: PARAMS.aggregation_months, minAcc: PARAMS.min_accepted, ovr: {}, excl: new Set(), kA: 1, kE: 1, leads: PARAMS.leads, n: PARAMS.offers, pen: 0};
const F = f.forecast(D.partners, cfg), Fr = f.forecast(D.partners, {...cfg, reach: true});
const mc = f.monteCarlo(F.rows, cfg.leads, PARAMS.monte_carlo.sims, PARAMS.monte_carlo.seed);
console.log(JSON.stringify({rev: F.rev, reach: Fr.rev, p10: mc.p10, p90: mc.p90, eligible: F.eligible}));
