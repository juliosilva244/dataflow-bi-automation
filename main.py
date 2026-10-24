"""Ponto de entrada oficial do DataFlow Fusion Ultimate 2.0."""

import os
import sys
from pathlib import Path

from app import main
from components import ai_assistant, ai_state
from services import llm_router
from services.logging_config import get_logger
from services.providers import groq_provider
from services.runtime_revision import runtime_diagnostics

if __name__ == "__main__":
    runtime = runtime_diagnostics()
    get_logger("dataflow.runtime").info(
        "runtime_integrity audit=%s loaded=%s disk=%s current=%s pid=%s source_at_import=%s source_current=%s watcher=%s run_on_save=%s",
        runtime["audit"], runtime["generation_loaded"], runtime["generation_disk"],
        runtime["current"], runtime["pid"], runtime["source_at_import"],
        runtime["source_current"], runtime["watcher"], runtime["run_on_save"],
    )
    get_logger("dataflow.runtime").info(
        "runtime revision=%s generation=%s model=%s pid=%s python=%s prefix=%s cwd=%s entry=%s app=%s ai_state=%s provider=%s router=%s ui=%s",
        ai_state.AI_STATE_REVISION, groq_provider.AI_GENERATION_REVISION,
        groq_provider.configured_groq_model(), os.getpid(), sys.executable, sys.prefix,
        Path.cwd(), Path(__file__).resolve(), main.__code__.co_filename, ai_state.__file__,
        groq_provider.__file__, llm_router.__file__, ai_assistant.__file__,
    )
    main()
