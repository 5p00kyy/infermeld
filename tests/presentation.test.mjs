import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');

test('README pairs responsive identity with honest, linked project statuses', () => {
  const readme = read('README.md');
  assert.match(readme, /<p align="center">\s*<picture>/);
  assert.match(readme, /<picture>/);
  assert.match(readme, /media="\(max-width: 600px\)"/);
  assert.match(readme, /assets\/infermeld-banner-compact\.svg/);
  for (const badge of ['status', 'version', 'python', 'platform', 'license']) {
    assert.match(readme, new RegExp(`assets/badges/${badge}\\.svg`));
  }
  assert.match(readme, /\[!\[Source checks: CPU-only\]\(https:\/\/github\.com\/5p00kyy\/infermeld\/actions\/workflows\/checks\.yml\/badge\.svg\?branch=main&event=push\)\]\(https:\/\/github\.com\/5p00kyy\/infermeld\/actions\/workflows\/checks\.yml\)/);
  assert.match(readme, /Hardware acceptance and source CI are separate/);
  assert.match(readme, /releases\/tag\/v0\.1\.0/);
  assert.doesNotMatch(readme, /private and unreleased|Experimental and unreleased|none has happened/);
  assert.match(readme, /Why use Infermeld/);
  assert.match(readme, /When not to use it/);
  assert.doesNotMatch(readme, /README-preview|Source checks.*snapshot/);
});

test('production landing has real navigation and retains failed attempts beside accepted evidence', () => {
  const html = read('site/index.html');
  assert.match(html, /Experimental v0\.1\.0/);
  assert.doesNotMatch(html, /Experimental and unreleased/);
  assert.match(html, /data-result="failed"/);
  assert.match(html, /Separate retry/);
  assert.match(html, /Neither model has a proven maximum usable context/);
  assert.match(html, /href="history\.html"/);
  assert.match(html, /href="https:\/\/github\.com\/5p00kyy\/infermeld"/);
  assert.match(html, /href="landing\.css"/);
  assert.doesNotMatch(html, /README-preview|README-source|history-record|private, local design preview|\b(?:evidence|build|third-party|license|contributing)\.html\b/);
  for (const record of ['capacity.json', 'cli-acceptance.json', 'results.json']) {
    assert.ok(html.includes(`href="${record}"`), `missing evidence link: ${record}`);
  }
});

test('shared historical record omits nonessential host identifiers', () => {
  const hardware = JSON.parse(read('site/results.json')).hardware;
  assert.deepEqual(Object.keys(hardware).sort(), ['amd', 'nvidia']);
  assert.doesNotMatch(read('site/history.html'), /Core (?:i\d|Ultra)|DDR\d|<dt>Host<\/dt>/);
});

test('Pages deployment is manual, fail-closed, and isolated from source CI', () => {
  const workflow = read('.github/workflows/pages.yml');
  assert.match(workflow, /workflow_dispatch:/);
  assert.match(workflow, /default: false/);
  assert.match(workflow, /inputs\.publish == true/);
  assert.match(workflow, /github\.event\.repository\.private == false/);
  assert.match(workflow, /github\.event\.repository\.visibility == 'public'/);
  assert.match(workflow, /github\.ref == 'refs\/heads\/main'/);
  assert.doesNotMatch(workflow, /^  (?:push|pull_request):/m);
  assert.match(workflow, /run: make test/);
  assert.match(workflow, /path: site/);
  assert.match(workflow, /pages: write/);
  assert.match(workflow, /id-token: write/);
  assert.match(workflow, /environment:[\s\S]*name: github-pages/);
  assert.match(workflow, /configure-pages@[a-f0-9]{40}/);
  assert.match(workflow, /upload-pages-artifact@[a-f0-9]{40}/);
  assert.match(workflow, /deploy-pages@[a-f0-9]{40}/);
});

test('the actual Pages gate rejects private, internal, unknown and non-main publication', () => {
  const workflow = read('.github/workflows/pages.yml');
  const expression = /^    if: \$\{\{ (.+) \}\}$/m.exec(workflow)?.[1];
  assert.ok(expression, 'missing build-job gate');
  // Interpret only this workflow's literal-equality conjunction, without eval.
  // This is a source contract and truth table, not live Actions acceptance.
  const clauses = expression.split(' && ').map(clause => {
    const match = /^([\w.]+) == (true|false|'[^']*')$/.exec(clause);
    assert.ok(match, `unsupported gate clause: ${clause}`);
    return [match[1], match[2] === 'true' ? true : match[2] === 'false' ? false : match[2].slice(1, -1)];
  });
  assert.equal(clauses.length, 4);
  const permits = context => clauses.every(([key, expected]) => context[key] === expected);
  const approved = {
    'inputs.publish': true,
    'github.event.repository.private': false,
    'github.event.repository.visibility': 'public',
    'github.ref': 'refs/heads/main',
  };
  assert.equal(permits(approved), true);
  for (const visibility of ['private', 'internal', 'unknown', undefined, null, '']) {
    assert.equal(permits({...approved, 'github.event.repository.visibility': visibility}), false, String(visibility));
  }
  for (const [key, value] of [
    ['inputs.publish', false], ['inputs.publish', undefined],
    ['github.event.repository.private', true], ['github.event.repository.private', undefined],
    ['github.ref', 'refs/heads/preview'], ['github.ref', 'refs/tags/v0.1.0'], ['github.ref', undefined],
  ]) {
    assert.equal(permits({...approved, [key]: value}), false, `${key}=${String(value)}`);
  }
});
