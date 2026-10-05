# What the evidence establishes

This is an experimental source-only companion kit, not a new inference engine or a universally qualified preset. The retained reference used llama.cpp revision `b92761a515ea31e852e7fbc1fad5f874b46f3718`, AMD RX 6900 XT 16 GB through Vulkan and NVIDIA RTX 3080 10 GB through CUDA. Backend identifiers must be mapped to physical cards before reuse.

## Evidence map

| Record | What it establishes | What it does not establish |
|---|---|---|
| [Q4 capacity record](../site/capacity.json) | Eight accepted context reservations and 32 short checks across two exact Q4 artifacts; per-card memory and the failed dense 128K split are retained | Filled 128K prompts, long-context recall, sustained Q4 throughput or an optimum context |
| [Fresh-build CLI acceptance](../site/cli-acceptance.json) | The unchanged Infermeld launcher served the MoE Q4 with the freshly built engine at an 8K reservation, both without MTP and with MTP4; each passed four short checks and owned SIGTERM teardown | Broad answer quality, sustained throughput, dense-model acceptance through this exact CLI or other hardware |
| [Historical IQ3-named measurements](../site/results.json) | Real short-prompt prefill, decode, end-to-end rates and speculative counters for four retained workload rows | Q4 speeds, fresh-build speeds, confidence intervals or a sustained-prefill comparison |
| Python and Node source tests | Argument, process-ownership, synthetic sensor, evidence, packaging and documentation contracts | GPU correctness or model quality |

The HTML views are [Q4 capacity](../site/index.html) and [labelled experiment history](../site/history.html). Exact artifact sources, immutable revisions and licenses are in [THIRD_PARTY.md](../THIRD_PARTY.md). The engine build recipe is [BUILD.md](../BUILD.md).

## Q4 capacity is not useful-context qualification

Both Q4 models passed short checks at reservations of 8,192, 32,768, 65,536 and 131,072 tokens. The dense model's 131,072-token attempt at split 3:2 failed during loading; the accepted retry used 2:1. The MoE reservations used 3:2. These allocation experiments used native MTP4, q8_0 target/draft caches and microbatch 32. They are not automatically the launcher's default recipe.

Neither model has a proven maximum usable context. 8K is the launcher's visible starting reservation, not a measured optimum. 128K is the largest reservation tested, not proof of full-length prompt ingestion or recall. Longer qualification did not complete under the retained test policy; aborted runs supply no performance numbers. Detailed local cooling diagnostics remain private and are not packaged as performance evidence.

## Fresh engine and CLI acceptance

The engine was rebuilt from the pinned source in a separate directory, with CUDA and Vulkan enabled and no embedded web UI assets. The isolated toolkit needed its real runtime libraries during final linking as well as execution. The final build and preflight passed.

The sanitized acceptance record is derived from a retained private receipt, not a newly run benchmark. It preserves the CLI digest, exact model provenance, executable/companion-library digests, 8K reservation, split 3:2, microbatch 32, MTP states, short-check outcomes, slot readback and exit 143 for both owned SIGTERM shutdowns. Existing GPU-control configuration was preserved. Private paths, generated responses and cooling telemetry were deliberately omitted.

The CLI SHA-256 in that record is checked against the current `infermeld.py` bytes by the source suite. These hardware results apply to that launcher and the recorded engine/model cohort; changing any of them requires fresh hardware acceptance. Local source/package verification does not rerun inference, and a binary digest is provenance evidence rather than a universal binary to install.

## Historical speeds stay historical

The IQ3-named records are separate exact artifacts, with one repetition per model/workload and 512 output tokens per row. Code prompts had 56 uncached tokens; prose prompts had 65. Those prompt-processing rates are not sustained prefill. Workloads stopped at the output cap, so the rows do not establish completed-task quality. Model families are not like-for-like hardware controls, and dynamic quantization filenames do not establish uniform tensor bit width. Host CPU/RAM metadata is omitted from the shared record, so it is not a fully specified cross-machine comparison.

Do not relabel these as Q4 speeds, transfer their results to the fresh engine cohort or infer a universal mixed-GPU speedup. Added capacity and faster execution are separate questions.

## Current boundary

Local tests and a clean source-bundle replay are preparation gates. They do not publish the repository or qualify sustained Q4 performance, full-length context, other GPU pairs, concurrent serving, Windows or macOS. Model weights, native binaries, toolkits and private raw receipts are not redistributed. Public repository creation, push, site deployment and release are separate actions.
