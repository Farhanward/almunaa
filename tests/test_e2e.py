"""End-to-end + concurrency/performance tests (real OS process, real socket)."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from almunaa.service import Handler, create_server
from almunaa.version import __version__

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVICE_NAME = "almunaa"
PREFIX = "ALMUNAA"
SERVE_CMD = "serve"
CLI_MODULE = "almunaa.cli"


def _free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _get(url: str, timeout: float = 5.0):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _reset_handler_logger() -> None:
    logger = Handler.logger
    if logger is None:
        return
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    for flag in ("_svc_configured", "_almeezan_configured", "_aegis_configured"):
        if hasattr(logger, flag):
            setattr(logger, flag, False)
    Handler.logger = None


class CliSubprocessE2E(unittest.TestCase):
    def _env(self, extra: dict | None = None) -> dict:
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        if extra:
            env.update(extra)
        return env

    def test_cli_version_subprocess(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", CLI_MODULE, "version"],
            cwd=str(PROJECT_ROOT), env=self._env(),
            capture_output=True, text=True, timeout=90,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["service"], SERVICE_NAME)
        self.assertEqual(payload["version"], __version__)

    def test_serve_subprocess_lifecycle(self) -> None:
        port = _free_port()
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        env = self._env({f"{PREFIX}_LOG_DIR": str(Path(tmp.name) / "logs")})
        proc = subprocess.Popen(
            [sys.executable, "-m", CLI_MODULE, SERVE_CMD, "--port", str(port)],
            cwd=str(PROJECT_ROOT), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            deadline = time.time() + 25
            body = None
            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                try:
                    status, body = _get(base + "/api/health")
                    if status == 200:
                        break
                except (urllib.error.URLError, ConnectionError, OSError):
                    time.sleep(0.25)
                    body = None
            if body is None:
                out = proc.stdout.read() if proc.stdout else ""
                err = proc.stderr.read() if proc.stderr else ""
                self.fail(f"service did not start rc={proc.poll()} out={out} err={err}")
            self.assertEqual(body["service"], SERVICE_NAME)
            self.assertEqual(body["version"], __version__)
            _, ver = _get(base + "/api/version")
            self.assertEqual(ver["version"], __version__)
            _, metrics = _get(base + "/api/metrics")
            self.assertIn("latency_ms", metrics)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            for stream in (proc.stdout, proc.stderr):
                if stream is not None:
                    stream.close()
            tmp.cleanup()


class ConcurrencyPerf(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ[f"{PREFIX}_LOG_DIR"] = str(Path(self._tmp.name) / "logs")
        self.server = create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        os.environ.pop(f"{PREFIX}_LOG_DIR", None)
        _reset_handler_logger()
        self._tmp.cleanup()

    def test_health_under_concurrency(self) -> None:
        base = f"http://127.0.0.1:{self.port}"

        def one(_: int):
            start = time.perf_counter()
            status, _body = _get(base + "/api/health", timeout=10)
            return status, (time.perf_counter() - start) * 1000.0

        total = 120
        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(one, range(total)))
        statuses = [s for s, _ in results]
        latencies = sorted(d for _, d in results)
        self.assertEqual(statuses.count(200), total)
        p99 = latencies[min(len(latencies) - 1, round(0.99 * (len(latencies) - 1)))]
        self.assertLess(p99, 5000.0)


if __name__ == "__main__":
    unittest.main()
