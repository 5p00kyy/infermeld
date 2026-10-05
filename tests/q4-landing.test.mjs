import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const landing = () => readFileSync(new URL('../site/index.html', import.meta.url), 'utf8');

test('landing leads with Q4 allocation evidence, not Q3 throughput', () => {
  const html = landing();
  assert.match(html, /Q4 capacity/);
  assert.doesNotMatch(html, /id="chart"/);
  assert.doesNotMatch(html, /infermeld\.py build/);
  assert.match(html, /not full-length/);
  assert.match(html, /history\.html/);
  assert.match(html, /https:\/\/github\.com\/5p00kyy\/infermeld/);
});

test('every displayed Q4 row matches the exported evidence, including the retry split', () => {
  const data = JSON.parse(readFileSync(new URL('../site/capacity.json', import.meta.url), 'utf8'));
  const html = landing();
  assert.equal(data.models.length, 2);
  let checks = 0;
  for (const model of data.models) {
    assert.match(model.sha256, /^[a-f0-9]{64}$/);
    assert.ok(Number.isSafeInteger(model.bytes) && model.bytes > 0);
    assert.match(model.artifact, /UD-Q4_K_M\.gguf$/);
    assert.match(model.source_repository, /^unsloth\//);
    assert.match(model.source_revision, /^[a-f0-9]{40}$/);
    assert.equal(model.quantization_publisher, 'Unsloth');
    assert.equal(model.publisher_declared_license, 'apache-2.0');
    assert.deepEqual(model.cases.map(c => c.context_reserved), [8192, 32768, 65536, 131072]);
    for (const c of model.cases) {
      const row = new RegExp(`<tr[^>]*data-family="${model.family}" data-context="${c.context_reserved}" data-result="passed"[^>]*>([\\s\\S]*?)</tr>`).exec(html);
      assert.ok(row, `missing ${model.family} / ${c.context_reserved}`);
      assert.match(row[1], new RegExp(`>${c.context_reserved.toLocaleString('en-US')}</th>`));
      assert.match(row[1], new RegExp(`<td>${c.split}</td>`));
      assert.match(row[1], new RegExp(`<td>${c.short_checks_passed} / 4(?:<|$)`));
      checks += c.short_checks_passed;
    }
  }
  assert.equal(checks, 32);
  assert.equal((html.match(/data-result="passed"/g) || []).length, 8);
  assert.equal((html.match(/data-result="failed"/g) || []).length, data.failed_conditions.length);
  assert.equal(data.models[0].cases.at(-1).split, '2:1');
  assert.equal(data.failed_conditions.length, 1);
  assert.equal(data.failed_conditions[0].split, '3:2');
  for (const failure of data.failed_conditions) {
    const row = new RegExp(`<tr[^>]*data-family="${failure.family}" data-context="${failure.context_reserved}" data-result="failed"[^>]*>([\\s\\S]*?)</tr>`).exec(html);
    assert.ok(row, 'failed condition must be a visible row');
    assert.ok(row[1].includes(`<td>${failure.split}</td>`));
    assert.ok(row[1].includes('Load failed'));
    assert.ok(row[1].includes('Checks not reached'));
    assert.ok(!row[1].includes('4 / 4'));
  }
  assert.equal(data.long_context_quality_tested, false);
  assert.equal(data.sustained_q4_throughput_tested, false);
});

test('Q3 chart survives in history with an explicit quant boundary', () => {
  const html = readFileSync(new URL('../site/history.html', import.meta.url), 'utf8');
  assert.match(html, /Not Q4 speeds/);
  assert.match(html, /id="chart"/);
  assert.match(html, /src="app\.mjs"/);
  assert.match(html, /href="index\.html"/);
});

test('Q4 export contains no private operational paths or receipt handles', () => {
  const text = readFileSync(new URL('../site/capacity.json', import.meta.url), 'utf8');
  assert.doesNotMatch(text, /\/root\/|\/mnt\/|192\.168\.|LACT|\/run\/|receipts\/|trial\.lock/i);
});

test('public evidence omits rig cooling diagnostics, without hiding incomplete qualification', () => {
  for (const name of ['capacity.json', 'results.json']) {
    const text = readFileSync(new URL(`../site/${name}`, import.meta.url), 'utf8');
    assert.doesNotMatch(text, /peak_junction|thermal_trip|fan_rpm|power_cap/);
  }
  assert.doesNotMatch(landing(), /Peak junction/);
  assert.match(landing(), /Neither model has a proven maximum usable context/);
});
