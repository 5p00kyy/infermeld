#!/usr/bin/env python3
"""Read-only engine preflight. Lists devices, but starts no model or listener."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from infermeld import clean_environment

PIN = 'b92761a515ea31e852e7fbc1fad5f874b46f3718'
REQUIRED_FLAGS = ('--list-devices', '--slots', '--fit', '--no-webui', '--spec-type',
                  '--spec-draft-n-max', '--spec-draft-type-k', '--spec-draft-type-v',
                  '--spec-draft-p-min')


def valid_digest(value):
    return re.fullmatch(r'[a-f0-9]{64}', value) is not None


def missing_flags(text):
    return [flag for flag in REQUIRED_FLAGS
            if re.search(r'(?<![\w-])' + re.escape(flag) + r'(?![\w-])', text) is None]


def select_devices(text, requested):
    identifiers = requested.split(',')
    if len(identifiers) != 2 or len(set(identifiers)) != 2 or any(
            re.fullmatch(r'(?:CUDA|Vulkan)[0-9]+', name) is None for name in identifiers):
        raise ValueError('Choose two distinct explicit CUDA/Vulkan identifiers')
    found = dict(re.findall(r'^\s*((?:CUDA|Vulkan)[0-9]+):\s*(.+)$', text, re.MULTILINE))
    if any(name not in found for name in identifiers):
        raise ValueError('Selected identifiers are not both present in this binary inventory')
    return {name: found[name] for name in identifiers}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True, help='Trusted locally built llama-server')
    parser.add_argument('--devices', required=True)
    parser.add_argument('--source', type=Path, help='Optional pinned, clean engine checkout')
    parser.add_argument('--cuda-lib', type=Path, help='Explicit isolated toolkit runtime library directory')
    parser.add_argument('--expected-binary-sha256', help='Optional digest of a previously accepted binary')
    args = parser.parse_args(argv)
    if args.expected_binary_sha256 and not valid_digest(args.expected_binary_sha256):
        parser.error('Expected SHA-256 must be exactly 64 lowercase hexadecimal characters')
    report = {'passed': False, 'model_started': False, 'listener_started': False,
              'physical_identity_requires_operator_confirmation': True, 'error': None}
    try:
        binary = shutil.which(args.server)
        if binary is None:
            raise ValueError('Executable not found')
        env = clean_environment()
        if args.cuda_lib is not None:
            directory = args.cuda_lib.resolve(strict=True)
            if not directory.is_dir():
                raise ValueError('CUDA runtime library path is not a directory')
            env['LD_LIBRARY_PATH'] = str(directory) + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
        with Path(binary).open('rb') as stream:
            report['binary_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        if args.expected_binary_sha256 and report['binary_sha256'] != args.expected_binary_sha256:
            raise ValueError('Binary digest differs from the expected accepted artifact')
        if args.source:
            pin = subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True, timeout=15).strip()
            dirty = subprocess.check_output(['git', '-C', str(args.source), 'status', '--porcelain'], text=True, timeout=15).strip()
            if pin != PIN or dirty:
                raise ValueError('Source checkout is not clean at the tested pin')
            report['source_checkout_pin'] = pin
            report['source_checkout_proves_binary_origin'] = False
        linked = subprocess.run(['ldd', binary], capture_output=True, text=True, env=env, timeout=15)
        if linked.returncode or 'not found' in linked.stdout + linked.stderr:
            raise ValueError('Runtime dependency check failed; inspect ldd locally with the matching library path')
        report['runtime_libraries_resolved'] = True
        help_result = subprocess.run([binary, '--help'], capture_output=True, text=True, env=env, timeout=30)
        if help_result.returncode:
            raise ValueError('Engine help failed to execute')
        report['missing_required_flags'] = missing_flags(help_result.stdout + help_result.stderr)
        if report['missing_required_flags']:
            raise ValueError('Engine is missing flags required by this wrapper')
        devices = subprocess.run([binary, '--list-devices'], capture_output=True, text=True, env=env, timeout=30)
        if devices.returncode:
            raise ValueError('Engine device inventory failed')
        report['selected_devices'] = select_devices(devices.stdout + devices.stderr, args.devices)
        report['passed'] = True
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 2


if __name__ == '__main__':
    sys.exit(main())
