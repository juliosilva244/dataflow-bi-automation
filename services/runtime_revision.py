"""Allowlisted local revision checks, not session/credential introspection."""
from __future__ import annotations

import ast
import hashlib
import os
import sys
from pathlib import Path

from services.errors import DataFlowError

AUDIT_REVISION = "IA-auditoria-20261023.3"
ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    "main.py", "app.py", "services/runtime_revision.py", "services/ai_evidence.py",
    "services/ai_grounding.py", "services/llm_router.py", "services/metrics_engine.py",
    "services/providers/groq_provider.py", "components/ai_assistant.py",
    "components/ai_state.py", "components/analytical_scope.py",
    "domain/normalization.py", "services/loader.py", "services/ai_presentation.py",
    "components/chat_message.py", "assets/styles.py",
    "services/anomalies.py", "services/sensitivity.py", "services/formatter.py",
    "components/sensitivity_panel.py",
)


def source_signature():
    digest = hashlib.sha256()
    for name in SOURCE_FILES:
        digest.update(name.encode("utf-8"))
        digest.update((ROOT / name).read_bytes())
    return digest.hexdigest()


def disk_generation_revision():
    path = ROOT / "services/providers/groq_provider.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "AI_GENERATION_REVISION" for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("Marcador de revisão ausente")


_SOURCE_AT_IMPORT = source_signature()


def runtime_diagnostics():
    from streamlit import config

    from services.providers import groq_provider

    current = source_signature()
    disk = disk_generation_revision()
    loaded = groq_provider.AI_GENERATION_REVISION
    return {
        "audit": AUDIT_REVISION, "pid": os.getpid(), "generation_loaded": loaded,
        "generation_disk": disk, "source_at_import": _SOURCE_AT_IMPORT,
        "source_current": current, "current": loaded == disk and current == _SOURCE_AT_IMPORT,
        "provider_path": str(Path(groq_provider.__file__).resolve()),
        "python": sys.executable, "prefix": sys.prefix, "cwd": str(Path.cwd()),
        "watcher": config.get_option("server.fileWatcherType"),
        "run_on_save": config.get_option("server.runOnSave"),
    }


def ensure_ai_runtime_current():
    try:
        current = runtime_diagnostics()["current"]
    except (OSError, SyntaxError, ValueError):
        current = False
    if not current:
        raise DataFlowError(
            "O código da IA em memória difere dos arquivos atuais. Não foi feita chamada externa. "
            "Solicite a atualização controlada do servidor; recarregar apenas o navegador pode não bastar.",
            code="AI_RUNTIME_STALE",
        )
