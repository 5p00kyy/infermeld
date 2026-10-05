import importlib.util
from pathlib import Path
import unittest


class PreflightTests(unittest.TestCase):
    def module(self):
        p = Path(__file__).resolve().parents[1] / 'preflight.py'
        self.assertTrue(p.exists(), 'engine preflight is missing')
        spec = importlib.util.spec_from_file_location('preflight', p)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_missing_engine_flags_fail_closed(self):
        module = self.module()
        self.assertIn('--spec-draft-type-k', module.missing_flags('--slots --fit --list-devices'))
        self.assertEqual(module.missing_flags('\n'.join(module.REQUIRED_FLAGS)), [])
        self.assertIn('--fit', module.missing_flags('\n'.join(module.REQUIRED_FLAGS).replace('--fit', '--fit-unrelated')))

    def test_device_ids_are_checked_without_assuming_a_vendor(self):
        module = self.module()
        output = 'Vulkan0: NVIDIA GPU (10000 MiB)\nCUDA0: NVIDIA GPU (10000 MiB)\n'
        found = module.select_devices(output, 'Vulkan0,CUDA0')
        self.assertEqual(len(found), 2)
        self.assertIn('NVIDIA', found['Vulkan0'])
        with self.assertRaises(ValueError):
            module.select_devices(output, 'Vulkan0,CUDA1')
        with self.assertRaises(ValueError):
            module.select_devices(output, 'CUDA0,CUDA0')

    def test_binary_digest_input_is_strict(self):
        module = self.module()
        self.assertTrue(module.valid_digest('a' * 64))
        self.assertFalse(module.valid_digest('a' * 63))
        self.assertFalse(module.valid_digest('A' * 64))
