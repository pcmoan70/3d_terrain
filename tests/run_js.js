// Runs viewer/habitat.js on a fixture (tests/parity.py writes it) and prints the result as JSON.
//   node tests/run_js.js tests/fixtures/preikestolen.json
// The fixture's `h` names a raw little-endian Float32 file next to it (NaN = no data).
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
globalThis.window = globalThis;
vm.runInThisContext(fs.readFileSync(path.join(__dirname, '..', 'viewer', 'habitat.js'), 'utf8'), { filename: 'habitat.js' });
const fx = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const raw = fs.readFileSync(path.join(path.dirname(process.argv[2]), fx.h));
const h = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
const t0 = Date.now();
const res = window.Habitat.compute(h, fx.n, fx.c, { X: fx.X, Y: fx.Y, R: fx.R, people: fx.people || null });
res.ms = Date.now() - t0;
res.rules = window.Habitat.rules;
process.stdout.write(JSON.stringify(res, (k, v) => (v === Infinity ? 'Infinity' : v)));
