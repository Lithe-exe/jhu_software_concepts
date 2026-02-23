# Module 5
Sultan Jacobs 
JHU ID: B443F8
Module info: Module 5 Testing and Documentation Assignment| Due 02/23/26 @ 11:59 EST

## Overview
This module contains a Python project over a local host dynamic website that gathers info by scraping on "Gradcafe". This module has automated testing, 100% code coverage, and CI using GitHub Actions.  
It also includes Sphinx documentation that is built and deployed via GitHub Pages.

## Project structure
- `src/board/` — main package code
- `tests/` — pytest test suite
- `docs/` — Sphinx documentation source
- `coverage_summary.txt` — terminal coverage summary 
### Fresh Install

**Method 1: standard pip**
1. `python -m venv venv`
2. `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
3. `pip install -r requirements.txt`
4. `python setup.py install` (or `pip install -e .`)
5. `python src/app.py`

**Method 2: uv (Faster, reproducible alternative)**
1. `uv venv`
2. `source .venv/bin/activate`
3. `uv pip sync requirements.txt`
4. `uv pip install -e .`
5. `python src/app.py`

## Instructions

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

macOS / Linux:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

### Run tests:
pytest
Run tests with coverage which prints the coverage report to the terminal:

pytest --cov-report=term-missing

Testing using pylint by pasting this into terminal:
python -m pylint src\app.py src\board\*.py


The CI workflow is located at:

.github/workflows/test.yml

It runs on push and executes the pytest test suite and PostgreSQL.


Documentation (Sphinx / GitHub Pages)
Sphinx documentation is located under docs/.
The docs are built and deployed via GitHub Actions and published using GitHub Pages.

Documentation site:
https://lithe-exe.github.io/jhu_software_concepts/testing.html