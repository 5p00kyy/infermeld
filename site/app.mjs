import {METRICS, selectRows, validateResults} from './data.mjs';

const chart = document.querySelector('#chart');
const axis = document.querySelector('#chart-axis');
const status = document.querySelector('#chart-status');
const metric = document.querySelector('#metric');
const buttons = [...document.querySelectorAll('[data-workload]')];
let workload = 'code';
let measurements;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function render() {
  const rows = selectRows(measurements, workload, metric.value);
  chart.replaceChildren();
  const table = document.querySelector('#result-table');
  table.replaceChildren();
  for (const row of rows) {
    const color = row.family === 'dense' ? 'coral' : 'mint';
    const holder = element('div', 'chart-row');
    const model = element('div', 'chart-model');
    const detail = metric.value === 'prefill_tps'
      ? `${row.prompt_tokens} uncached prompt tokens · ${row.prompt_ms.toFixed(1)} ms`
      : `MTP4 · ${(row.acceptance * 100).toFixed(1)}% draft acceptance`;
    model.append(element('strong', '', measurements.models[row.family].label), element('span', '', detail));
    const track = element('div', 'bar-track');
    const bar = element('div', `bar ${color}`);
    bar.style.setProperty('--width', `${row.width}%`);
    track.append(bar);
    const value = element('div', 'chart-value', row.value.toFixed(1));
    value.append(element('span', '', 'TOKENS / SEC'));
    holder.append(model, track, value);
    chart.append(holder);
    const tr = element('tr');
    tr.append(element('td', '', measurements.models[row.family].label), element('td', '', row.decode_tps.toFixed(2)), element('td', '', row.end_to_end_tps.toFixed(2)), element('td', '', `${row.drafted} / ${row.accepted}`));
    table.append(tr);
  }
  axis.replaceChildren();
  const maximum = Math.max(...rows.map(row => row.value));
  for (let step = 0; step <= 4; step++) axis.append(element('span', '', (maximum * step / 4).toFixed(0)));
  document.querySelector('#chart-description').textContent = METRICS[metric.value];
  const description = `${workload} generation, ${metric.selectedOptions[0].textContent}. ${rows.map(row => `${measurements.models[row.family].label}: ${row.value.toFixed(2)} tokens per second`).join('; ')}. One repetition per condition, different model families, not a like-for-like comparison.`;
  chart.setAttribute('aria-label', description);
  chart.hidden = false;
  axis.hidden = false;
  status.hidden = true;
  for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.workload === workload));
}

for (const control of [...buttons, metric]) control.disabled = true;
for (const button of buttons) button.addEventListener('click', () => {
  workload = button.dataset.workload;
  render();
});
metric.addEventListener('change', render);

try {
  const response = await fetch(new URL('./results.json', import.meta.url));
  if (!response.ok) throw new Error(`Measurement request returned ${response.status}`);
  measurements = validateResults(await response.json());
  document.querySelector('#source-pin').textContent = measurements.source_pin;
  render();
  for (const control of [...buttons, metric]) control.disabled = false;
} catch (error) {
  status.hidden = false;
  chart.hidden = true;
  axis.hidden = true;
  status.textContent = 'The measurements could not be loaded or validated. No chart has been substituted. You can inspect the JSON record directly.';
  console.error('Infermeld measurement load failed:', error);
}
