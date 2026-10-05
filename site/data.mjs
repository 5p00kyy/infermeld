export const METRICS = Object.freeze({
  decode_tps: 'Server-reported decode throughput. Excludes prefill; not an end-to-end speed measure.',
  end_to_end_tps: 'Output tokens divided by measured request wall time, including prefill and request overhead.',
  prefill_tps: 'Short-prompt processing: 56 or 65 uncached tokens at microbatch32. This is not sustained prefill throughput; inspect the token count and duration below.',
});

export function validateResults(data) {
  if (data?.schema_version !== 1 || data?.repetitions !== 1 || !/^[a-f0-9]{40}$/.test(data.source_pin) || !Array.isArray(data.rows) || data.rows.length !== 4) {
    throw new Error('The retained reference measurement record has an invalid schema.');
  }
  const seen = new Set();
  for (const row of data.rows) {
    const identity = `${row.family}:${row.workload}`;
    if (!['dense', 'moe'].includes(row.family) || !['code', 'prose'].includes(row.workload) || seen.has(identity)) {
      throw new Error('Measurement rows are missing, duplicated or unsupported.');
    }
    seen.add(identity);
    if (!Number.isInteger(row.prompt_tokens) || row.prompt_tokens <= 0 || !Number.isFinite(row.prompt_ms) || row.prompt_ms <= 0 || row.cached_prompt_tokens !== 0 || Math.abs(row.prompt_tokens * 1000 / row.prompt_ms - row.prefill_tps) > 1e-8) {
      throw new Error('Prompt-processing rates require consistent token counts, duration and cache status.');
    }
    for (const metric of Object.keys(METRICS)) {
      if (typeof row[metric] !== 'number' || !Number.isFinite(row[metric]) || row[metric] <= 0) {
        throw new Error('Throughput must be a positive finite measured number.');
      }
    }
    if (!Number.isInteger(row.drafted) || !Number.isInteger(row.accepted) || row.accepted < 0 || row.drafted <= 0 || row.accepted > row.drafted || row.output_tokens !== 512 || row.finish_reason !== 'length') {
      throw new Error('The draft counters or complete generation record are invalid.');
    }
  }
  return data;
}

export function selectRows(data, workload, metric) {
  validateResults(data);
  if (!['code', 'prose'].includes(workload) || !Object.hasOwn(METRICS, metric)) {
    throw new Error('Choose a supported workload and measured metric.');
  }
  const rows = ['dense', 'moe'].map(family => data.rows.find(row => row.family === family && row.workload === workload));
  const maximum = Math.max(...rows.map(row => row[metric]));
  return rows.map(row => ({...row, value: row[metric], width: row[metric] / maximum * 100, acceptance: row.accepted / row.drafted}));
}
