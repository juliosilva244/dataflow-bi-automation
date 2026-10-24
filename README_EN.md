# DataFlow Fusion Ultimate 2.0

A local Business Intelligence application built with Python and Streamlit for secure
ingestion, normalization, analysis, and export of commercial data. It provides eight
areas: Overview, Sales Analysis, Products, Stores, Artificial Intelligence, Data Quality,
Reports, and Settings.

> Stable release: **IA-geracao-20261023.6**, audit **IA-auditoria-20261023.3**.
> This public distribution includes code, controlled-data tests, and synthetic demo data,
> not operational data or internal reports. Publication awaits owner confirmation.
> Live Groq acceptance for this revision and production deployment remain pending.
> See the [release notes](docs/RELEASE_IA6_AUDIT3.md).

## Purpose and confirmed features

DataFlow turns heterogeneous CSV/XLSX files into a consistent analytical view without
hiding data loss or monetary anomalies. It provides a centralized schema and
normalization, exact `Decimal` monetary totals, equivalent-period comparisons, shared
filters, KPIs, Plotly charts, paginated tables, visible quality findings, and CSV/Excel/PDF
reports. Uploads are content-validated and exports neutralize spreadsheet formulas.

The optional Groq assistant requires explicit activation and consent, supports
anonymization and usage limits, and never receives the complete DataFrame. The dashboard
works without an AI key.

## Stack and structure

Validated with Python 3.11.9, Streamlit, Pandas, Plotly, OpenPyXL, and ReportLab.

```text
app.py / main.py       composition and official entry point
components/            Streamlit presentation components
domain/                schema, normalization, models, and periods
services/              loading, metrics, security, AI, and reports
services/providers/    external-provider adapters
data/demo/             public deterministic synthetic data
scripts/               reproducible utilities
tests/                 local unit and integration tests
docs/                  architecture, security, publication guidance
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Install and run

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m streamlit run main.py --server.port 8510
```

Open `http://localhost:8510`. For development, install `requirements-dev.txt` and run:

```powershell
python -m pytest
python -m ruff check .
python -m compileall -q app.py main.py assets components domain services scripts tests
python -m pip check
```

Direct dependencies are pinned to locally validated versions.
`requirements-lock-py311-windows.txt` reproduces the approved Windows/Python 3.11
candidate, including test tools; install it with
`python -m pip install -r requirements-lock-py311-windows.txt` instead of the two
requirements files when reproducing that environment. Local rollback snapshots are not
distributed. Distribution hashes are still recommended before production.

Each user enters a personal Groq key in the masked field on the Artificial Intelligence
page. It is held only in that Streamlit session, can be replaced or removed, and must not
be stored in `.env`. The rest of the dashboard works without a key.

## Data and safe demonstration

Required fields are `Data`, `Loja`, `Produto`, `Quantidade`, and `Faturamento`; order,
category, profit, and unit price are optional. Upload
[`data/demo/vendas_demo.csv`](data/demo/vendas_demo.csv) for a safe demo. Its 720 rows are
fictional and reproducible with `python -m scripts.generate_demo_data`.

The operational `data/raw/vendas.xlsx` file is excluded from publication by default and
must not be replaced by demo data.
On a fresh clone, the missing-default-file message is expected: open **Dados** in the
top toolbar and upload the demo CSV. Do not commit a real dataset.

Public tests use controlled fixtures and demo data. Local regressions tied to operational
data, totals, or UI state remain local. The previously recorded 357 passing tests are
historical evidence, not the public suite count. AppTest is not browser visual acceptance.

## Security, screenshots, and license

The application enforces upload limits, sanitizes logs, escapes dynamic HTML, and protects
spreadsheets. See [docs/SECURITY.md](docs/SECURITY.md). Existing screenshots require human
review; follow [`docs/screenshots/README.md`](docs/screenshots/README.md) and never present
a mockup as a real screen.

No cloud deployment was verified here. The previous remote README advertises a Streamlit
Cloud app; its status and automatic updates must be checked before pushing. Visual
approval was declared by the owner, not established
by a new independent browser inspection here; no final public screenshots were supplied.
Live Groq acceptance specifically for revision `.6` remains pending. The October 23
dependency audit found no known vulnerabilities at that time; this is not a fresh scan.
The remote repository's existing [MIT license](LICENSE) and copyright notice are preserved.
Removing operational data or screenshots from the current tree does not remove copies
in older Git commits; those require a separate privacy review.
