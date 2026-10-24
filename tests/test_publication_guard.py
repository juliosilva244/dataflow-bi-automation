from scripts.check_publication import inspect_content


def test_index_guard_detects_credentials_without_returning_their_values():
    synthetic_token = b"gsk_" + b"A" * 32
    result = inspect_content("example.py", synthetic_token)
    assert "groq-token" in result
    assert all(synthetic_token.decode() not in finding for finding in result)


def test_index_guard_blocks_private_paths_and_binary_payloads():
    assert "unapproved-data" in inspect_content("data/raw/real.xlsx", b"\x00")
    assert "private-directory" in inspect_content(".venv/pyvenv.cfg", b"example")
    assert "secret-configuration" in inspect_content(".env", b"example")
    assert "local-recovery-material" in inspect_content("BACKUP/data.csv", b"example")


def test_index_guard_accepts_documented_demo_and_parses_python_without_execution():
    assert inspect_content("data/demo/vendas_demo.csv", b"Data,Loja\n") == []
    assert inspect_content(".env.example", b"GROQ_MODEL=openai/gpt-oss-20b\n") == []
    assert inspect_content("example.py", b"raise RuntimeError('not executed')\n") == []
    assert "python-syntax-error" in inspect_content("example.py", b"def broken(\n")
    assert "python-syntax-error" in inspect_content("example.py", b"return 1\n")
