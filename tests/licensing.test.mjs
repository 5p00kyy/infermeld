import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
const grant = text => text.slice(text.indexOf('Permission is hereby granted')).replace(/\s+/g, ' ').trim();

test('own MIT grant preserves upstream MIT permissions and separate copyright holders', () => {
  const own = read('LICENSE');
  const upstream = read('LICENSES/llama.cpp-MIT.txt');
  assert.match(own, /^MIT License/);
  assert.match(upstream, /^MIT License/);
  assert.match(own, /Copyright \(c\) 2026 5p00kyy and Infermeld contributors/);
  assert.match(upstream, /Copyright \(c\) 2023-2026 The ggml authors/);
  assert.match(own, /Permission is hereby granted/);
  assert.match(upstream, /Permission is hereby granted/);
  assert.equal(grant(own), grant(upstream));
});

test('documentation distinguishes our license from upstream and experimental release scope', () => {
  const readme = read('README.md');
  const notice = read('THIRD_PARTY.md');
  assert.match(readme, /MIT-licensed under \[LICENSE\]/);
  assert.match(readme, /not a source fork or a bundled engine/);
  assert.match(readme, /source-only experimental release/);
  assert.match(notice, /LICENSES\/llama\.cpp-MIT\.txt/);
  assert.match(notice, /does not replace third-party copyright notices or license terms/);
  assert.doesNotMatch(notice, /Owner selection is pending/);
});
