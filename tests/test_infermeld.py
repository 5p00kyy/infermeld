import pathlib
import contextlib
import io
import json
import subprocess
import sys
import socket
import tempfile
import unittest
from unittest.mock import patch

import infermeld


class CommandTests(unittest.TestCase):
    def model_args(self, model, extra=()):
        return ['serve', '--model', str(model), '--devices', 'Vulkan0,CUDA0',
                '--split', '3,2', '--confirm-devices', *extra]

    def test_cli_help_is_real(self):
        result = subprocess.run([sys.executable, infermeld.__file__, '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('serve', result.stdout)
        self.assertIn('devices', result.stdout)

    def test_rejects_unconfirmed_and_invalid_inputs(self):
        self.assertTrue(callable(getattr(infermeld, 'parse_args', None)))
        with tempfile.TemporaryDirectory() as directory:
            model = pathlib.Path(directory) / 'fixture.gguf'
            model.write_bytes(b'GGUF' + bytes(32))
            base = self.model_args(model)
            invalid = [base[:-1], base + ['--split', 'nan,2'], base + ['--split', '0,2'],
                       base + ['--devices', 'CUDA0,CUDA0'], base + ['--devices', 'CUDA0'],
                       base + ['--port', '0'], base + ['--host', '0.0.0.0'],
                       base + ['--ctx-size', '0'], base + ['--ubatch', '513'],
                       base + ['--trip-c', '100'], base + ['--mtp', '8'],
                       base + ['--model', str(model.parent / 'absent.gguf')]]
            with contextlib.redirect_stderr(io.StringIO()):
                for arguments in invalid:
                    with self.subTest(arguments=arguments), self.assertRaises(SystemExit):
                        infermeld.parse_args(arguments)

    def test_dry_run_returns_an_argument_array_without_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            model = pathlib.Path(directory) / 'fixture.gguf'
            model.write_bytes(b'GGUF' + bytes(32))
            result = subprocess.run([sys.executable, infermeld.__file__,
                                     *self.model_args(model, ['--server', sys.executable, '--dry-run'])],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.strip(), 'Dry run emitted no command')
            command = json.loads(result.stdout)
            self.assertIsInstance(command, list)
            self.assertEqual(command[command.index('--host') + 1], '127.0.0.1')

    def test_explicit_mtp_uses_current_upstream_flags(self):
        self.assertTrue(callable(getattr(infermeld, 'parse_args', None)))
        with tempfile.TemporaryDirectory() as directory:
            model = pathlib.Path(directory) / 'fixture.gguf'
            model.write_bytes(b'GGUF' + bytes(32))
            args = infermeld.parse_args(self.model_args(model, ['--mtp', '4']))
            command = infermeld.server_command(pathlib.Path('llama-server'), args)
            self.assertEqual(command[command.index('--spec-type') + 1], 'draft-mtp')
            self.assertEqual(command[command.index('--spec-draft-n-max') + 1], '4')
            self.assertNotIn('--draft-max', command)
            self.assertIn('--spec-draft-type-k', command)
            self.assertEqual(command[command.index('--spec-draft-type-k') + 1], 'q8_0')
            self.assertEqual(command[command.index('--spec-draft-type-v') + 1], 'q8_0')

    def test_default_launch_is_loopback_without_speculation(self):
        self.assertTrue(callable(getattr(infermeld, 'parse_args', None)), 'CLI argument parser is not implemented')
        self.assertTrue(callable(getattr(infermeld, 'server_command', None)), 'Safe server command is not implemented')
        with tempfile.TemporaryDirectory() as directory:
            model = pathlib.Path(directory) / 'fixture.gguf'
            model.write_bytes(b'GGUF' + bytes(32))
            args = infermeld.parse_args(['serve', '--model', str(model), '--devices', 'Vulkan0,CUDA0', '--split', '3,2', '--confirm-devices'])
            command = infermeld.server_command(pathlib.Path(directory) / 'llama-server', args)
            self.assertEqual(command[command.index('--host') + 1], '127.0.0.1')
            self.assertEqual(command[command.index('--spec-type') + 1], 'none')
            self.assertEqual(command[command.index('-sm') + 1], 'layer')
            self.assertEqual(command[command.index('-ctk') + 1], 'q8_0')
            self.assertEqual(command[command.index('-ctv') + 1], 'q8_0')
            self.assertNotIn('0.0.0.0', command)
            self.assertIn('--fit', command)
            self.assertEqual(command[command.index('--fit') + 1], 'off')
            self.assertIn('--jinja', command)
            self.assertIn('--no-webui', command)


class OwnershipTests(unittest.TestCase):
    def test_environment_overrides_are_removed_without_exposing_them(self):
        with patch.dict('infermeld.os.environ', {'LLAMA_ARG_HOST': '0.0.0.0',
                        'GGML_CUDA_ENABLE_UNIFIED_MEMORY': '1', 'LLAMA_MTP_ADAPTIVE': '1',
                        'LD_LIBRARY_PATH': '/example/runtime'}, clear=True):
            self.assertEqual(infermeld.clean_environment(), {'LD_LIBRARY_PATH': '/example/runtime'})

    def test_occupied_port_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory, socket.socket() as owner:
            model = pathlib.Path(directory) / 'fixture.gguf'
            model.write_bytes(b'GGUF' + bytes(32))
            owner.bind(('127.0.0.1', 0))
            owner.listen()
            arguments = ['serve', '--server', sys.executable, '--model', str(model),
                         '--devices', 'Vulkan0,CUDA0', '--split', '3,2', '--confirm-devices',
                         '--port', str(owner.getsockname()[1])]
            with patch('infermeld.subprocess.Popen') as launch:
                self.assertEqual(infermeld.main(arguments), 2)
                launch.assert_not_called()
            self.assertGreaterEqual(owner.fileno(), 0)

    def test_sensor_loss_after_launch_reaps_child(self):
        with tempfile.TemporaryDirectory() as directory:
            sensor = pathlib.Path(directory) / 'junction'
            pidfile = pathlib.Path(directory) / 'pid'
            sensor.write_text('40000')
            code = ('import os,pathlib,time;'
                    f'pathlib.Path({str(pidfile)!r}).write_text(str(os.getpid()));'
                    f'pathlib.Path({str(sensor)!r}).unlink();'
                    'time.sleep(30)')
            self.assertEqual(infermeld.run_owned([sys.executable, '-c', code], sensor, 85, interval=0.01), 74)
            import os
            with self.assertRaises(ProcessLookupError):
                os.kill(int(pidfile.read_text()), 0)

    def test_hot_sensor_prevents_any_launch(self):
        self.assertTrue(callable(getattr(infermeld, 'run_owned', None)))
        with tempfile.TemporaryDirectory() as directory:
            sensor = pathlib.Path(directory) / 'junction'
            sensor.write_text('90000')
            with patch('infermeld.subprocess.Popen') as launch:
                self.assertEqual(infermeld.run_owned([sys.executable, '-c', 'pass'], sensor, 85), 75)
                launch.assert_not_called()

    def test_watchdog_aborts_and_reaps_its_own_child(self):
        self.assertTrue(callable(getattr(infermeld, 'run_owned', None)))
        with tempfile.TemporaryDirectory() as directory:
            sensor = pathlib.Path(directory) / 'junction'
            pidfile = pathlib.Path(directory) / 'pid'
            sensor.write_text('40000')
            # Publish complete fixture values; truncation is not a sensor update.
            pending = sensor.with_suffix('.next')
            code = ('import os,pathlib,time;'
                    f'pathlib.Path({str(pidfile)!r}).write_text(str(os.getpid()));'
                    f'pathlib.Path({str(pending)!r}).write_text("90000");'
                    f'pathlib.Path({str(pending)!r}).replace({str(sensor)!r});'
                    'time.sleep(30)')
            self.assertEqual(infermeld.run_owned([sys.executable, '-c', code], sensor, 85, interval=0.01), 75)
            import os
            with self.assertRaises(ProcessLookupError):
                os.kill(int(pidfile.read_text()), 0)

    def test_sensor_failure_is_fail_closed(self):
        self.assertTrue(callable(getattr(infermeld, 'run_owned', None)))
        with tempfile.TemporaryDirectory() as directory:
            with patch('infermeld.subprocess.Popen') as launch:
                self.assertEqual(infermeld.run_owned([sys.executable, '-c', 'pass'],
                                                     pathlib.Path(directory) / 'absent', 85), 74)
                launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
