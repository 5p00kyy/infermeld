import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {METRICS, validateResults} from '../site/data.mjs';

const measured = JSON.parse(readFileSync(new URL('../site/results.json', import.meta.url)));

test('short-prompt rates retain actual token counts, duration and cache status', () => {
  for (const row of measured.rows) {
    assert.ok(Number.isInteger(row.prompt_tokens) && row.prompt_tokens > 0, 'Prompt-processing token count must not be omitted');
    assert.ok(Number.isFinite(row.prompt_ms) && row.prompt_ms > 0);
    assert.equal(row.cached_prompt_tokens, 0);
    assert.ok(Math.abs(row.prompt_tokens * 1000 / row.prompt_ms - row.prefill_tps) < 1e-8);
  }
});

test('prefill description explicitly disclaims sustained throughput', () => {
  assert.match(METRICS.prefill_tps, /short.prompt/i);
  assert.match(METRICS.prefill_tps, /not.*sustained/i);
});

test('duration and rate disagreement cannot be published as a valid measurement', () => {
  const corrupt = structuredClone(measured);
  corrupt.rows[0].prompt_ms = 1;
  assert.throws(() => validateResults(corrupt));
});
