# Troubleshooting the first launch

Start from a trusted engine binary and a verified local GGUF. Do not change drivers, disable the guard or kill unrelated servers to make a recipe run. These checks diagnose the kit; they do not qualify new hardware.

## Executable or runtime libraries are missing

Use an explicit `--server` path, keep the engine's companion shared libraries with the binary, and run the [engine preflight](../BUILD.md#verify-the-engine-before-loading-weights). With an isolated CUDA toolkit, its real runtime libraries must be available at both link time and serve time. CUDA stub libraries are not a runtime substitute.

If preflight reports missing required flags, check that the binary supports the documented source pin. A source checkout at the correct revision does not prove that an independently supplied executable came from it. Record a fresh binary's digest rather than claiming the retained binary hash.

## Device IDs are wrong or refer to the same card

Run `infermeld.py devices` against the **same binary you will serve with**, then read the device descriptions. Vulkan can enumerate an NVIDIA card too. `Vulkan0,CUDA0` is an example, not automatic vendor detection or proof of two physical GPUs.

The two comma-separated split proportions follow the device order. They describe layer placement, not a literal pooled-VRAM ratio. Change a copied pair only after confirming the physical mapping. `--confirm-devices` acknowledges that inspection; it does not perform it.

## Dry-run succeeds but serving does not

`--dry-run` verifies arguments, finds the executable and checks the GGUF header, then prints a JSON argument array. It does **not** validate the model's full hash, query the GPUs, resolve runtime dependencies, find the sensor or prove that weights will fit. Do the preflight and independent hash verification before treating the command as ready to run.

The current quick start uses an 8K reservation and no MTP. The allocation experiments used explicit MTP4. If you enable `--mtp 4`, use an artifact with compatible embedded draft tensors and keep that change visible in any result report.

## No unique AMD junction sensor is available

Automatic discovery requires exactly one `amdgpu` sensor labelled `junction`. Multiple matches require you to identify the correct GPU and supply its existing readable sensor path with `--junction-sensor`. Paths can change across boots; never blindly reuse a sensor index or point the option at an invented/fake sensor.

The companion `_label` must say `junction`. Sensor loss or invalid input causes fail-closed shutdown. This kit does not write fan, clock, voltage or power settings. If your hardware does not expose a suitable sensor, it is outside the current guarded serving scope.

## The port is already occupied

The wrapper leaves the existing owner alone. Identify that service before deciding what to stop, or select another loopback port with `--port`. Do not use a broad process-kill command. The wrapper binds to `127.0.0.1`, not the LAN; remote access and authentication are not provided here.

## Model loading fails or the guard stops the run

Do not treat an aborted run as throughput evidence. Start with the documented short reservation, keep the actual split/cache/speculation settings attached to the report, and include failed conditions. A dry-run or allocated 128K reservation does not prove full-length prompt processing or useful context.

The read-only guard stops only this invocation's owned process group. Its sampled trip is **not a guaranteed hard temperature ceiling**. Fix the local operating conditions before another attempt; do not raise or bypass the guard. Do not upload private cooling telemetry or raw model conversations with the report.

If none of these explains the failure, use the hardware/result issue form described in [CONTRIBUTING.md](../CONTRIBUTING.md). Include the stage reached and sanitized arguments; write `unknown` where you could not verify a value. See [the evidence guide](EVIDENCE.md) for the difference between a short check and a qualified result.
