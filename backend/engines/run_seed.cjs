'use strict';

const seed = require('@uuon-foundation/phyllotaxis-seed-engine/api/lib/seed.js');

const raw = process.argv[2];
const width = Number(process.argv[3] || 800);
const height = Number(process.argv[4] || 800);

if (!raw) {
  console.error('Missing P-vector JSON argument');
  process.exit(2);
}

let p;
try {
  p = JSON.parse(raw);
} catch (err) {
  console.error(`Invalid P-vector JSON: ${err.message}`);
  process.exit(2);
}

try {
  const field = seed.computeField(p, width, height, 0);

  process.stdout.write(JSON.stringify({
    engine: 'phyllotaxis-seed',
    engine_version: '2.0.0',
    width,
    height,
    field
  }));
} catch (err) {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
}
