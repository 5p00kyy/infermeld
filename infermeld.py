#!/usr/bin/env python3
"""Infermeld private candidate: explicit, loopback-only llama.cpp serving."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    devices = commands.add_parser('devices', help='List the selected llama.cpp build devices')
    devices.add_argument('--server', default='llama-server')
    serve = commands.add_parser('serve', help='Serve a local GGUF under a read-only junction guard')
    serve.add_argument('--server', default='llama-server')
    serve.add_argument('--model', type=Path, required=True)
    serve.add_argument('--devices', required=True, help='Two explicit comma-separated device identifiers')
    serve.add_argument('--split', required=True, help='Two positive comma-separated layer proportions')
    serve.add_argument('--confirm-devices', action='store_true', help='Acknowledge checking physical GPU identities')
    serve.add_argument('--ctx-size', type=int, default=8192)
    serve.add_argument('--ubatch', type=int, default=32)
    serve.add_argument('--threads', type=int, default=8)
    serve.add_argument('--port', type=int, default=8080)
    serve.add_argument('--mtp', type=int, choices=range(5), default=0)
    serve.add_argument('--trip-c', type=int, default=85, help='Sampled junction trip, not a hard ceiling (max85C)')
    serve.add_argument('--junction-sensor', type=Path, help='Read-only labeled junction sensor; otherwise discover one AMD GPU')
    serve.add_argument('--dry-run', action='store_true', help='Emit a JSON argument array without starting a server')
    args = parser.parse_args(argv)
    if args.action == 'serve':
        if not args.confirm_devices:
            parser.error('Run devices, check the physical GPU identities, then use --confirm-devices')
        selected = args.devices.split(',')
        if len(selected) != 2 or len(set(selected)) != 2 or any(
                re.fullmatch(r'(?:CUDA|Vulkan)[0-9]+', name) is None for name in selected):
            parser.error('Choose two distinct CUDA/Vulkan device identifiers')
        try:
            weights = [float(value) for value in args.split.split(',')]
        except ValueError:
            parser.error('Split proportions must be numeric')
        if len(weights) != 2 or not all(math.isfinite(value) and value > 0 for value in weights):
            parser.error('Split needs two finite positive proportions')
        if not (512 <= args.ctx_size <= 131072 and 1 <= args.ubatch <= 512
                and 1 <= args.threads <= 256 and 1 <= args.port <= 65535 and 1 <= args.trip_c <= 85):
            parser.error('Context, microbatch, threads, port or trip threshold is outside the supported range')
        try:
            with args.model.open('rb') as model:
                if model.read(4) != b'GGUF':
                    parser.error('Model does not have a GGUF header')
        except OSError as error:
            parser.error(f'Model cannot be read: {error}')
    return args


def server_command(binary, args):
    command = [str(binary), '-m', str(args.model), '-ngl', '99',
               '-dev', args.devices, '-ts', args.split, '-sm', 'layer', '-fa', 'on',
               '-ctk', 'q8_0', '-ctv', 'q8_0', '-c', str(args.ctx_size),
               '-b', '512', '-ub', str(args.ubatch), '-t', str(args.threads),
               '--host', '127.0.0.1', '--port', str(args.port), '-np', '1', '--slots',
               '--fit', 'off', '--jinja', '--no-webui',
               '--spec-type', 'draft-mtp' if args.mtp else 'none']
    if args.mtp:
        command.extend(['--spec-draft-n-max', str(args.mtp), '--spec-draft-type-k', 'q8_0',
                        '--spec-draft-type-v', 'q8_0', '--spec-draft-p-min', '0.0'])
    return command


class StopRequested(Exception):
    def __init__(self, signum):
        self.signum = signum


def stop_owned(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)


def clean_environment():
    return {key: value for key, value in os.environ.items()
            if not key.startswith(('LLAMA_ARG_', 'GGML_', 'LLAMA_MTP_'))}


def run_owned(command, sensor, limit_c, interval=0.1):
    """Read-only sampled guard; terminate/reap only this launch's process group."""
    process = None
    handlers = {}
    def interrupted(signum, frame):
        raise StopRequested(signum)
    try:
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            handlers[signum] = signal.signal(signum, interrupted)
        temperature = int(Path(sensor).read_text())
        if temperature >= limit_c * 1000:
            print('Thermal precondition failed; nothing launched.', file=sys.stderr)
            return 75
        process = subprocess.Popen(command, start_new_session=True, env=clean_environment())
        print(json.dumps({'event': 'owned_launch', 'pid': process.pid,
                          'junction_trip_c': limit_c, 'guard_is_hard_ceiling': False}), file=sys.stderr)
        while process.poll() is None:
            temperature = int(Path(sensor).read_text())
            if temperature >= limit_c * 1000:
                print(json.dumps({'event': 'thermal_abort', 'observed_junction_c': temperature / 1000,
                                  'trip_c': limit_c}), file=sys.stderr)
                return 75
            time.sleep(interval)
        return process.returncode if process.returncode >= 0 else 128 - process.returncode
    except StopRequested as error:
        return 128 + error.signum
    except (OSError, ValueError) as error:
        print(f'Guard or launch failed: {error}', file=sys.stderr)
        return 74
    finally:
        try:
            if process is not None:
                stop_owned(process)
        finally:
            for signum, handler in handlers.items():
                signal.signal(signum, handler)


def discover_sensor():
    sensors = []
    for hwmon in Path('/sys/class/drm').glob('card[0-9]*/device/hwmon/hwmon*'):
        if (hwmon / 'name').read_text().strip() == 'amdgpu':
            for label in hwmon.glob('temp*_label'):
                if label.read_text().strip() == 'junction':
                    sensors.append(label.with_name(label.name.replace('_label', '_input')))
    if len(sensors) != 1:
        raise ValueError('Expected exactly one AMD junction sensor; specify --junction-sensor explicitly')
    return sensors[0]


def main(argv=None):
    args = parse_args(argv)
    binary = shutil.which(args.server)
    if binary is None:
        print('llama-server executable not found; specify --server.', file=sys.stderr)
        return 2
    if args.action == 'devices':
        return subprocess.run([binary, '--list-devices'], env=clean_environment(), timeout=30).returncode
    command = server_command(binary, args)
    if args.dry_run:
        print(json.dumps(command))
        return 0
    with socket.socket() as probe:
        probe.settimeout(0.5)
        if probe.connect_ex(('127.0.0.1', args.port)) == 0:
            print('Loopback port already has an owner; leave it untouched.', file=sys.stderr)
            return 2
    try:
        sensor = args.junction_sensor or discover_sensor()
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 74
    return run_owned(command, sensor, args.trip_c)


if __name__ == '__main__':
    raise SystemExit(main())
