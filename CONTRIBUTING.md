# Contributing to Infermeld

Infermeld is a small Linux companion kit for a separately built llama.cpp. Keep changes focused on explicit device selection, reproducible builds, owned-process safety and evidence that other people can check. It is not a new inference engine or a promise that mixed GPUs are faster.

## Local checks

Use Python 3.11 or newer, Node.js 22 or newer, and Make:

```sh
make test
make package
```

There are no pip or npm dependencies. The Python tests use synthetic GGUF headers, temporary sensor files and ordinary CPU subprocesses; they are not GPU benchmarks. Node tests check the static site, provenance and repository contracts. GitHub Actions runs these checks on Linux with Python 3.11 and 3.13 and Node.js 22. A successful workflow qualifies only those source and bundle contracts on its exact commit, not a GPU configuration.

`make package` writes a source-only archive under `dist/`, with a per-file SHA-256 manifest. It excludes Git metadata, local weights, native binaries, private receipts and caches. The bundle does not build or run the engine. `make preview` serves the existing site on loopback port 8000 until Ctrl+C. Landing markup is checked against every displayed JSON evidence row, including the failed attempt and separate retry. Keep site links relative so project Pages paths work. See [the release checklist](docs/RELEASING.md) for bundle, browser and publication gates; its manual Pages workflow is not dispatched by source CI.

## Report hardware results, including failures

Use the hardware/result issue form. Partial reports are useful: write `unknown` for information you could not verify rather than inventing a value. Include:

- Physical GPU models and VRAM variants, backend identifiers and their physical mapping.
- OS, driver/runtime versions, llama.cpp revision and binary/library fingerprints when available.
- Exact model filename, publisher, immutable revision, file size and SHA-256 when known.
- Sanitized launch arguments, split mode/proportions, reserved context, cache precision, microbatch, thread count and speculation settings.
- The stage reached: preflight, load, first completion, representative workload or shutdown.
- For performance, actual processed prompt/output token counts, cache state, repetitions and timing definitions.

An allocated context is not a filled-context quality result. A successful short answer is not sustained throughput. Aborted runs must be marked incomplete and must not become performance rows. Retain failures and explain settings changed between attempts. See [the evidence guide](docs/EVIDENCE.md).

Do not post credentials, private paths, IP addresses, raw private conversation logs or local cooling diagnostics. Replace private paths in reproductions with generic paths. The wrapper's documented guard behaviour can be reported without uploading temperature/fan/power telemetry. If a report exposes credentials, stop sharing it and arrange a private reporting channel; do not paste the secret into an issue.

## Changes and acceptance

Add a failing regression for a demonstrated defect, then run the full source suite. Keep default serving loopback-only, MTP opt-in and cleanup limited to the invocation's own server. Do not weaken the read-only junction guard to make a test pass. New dependencies, automatic downloads, driver changes, persistent services, additional operating systems and new backends each require their own implementation and acceptance evidence.

CPU tests cannot qualify a GPU configuration. A hardware claim must identify the actual executable/library cohort, exact model and tested settings. Do not replace known-good private acceptance with an edited success flag, or attribute historical IQ3 speeds to Q4 models or a new engine build.

Keep licensing and attribution intact. Infermeld's original work is MIT; llama.cpp and model weights retain their own notices and terms. No public push, deployment or release is part of local contribution checks.
