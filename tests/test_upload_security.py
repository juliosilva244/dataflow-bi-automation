from dataclasses import replace
from io import BytesIO

import pandas as pd
import pytest

from services.errors import UploadValidationError
from services.loader import carregar_dados
from services.settings import get_security_settings
from services.upload_security import read_validated_upload


class NamedBytesIO(BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


def test_rejeita_upload_acima_do_limite_configurado():
    settings = replace(get_security_settings(), max_upload_bytes=10)
    upload = NamedBytesIO(b"Data,Loja\n2024-01-01,A\n", "dados.csv")

    with pytest.raises(UploadValidationError, match="excede o limite"):
        read_validated_upload(upload, settings)


def test_rejeita_conteudo_xlsx_disfarcado_de_csv():
    upload = NamedBytesIO(b"PK\x03\x04conteudo", "dados.csv")

    with pytest.raises(UploadValidationError) as captured:
        read_validated_upload(upload)

    assert captured.value.code == "CSV_SIGNATURE_MISMATCH"


def test_rejeita_texto_disfarcado_de_xlsx():
    upload = NamedBytesIO(b"Data,Loja\n2024-01-01,A", "dados.xlsx")

    with pytest.raises(UploadValidationError) as captured:
        read_validated_upload(upload)

    assert captured.value.code == "XLSX_SIGNATURE_MISMATCH"


def test_rejeita_csv_com_colunas_inconsistentes():
    upload = NamedBytesIO(b"Data,Loja\n2024-01-01,A,EXTRA\n", "dados.csv")

    with pytest.raises(UploadValidationError) as captured:
        read_validated_upload(upload)

    assert captured.value.code == "CSV_INCONSISTENT_COLUMNS"


def test_rejeita_limites_de_linhas_e_colunas():
    settings = replace(get_security_settings(), max_rows=1, max_columns=2)
    too_many_rows = NamedBytesIO(b"Data,Loja\n1,A\n2,B\n", "dados.csv")
    too_many_columns = NamedBytesIO(b"A,B,C\n1,2,3\n", "dados.csv")

    with pytest.raises(UploadValidationError) as rows_error:
        read_validated_upload(too_many_rows, settings)
    with pytest.raises(UploadValidationError) as columns_error:
        read_validated_upload(too_many_columns, settings)

    assert rows_error.value.code == "UPLOAD_TOO_MANY_ROWS"
    assert columns_error.value.code == "UPLOAD_TOO_MANY_COLUMNS"


def test_aceita_xlsx_valido_dentro_dos_limites():
    output = BytesIO()
    source = pd.DataFrame({"Data": ["2024-01-01"], "Loja": ["Centro"]})
    source.to_excel(output, index=False)
    upload = NamedBytesIO(output.getvalue(), "dados.xlsx")

    result = read_validated_upload(upload)

    assert result.to_dict(orient="records") == [
        {"Data": "2024-01-01", "Loja": "Centro"}
    ]


def test_loader_exibe_erro_amigavel_sem_detalhes_internos():
    upload = NamedBytesIO(b"nao-e-uma-planilha", "segredo.xlsx")

    dataframe, origem, error = carregar_dados(upload)

    assert dataframe is None
    assert origem is None
    assert "XLSX_SIGNATURE_MISMATCH" in error
    assert "Traceback" not in error

