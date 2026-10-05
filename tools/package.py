#!/usr/bin/env python3
"""Build or verify a source-only Infermeld bundle; never load an engine or model."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = ('.gitignore', 'BUILD.md', 'CONTRIBUTING.md', 'LICENSE', 'Makefile',
              'README.md', 'THIRD_PARTY.md', 'infermeld.py', 'preflight.py')
DIRECTORIES = {
    '.github': {'.yml', '.yaml'},
    'assets': {'.svg'},
    'docs': {'.md'},
    'LICENSES': {'.txt'},
    'site': {'.html', '.css', '.mjs', '.json', '.svg'},
    'tests': {'.py', '.mjs'},
    'tools': {'.py'},
}


def collect(root):
    paths = [root / name for name in ROOT_FILES]
    for name, extensions in DIRECTORIES.items():
        directory = root / name
        if directory.is_symlink():
            raise ValueError(f'Symlink source directory refused: {name}')
        paths.extend(path for path in directory.rglob('*')
                     if path.suffix in extensions and '__pycache__' not in path.parts)
    files = {}
    for path in sorted(paths):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Missing or non-regular source file: {path.relative_to(root)}')
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def manifest(files):
    return {'schema_version': 1, 'files': {
        name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}


def build(root, output):
    files = collect(root)
    files['SOURCE-MANIFEST.json'] = (json.dumps(manifest(files), indent=2) + '\n').encode()
    if output.is_symlink() or output.resolve() in {(root / name).resolve() for name in files}:
        raise ValueError('Archive destination must not replace a source file or symlink')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('wb') as stream, gzip.GzipFile(filename='', fileobj=stream, mode='wb', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for name, data in sorted(files.items()):
                info = tarfile.TarInfo(f'infermeld/{name}')
                info.size = len(data)
                info.mode = 0o644
                info.mtime = 0
                archive.addfile(info, io.BytesIO(data))
    return {'archive': str(output), 'source_files': len(files) - 1,
            'manifest_entries': len(files) - 1,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


def verify(root, path):
    recorded = json.loads(path.read_text())
    if recorded != manifest(collect(root)):
        raise ValueError('Source manifest does not match the selected source files')
    return {'verified': True, 'source_files': len(recorded['files'])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--output', type=Path, help='Archive destination (default: dist/infermeld-source.tar.gz)')
    mode.add_argument('--verify-manifest', type=Path, help='Verify an extracted source manifest')
    args = parser.parse_args(argv)
    try:
        report = (verify(ROOT, args.verify_manifest) if args.verify_manifest
                  else build(ROOT, args.output or ROOT / 'dist/infermeld-source.tar.gz'))
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}))
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
