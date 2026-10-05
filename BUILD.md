# Building the pinned CUDA + Vulkan engine

Infermeld is a Python wrapper, not an engine installer. This Linux recipe targets the engine revision used in the retained experiment:

```text
b92761a515ea31e852e7fbc1fad5f874b46f3718
```

Build inside a new directory. Do not overwrite your usual llama.cpp installation, change GPU drivers, or run compilation alongside a performance test. The private test rig uses an exclusive job lease for both compilation and inference.

## Dependencies and scope

You need Git, CMake, Ninja, a CUDA-compatible GCC/G++ toolchain, the CUDA toolkit, a working Vulkan loader and ICD for the AMD GPU, Vulkan development headers, `glslc`, and SPIR-V headers. `ldd` is used by the engine preflight. Driver/device access must already work; this guide does not install or upgrade drivers.

The reference build cache reports CMake 4.4.3, Ninja 1.13.2, GCC 16.2.1 and CUDA compiler release 13.4 (V13.4.92). These describe the tested environment, not universal minimum versions or a recommendation to upgrade an existing system. Toolkit/compiler compatibility matters. Other combinations are not yet qualified by Infermeld.

The reference NVIDIA target is **SM86**, matching the RTX 3080. Change the architecture only for your actual hardware and validate the resulting binary; SM86 is not an all-NVIDIA compatibility setting. Vulkan provides the AMD backend without a ROCm dependency in this recipe.

## Source and configure

From a fresh working directory:

```sh
git clone --filter=blob:none --no-checkout https://github.com/ggml-org/llama.cpp.git engine
git -C engine checkout --detach b92761a515ea31e852e7fbc1fad5f874b46f3718
test "$(git -C engine rev-parse HEAD)" = b92761a515ea31e852e7fbc1fad5f874b46f3718
test -z "$(git -C engine status --porcelain)"
```

Set these to existing toolkit/header installations. The example assumes paths without spaces. An isolated CUDA toolkit is fine; do not use its stub-library directory as your runtime library path.

```sh
export CUDA_ROOT=/absolute/path/to/cuda
export SPIRV_PREFIX=/absolute/path/to/spirv-headers-install
export LD_LIBRARY_PATH="$CUDA_ROOT/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

cmake -S engine -B build-cuda-vulkan -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$(command -v gcc)" \
  -DCMAKE_CXX_COMPILER="$(command -v g++)" \
  -DCMAKE_CUDA_HOST_COMPILER="$(command -v g++)" \
  -DCMAKE_CUDA_COMPILER="$CUDA_ROOT/bin/nvcc" \
  -DCUDAToolkit_ROOT="$CUDA_ROOT" \
  -DCMAKE_CUDA_ARCHITECTURES=86 \
  -DCMAKE_PREFIX_PATH="$SPIRV_PREFIX" \
  -DSPIRV-Headers_DIR="$SPIRV_PREFIX/share/cmake/SPIRV-Headers" \
  -DCMAKE_CXX_FLAGS="-I$SPIRV_PREFIX/include" \
  -DGGML_CUDA=ON -DGGML_VULKAN=ON -DGGML_NATIVE=OFF \
  -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF

cmake --build build-cuda-vulkan --target llama-server llama-bench --parallel 4
```

The explicit SPIR-V include/package paths reproduce the reference build's local header installation. If your distribution provides these in standard system locations, adapt those paths rather than copying another person's filesystem layout. An isolated CUDA runtime must also be available during final executable linking, not just when serving. Both UI switches are off so compilation does not download a mutable prebuilt web UI. A configure success is not a compiled-engine or GPU-serving success.

## Verify the engine before loading weights

Run the wrapper's read-only preflight against a trusted binary. It checks the dynamic loader, flags needed by Infermeld, source checkout pin when supplied, binary SHA-256 and the selected device inventory. It starts no model or listener, but device enumeration can initialize driver contexts.

From your Infermeld source directory:

```sh
python3 preflight.py \
  --server /absolute/path/to/build-cuda-vulkan/bin/llama-server \
  --source /absolute/path/to/engine \
  --cuda-lib "$CUDA_ROOT/lib64" \
  --devices Vulkan0,CUDA0
```

A passing inventory does **not** prove that two backend names are two distinct physical GPUs. Vulkan can expose the NVIDIA card too. Read the descriptions and confirm physical identities yourself before `--confirm-devices`. The preflight explicitly does not infer vendor from an index.

For an already accepted binary you can additionally require its exact digest with `--expected-binary-sha256`. A fresh local compilation may have a different digest; record it, do not substitute an old digest to make the check pass. A clean pinned source checkout alone does not prove the provenance of an independently supplied binary.

If runtime dependencies do not resolve, inspect them locally with the same library path:

```sh
LD_LIBRARY_PATH="$CUDA_ROOT/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  ldd /absolute/path/to/build-cuda-vulkan/bin/llama-server
```

Keep the engine's companion shared libraries with its binary. Do not copy only `llama-server` and assume that the resulting deployment is complete.

## Weights and serving

Weights are not included. Independently verify the chosen artifact hash and its applicable license. The Q4 allocation record in `site/capacity.json` identifies the two tested artifact filenames and hashes; it does not establish a maximum usable context or the model's full answer quality.

Use the README's explicit device/split dry-run first. For an isolated toolkit, make its real runtime libraries available to the serving invocation as well:

```sh
export LD_LIBRARY_PATH="$CUDA_ROOT/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python3 infermeld.py devices --server /absolute/path/to/build-cuda-vulkan/bin/llama-server
```

Do not automatically promote a context or speculative depth from an allocation test. The complete-prompt qualification is held on the reference machine; private cooling diagnostics are not performance measurements.

## Acceptance boundaries

Existing reference binary: dynamic-library/flag/device preflight passed, and short live Q4 serving was exercised. A fresh pinned source build of llama-server and llama-bench also completed and passed loader/flag/device preflight on 2026-10-04, after fixing the isolated-toolkit link path and disabling prebuilt UI provisioning. Isolated-source MoE Q4 quick-start and owned teardown then passed with the fresh engine: default non-MTP and MTP4 each passed four short checks at an 8K reservation. The [sanitized acceptance record](site/cli-acceptance.json) preserves executable and companion-library hashes, exact model/CLI provenance and shutdown outcomes without private paths or cooling telemetry. Source tests and short serving do not establish sustained throughput or full-length context quality. No public release is authorized by this document.
