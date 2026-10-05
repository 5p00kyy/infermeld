import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as data from '../site/data.mjs';

const measured = JSON.parse(readFileSync(new URL('../site/results.json', import.meta.url)));

test('chart derives two rows and real acceptance from the retained measurements', () => {
  assert.equal(typeof data.selectRows, 'function', 'measurement selection is not implemented');
  const rows = data.selectRows(measured, 'code', 'decode_tps');
  assert.equal(rows.length, 2);
  assert.equal(rows[0].value, 55.64241894908566);
  assert.equal(rows[1].value, 144.23766302243106);
  assert.equal(rows[1].width, 100);
  assert.equal(rows[0].acceptance, 391 / 476);
});

test('different metrics use different measured values, not reused decode values', () => {
  assert.equal(typeof data.selectRows, 'function');
  const rows = data.selectRows(measured, 'prose', 'end_to_end_tps');
  assert.equal(rows[0].value, 30.4468800748326);
  assert.equal(rows[1].value, 86.85783181383022);
});

test('corrupt counters, duplicate rows and unrecognized metrics fail closed', () => {
  assert.equal(typeof data.validateResults, 'function');
  const corrupted = structuredClone(measured);
  corrupted.rows[0].accepted = corrupted.rows[0].drafted + 1;
  assert.throws(() => data.validateResults(corrupted));
  const duplicates = structuredClone(measured);
  duplicates.rows.push(duplicates.rows[0]);
  assert.throws(() => data.validateResults(duplicates));
  assert.throws(() => data.selectRows(measured, 'code', 'invented_metric'));
  assert.throws(() => data.selectRows(measured, 'invented_workload', 'decode_tps'));
});

test('nonfinite or empty throughput never becomes a credible chart', () => {
  assert.equal(typeof data.validateResults, 'function');
  for (const value of [NaN, Infinity, -1, 0, null]) {
    const bad = structuredClone(measured);
    bad.rows[0].decode_tps = value;
    assert.throws(() => data.validateResults(bad));
  }
});

test('public record retains the scope, pin and a single repetition', () => {
  assert.match(measured.status, /not a clean-checkout/);
  assert.match(measured.source_pin, /^[a-f0-9]{40}$/);
  assert.match(measured.binary_sha256, /^[a-f0-9]{64}$/);
  assert.equal(measured.repetitions, 1);
  assert.equal(measured.rows.length, 4);
  assert.ok(measured.rows.every(row => row.finish_reason === 'length' && row.output_tokens === 512));
});
