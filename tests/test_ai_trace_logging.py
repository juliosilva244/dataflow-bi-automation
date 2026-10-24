import json
import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from services import ai_trace
from services.ai_trace import generation_trace, trace_stage
from services.logging_config import SafeRotatingFileHandler, get_logger


def test_loggers_share_one_handler_and_use_a_process_specific_file():
    first, second = get_logger("test.log.first"), get_logger("test.log.second")
    a = next(h for h in first.handlers if isinstance(h, SafeRotatingFileHandler))
    b = next(h for h in second.handlers if isinstance(h, SafeRotatingFileHandler))
    assert a is b
    assert Path(a.baseFilename).name == f"dataflow-{os.getpid()}.log"


@pytest.mark.skipif(sys.platform != "win32", reason="Reprodução específica do bloqueio de arquivos Windows")
def test_legacy_multiple_handles_reproduce_windows_rotation_failure(tmp_path):
    path = tmp_path / "legacy.log"
    first = RotatingFileHandler(path, maxBytes=32, backupCount=1)
    second = RotatingFileHandler(path, maxBytes=32, backupCount=1)
    failed = []
    second.handleError = lambda record: failed.append(sys.exc_info()[1])
    try:
        first.emit(logging.LogRecord("test", logging.INFO, "", 0, "x" * 24, (), None))
        second.emit(logging.LogRecord("test", logging.INFO, "", 0, "y" * 24, (), None))
        assert any(isinstance(error, PermissionError) and error.winerror == 32 for error in failed)
    finally:
        first.close()
        second.close()


def test_safe_handler_failure_never_prints_raw_record(tmp_path, capsys, monkeypatch):
    handler = SafeRotatingFileHandler(tmp_path / "safe.log", maxBytes=1, backupCount=1)
    monkeypatch.setattr(handler, "shouldRollover", lambda record: True)
    monkeypatch.setattr(handler, "doRollover", lambda: (_ for _ in ()).throw(PermissionError("private")))
    try:
        handler.emit(logging.LogRecord("test", logging.INFO, "", 0, "gsk_fake_private prompt-private", (), None))
        stderr = capsys.readouterr().err
        assert "falha ao gravar" in stderr
        assert "gsk_" not in stderr and "prompt-private" not in stderr and "Traceback" not in stderr
    finally:
        handler.close()


def test_concurrent_processes_rotate_their_own_logs_without_windows_lock_error():
    script = '''
import json
from services.logging_config import get_logger
logger = get_logger("test.process.rotation")
handler = logger.handlers[0]
handler.maxBytes = 200
for index in range(40):
    logger.info("event allowed rotation %s", index)
print(json.dumps(handler.baseFilename))
'''

    def run(_):
        return subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, range(2)))
    names = []
    for result in results:
        assert result.returncode == 0
        assert not result.stderr
        names.append(json.loads(result.stdout))
    assert names[0] != names[1]


def test_logging_rotation_survives_module_reloads_and_sequential_process_restarts(tmp_path):
    script = '''
import importlib, json, sys
from pathlib import Path
from services import logging_config as config
config.__file__ = str(Path(sys.argv[1]) / "services" / "logging_config.py")
first = config.get_logger("restart.first")
handler = first.handlers[0]
handler.maxBytes = 200
for cycle in range(4):
    importlib.reload(config)
    config.__file__ = str(Path(sys.argv[1]) / "services" / "logging_config.py")
    second = config.get_logger("restart.second")
    assert second.handlers[0] is handler
    for index in range(50):
        first.info("restart event %s", index)
        second.info("reload event %s", index)
assert Path(handler.baseFilename + ".1").exists()
print(json.dumps(handler.baseFilename))
'''
    for _ in range(3):
        result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        assert result.stderr == ""
        assert Path(json.loads(result.stdout)).exists()


def test_trace_is_allowlisted_correlated_and_isolated_between_threads(monkeypatch):
    events = []
    monkeypatch.setattr(ai_trace.logger, "info", lambda fmt, *args: events.append(fmt % args))

    class RemoteFailure(Exception):
        status_code = 404

    def run(_):
        with generation_trace("openai/gpt-oss-20b") as trace:
            trace_stage("http.send")
            trace_stage("provider.error", RemoteFailure("gsk_fake_private prompt-private"))
            return trace.correlation

    with ThreadPoolExecutor(max_workers=2) as pool:
        identifiers = list(pool.map(run, range(2)))
    assert len(set(identifiers)) == 2
    assert len(events) == 4
    assert all("gsk_fake_private" not in e and "prompt-private" not in e for e in events)
    for identifier in identifiers:
        same = [e for e in events if identifier in e]
        assert len(same) == 2
        assert any("exception=RemoteFailure http=404" in e for e in same)


def test_trace_failure_does_not_change_application_outcome(monkeypatch):
    monkeypatch.setattr(ai_trace.logger, "info", lambda *args: (_ for _ in ()).throw(PermissionError()))
    with generation_trace("gsk_fake_private"):
        trace_stage("ui.request")


def test_rate_limiter_migration_preserves_budget_and_current_exception_identity():
    from collections import deque
    from threading import Lock
    from types import SimpleNamespace

    from services.errors import AIRateLimitError
    from services.llm_router import ensure_current_rate_limiter

    now = [10.0]
    old = SimpleNamespace(limit=1, window_seconds=60, clock=lambda: now[0], _lock=Lock(), _requests=deque([9.0]))
    migrated = ensure_current_rate_limiter(old, 1)
    assert list(migrated._requests) == [9.0]
    with pytest.raises(AIRateLimitError):
        migrated.acquire()
    now[0] = 70.0
    migrated.acquire()
    assert ensure_current_rate_limiter(migrated, 1) is migrated


def test_existing_limiter_uses_current_error_after_module_reload():
    script = '''
import importlib, sys
from services.llm_router import SlidingWindowRateLimiter
limiter = SlidingWindowRateLimiter(1)
limiter.acquire()
sys.modules.pop("services.errors")
current = importlib.import_module("services.errors")
try:
    limiter.acquire()
except current.AIRateLimitError:
    print("current_exception")
else:
    raise AssertionError("Rate limit bypassed")
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "current_exception" in result.stdout
