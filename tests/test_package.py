import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from tools import package


class PackageTests(unittest.TestCase):
    def source(self, directory):
        root = Path(directory)
        for name in package.ROOT_FILES:
            (root / name).write_text('Synthetic source fixture\n')
        (root / 'tests').mkdir()
        (root / 'tests' / 'fixture.py').write_text('# Synthetic test\n')
        return root

    def test_bundle_is_deterministic_and_excludes_private_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source(directory)
            for name in ['models/private.gguf', 'receipts/private.json', '.git/config',
                         '.env', 'tests/__pycache__/fixture.pyc']:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Private fixture, not release content\n')
            first = package.build(root, root / 'first.tar.gz')
            second = package.build(root, root / 'second.tar.gz')
            self.assertEqual(first['sha256'], second['sha256'])
            with tarfile.open(first['archive']) as archive:
                names = archive.getnames()
                self.assertEqual(len(names), first['source_files'] + 1)
                self.assertFalse(any('private' in name or '__pycache__' in name or '/.git/' in name
                                     or name.endswith('/.env') for name in names))
                source_manifest = archive.extractfile('infermeld/SOURCE-MANIFEST.json')
                assert source_manifest is not None
                recorded = json.load(source_manifest)
                for name, digest in recorded['files'].items():
                    member = archive.extractfile(f'infermeld/{name}')
                    assert member is not None
                    self.assertEqual(hashlib.sha256(member.read()).hexdigest(), digest)

    def test_source_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source(directory)
            (root / 'README.md').unlink()
            (root / 'README.md').symlink_to(root / 'BUILD.md')
            with self.assertRaises(ValueError):
                package.collect(root)

    def test_archive_destination_cannot_overwrite_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source(directory)
            output = root / 'README.md'
            original = output.read_bytes()
            with self.assertRaises(ValueError):
                package.build(root, output)
            self.assertEqual(output.read_bytes(), original)

    def test_manifest_rejects_tampered_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source(directory)
            path = root / 'SOURCE-MANIFEST.json'
            path.write_text(json.dumps(package.manifest(package.collect(root))))
            self.assertTrue(package.verify(root, path)['verified'])
            (root / 'README.md').write_text('Changed source\n')
            with self.assertRaises(ValueError):
                package.verify(root, path)


if __name__ == '__main__':
    unittest.main()
