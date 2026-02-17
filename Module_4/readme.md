# Module 4
Sultan Jacobs 
JHU ID: B443F8
Module info: Module 4 Testing and Documentation Assignment| Due 02/15/26 @ 11:59 EST

## Overview
This module contains a Python project over a local host dynamic website that gathers info by scraping on "Gradcafe". This module has automated testing, 100% code coverage, and CI using GitHub Actions.  
It also includes Sphinx documentation that is built and deployed via GitHub Pages.

## Project structure
- `src/board/` — main package code
- `tests/` — pytest test suite
- `docs/` — Sphinx documentation source
- `coverage_summary.txt` — terminal coverage summary 
## Setup
Create and activate a virtual environment, then install dependencies:

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

macOS / Linux:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Run tests:
pytest
Run tests with coverage which prints the coverage report to the terminal:

pytest --cov-report=term-missing

The CI workflow is located at:

.github/workflows/test.yml

It runs on push and executes the pytest test suite and PostgreSQL.


Documentation (Sphinx / GitHub Pages)
Sphinx documentation is located under docs/.
The docs are built and deployed via GitHub Actions and published using GitHub Pages.

Documentation site:
https://lithe-exe.github.io/jhu_software_concepts/testing.html