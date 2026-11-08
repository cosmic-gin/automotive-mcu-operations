# Automotive MCU Operations Intelligence Platform

An analytics project for a fictional automotive microcontroller manufacturer. All source records,
targets and findings are simulated. The project has no affiliation with Infineon Technologies.

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
```

The `src/mcu_ops` package holds the pipeline and analytics logic. The `tests` directory verifies
its behavior. The `docs` directory explains the business model and records how the project was built.
