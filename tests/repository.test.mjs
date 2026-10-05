import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync, readFileSync, readdirSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const read = path => readFileSync(join(root, path), 'utf8');

test('repository has one CPU-only check entrypoint and read-only CI', () => {
  const makefile = read('Makefile');
  assert.match(makefile, /-m unittest discover -s tests -v/);
  assert.match(makefile, /--test tests\/\*\.test\.mjs/);
  const workflow = read('.github/workflows/checks.yml');
  assert.match(workflow, /contents: read/);
  assert.match(workflow, /run: make test/);
  assert.doesNotMatch(workflow, /self-hosted|contents: write|id-token: write|llama-server|nvcc|nvidia-smi|deploy|release create/);
  assert.match(read('CONTRIBUTING.md'), /not GPU benchmarks/);
});

test('repository documentation has no broken relative file links', () => {
  const docs = readdirSync(root).filter(name => name.endsWith('.md'));
  docs.push(...readdirSync(join(root, 'docs')).filter(name => name.endsWith('.md')).map(name => `docs/${name}`));
  for (const name of docs) {
    for (const match of read(name).matchAll(/\]\(([^\s)]+)\)/g)) {
      const target = match[1].split('#')[0];
      if (!target || /^(?:https?:|mailto:)/.test(target)) continue;
      const path = resolve(dirname(join(root, name)), target);
      assert.ok(path.startsWith(root), `link escapes repository: ${name}`);
      assert.ok(existsSync(path), `missing ${target} linked by ${name}`);
    }
  }
  assert.match(read('README.md'), /docs\/EVIDENCE\.md/);
  assert.match(read('README.md'), /Python 3\.11/);
});

test('sanitized CLI acceptance is bound to the unchanged launcher and exact Q4 artifact', () => {
  const record = JSON.parse(read('site/cli-acceptance.json'));
  const capacity = JSON.parse(read('site/capacity.json'));
  const model = capacity.models.find(model => model.family === 'moe');
  assert.equal(record.source_pin, capacity.source_pin);
  assert.equal(record.cli_sha256, createHash('sha256').update(readFileSync(join(root, 'infermeld.py'))).digest('hex'));
  assert.equal(record.model.sha256, model.sha256);
  assert.equal(record.model.bytes, model.bytes);
  assert.equal(record.model.source_revision, model.source_revision);
  assert.equal(record.throughput_qualified, false);
  assert.equal(record.full_length_context_qualified, false);
  assert.equal(record.gpu_control_configuration_preserved, true);
  assert.deepEqual(record.cases.map(c => c.mtp), [0, 4]);
  for (const c of record.cases) {
    assert.equal(c.context_reserved, 8192);
    assert.equal(c.split, '3,2');
    assert.equal(c.microbatch, 32);
    assert.equal(c.speculative, Boolean(c.mtp));
    assert.equal(c.shutdown_exit, 143);
    assert.deepEqual(c.checks.map(check => check.case), ['exact', 'json', 'retrieval', 'prose']);
    assert.ok(c.checks.every(check => check.passed === true));
  }
  assert.ok(record.engine_cohort_sha256['llama-server']);
  for (const digest of Object.values(record.engine_cohort_sha256)) assert.match(digest, /^[a-f0-9]{64}$/);
  assert.doesNotMatch(read('site/cli-acceptance.json'), /\/root\/|\/home\/|\/mnt\/|192\.168\.|peak_junction|thermal_trip|fan_rpm|power_cap|LACT|"response"/i);
});

test('community reports ask for reproducible topology and allow unknowns', () => {
  const form = read('.github/ISSUE_TEMPLATE/hardware_report.yml');
  assert.match(form, /unknown/);
  for (const id of ['result', 'topology', 'engine', 'model', 'reproduction', 'measurements']) {
    assert.match(form, new RegExp(`id: ${id}\\b`));
  }
  assert.match(form, /credentials/);
  assert.match(form, /Aborted/);
});
