# Third-party attribution and artifact provenance

Infermeld is an independent companion wrapper. Mixed-vendor execution is a llama.cpp capability, not an Infermeld invention. There is no claimed endorsement by the engine, model, quantization or GPU vendors.

## Engine

- Project: ggml-org/llama.cpp, by the ggml authors.
- Tested revision: `b92761a515ea31e852e7fbc1fad5f874b46f3718`.
- Upstream license: MIT, verified at the pinned source revision on 2026-10-04.
- License source: https://raw.githubusercontent.com/ggml-org/llama.cpp/b92761a515ea31e852e7fbc1fad5f874b46f3718/LICENSE
- Preserved upstream notice: [LICENSES/llama.cpp-MIT.txt](LICENSES/llama.cpp-MIT.txt).

This source-only candidate does not bundle the engine, its shared libraries, CUDA toolkit, drivers or model weights. Building dependencies locally does not license Infermeld's own code. Preserve the applicable upstream notices if a future distribution includes those components; that distribution requires a separate review.

## Q4 artifacts used in allocation and short-serving checks

Base-model creator: Qwen Team. GGUF quantization publisher: Unsloth. The following entries identify the exact tested files, rather than treating a model family name as artifact provenance.

| Artifact | Source repository | Immutable source revision | Bytes | SHA-256 |
|---|---|---|---:|---|
| `Qwen3.8-27B-UD-Q4_K_M.gguf` | `unsloth/Qwen3.8-27B-GGUF` | `4ca720788d1e01f1bff70c033e0d0028fd02e502` | 16464440224 | `322e194ff79741c7baa497c240f677f54b201b0efab44ca8e50f122b39123482` |
| `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` | `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` | `5bc3e238d916f48a861bac2f8a1990a0e9b7e98d` | 22663387424 | `0b21525e972670ed59e1812e170b27c26355381f0656ecc4e25617ece7dac58b` |

On 2026-10-04 the Hugging Face API at each immutable revision returned those exact filenames, byte sizes and LFS SHA-256 values, matching the retained local checks. Each quantization repository's `cardData.license` and license tag declare `apache-2.0`. This is a checked publisher declaration for those repositories, not a legal guarantee inferred from a base-model card. The API inventory returned no separate LICENSE or NOTICE file in either quantization repository.

Sources:

- https://huggingface.co/api/models/unsloth/Qwen3.8-27B-GGUF/revision/4ca720788d1e01f1bff70c033e0d0028fd02e502?blobs=true
- https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/revision/5bc3e238d916f48a861bac2f8a1990a0e9b7e98d?blobs=true

The records in `site/capacity.json` carry the same provenance. No weights are redistributed. Users must independently review the applicable terms before obtaining or using them.

## IQ3-named historical artifacts

The optional experiment history names `Qwen3.8-27B-UD-IQ3_XXS.gguf` and `Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf`. Retained launchers identify their source repositories as `unsloth/Qwen3.8-27B-GGUF` and `unsloth/Qwen3.6-35B-A3B-MTP-GGUF`, respectively. Qwen Team and Unsloth are credited for the base models and quantization publications.

Both local files were independently streamed through SHA-256 on 2026-10-04 and matched exact byte sizes and LFS hashes at these publication revisions. The pinned publisher metadata declares `apache-2.0` for each. These are content-verified publication revisions, not a claim that the original download revision was recorded.

| Artifact | Verified publication revision | Bytes | SHA-256 |
|---|---|---:|---|
| `Qwen3.8-27B-UD-IQ3_XXS.gguf` | `f975863083b62f54a5e6fac11671c750c2bbc59c` | 11913559104 | `0a6129dcbbbe72f423dc67e0e3bbfbbdf3e923981a3637687ebb96a46c59d6be` |
| `Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf` | `5bc3e238d916f48a861bac2f8a1990a0e9b7e98d` | 14069266720 | `36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012e3d9e2495a90e7a7150` |

The dense IQ3-named file at the newer Q4 publication revision has a different size and hash. Reproducing the history requires the older matching revision above, not a current branch or a Q4 pin. A filename does not establish uniform tensor bit width. No historical speed is attributed to the Q4 artifacts or the freshly rebuilt engine.

Source metadata for the dense historical artifact: https://huggingface.co/api/models/unsloth/Qwen3.8-27B-GGUF/revision/f975863083b62f54a5e6fac11671c750c2bbc59c?blobs=true

## Infermeld's own license

The owner selected MIT on 2026-10-04. [LICENSE](LICENSE) applies to Infermeld's original wrapper, tests, documentation and site assets. The copyright attribution uses the public developer identity, 5p00kyy, and Infermeld contributors.

This does not replace third-party copyright notices or license terms, claim authorship of llama.cpp, or license model weights. If a future candidate includes upstream source or binaries, preserve the ggml authors' copyright and MIT permission notice with that distribution, as well as other applicable dependency notices. Keeping our original contributions MIT matches the engine's license without confusing the two copyright holders.

Infermeld is a source-only experimental companion kit, not a distribution of a llama.cpp source fork. No engine binaries or model weights are included.
