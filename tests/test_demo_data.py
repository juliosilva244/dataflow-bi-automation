import csv
import hashlib
import io
from pathlib import Path

from domain.schema import REQUIRED_FIELDS
from scripts.generate_demo_data import FIELDNAMES, ROW_COUNT, build_rows, write_demo_csv
from scripts.list_publishable_files import is_ignored, load_patterns
from services.loader import limpar_dados
from services.upload_security import read_validated_content


def test_demo_generator_is_deterministic():
    first = build_rows()
    second = build_rows()
    assert first == second
    assert len(first) == ROW_COUNT
    assert all(row["Loja"].startswith("Loja ") for row in first)
    assert all(str(row["Pedido"]).startswith("DEMO-") for row in first)


def test_demo_csv_is_compatible_with_secure_pipeline(tmp_path):
    output = write_demo_csv(tmp_path / "demo.csv")
    content = output.read_bytes()
    raw = read_validated_content(content, output.name)
    normalized, error = limpar_dados(raw)

    assert error is None
    assert normalized is not None
    assert len(normalized) == ROW_COUNT
    assert set(REQUIRED_FIELDS).issubset(normalized.columns)
    assert normalized["Faturamento"].gt(0).all()


def test_demo_csv_has_documented_schema_and_stable_content(tmp_path):
    output = write_demo_csv(tmp_path / "demo.csv")
    text = output.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    assert tuple(reader.fieldnames or ()) == FIELDNAMES
    assert hashlib.sha256(output.read_bytes()).hexdigest() == (
        "2dec98b58c7ddf38bd127e3cc0e6cdeddeb9522bd5c2d00ea08bb73ce5aa3286"
    )


def test_public_display_name_has_no_personal_fallback(monkeypatch):
    monkeypatch.delenv("DATAFLOW_DISPLAY_NAME", raising=False)
    from components.executive_dashboard import display_name

    assert display_name() == "Visitante"


def test_gitignore_excludes_private_content_and_keeps_public_demo():
    patterns = load_patterns(Path(__file__).resolve().parents[1])
    assert is_ignored("data/raw/vendas.xlsx", patterns)
    assert is_ignored("outputs/dataflow.log", patterns)
    assert is_ignored(".venv/pyvenv.cfg", patterns)
    assert is_ignored("artifacts/dashboard.png", patterns)
    assert is_ignored("src/utils/generate_data.py", patterns)
    assert is_ignored(".env", patterns)
    assert not is_ignored(".env.example", patterns)
    assert not is_ignored("data/demo/vendas_demo.csv", patterns)
    assert not is_ignored("tests/test_demo_data.py", patterns)


def test_gitignore_excludes_candidate_virtual_environment():
    patterns = load_patterns(Path.cwd())

    assert is_ignored(".venv-candidate-cve/Lib/site-packages/example.py", patterns)
