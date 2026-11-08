# Deployment

The source repository and application can be shared after review. All bundled or generated
operational records and thresholds are fictional.

## Local DuckDB demo

From the repository, install the package and run Streamlit.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m streamlit run app/streamlit_app.py
```

Without an existing local database, Streamlit generates the standard synthetic snapshot in an
OS temporary directory. The process caches the validated demo. If you run the standalone
database loader first, Streamlit opens the committed local DuckDB file instead. Stop the dashboard
before replacing that file from a separate process.

## Local PostgreSQL stack

Install Docker with the Compose plugin and start the Docker engine. Copy `.env.example` to
`.env`, set `MCU_BACKEND=postgresql`, and enter a local password in `POSTGRES_PASSWORD`.
Create your data and bring up the loopback-only database.

```powershell
Copy-Item .env.example .env
# Edit .env now with your chosen backend and local password.
docker compose up -d --wait postgres
python -m mcu_ops.data_generation.generator
python -m mcu_ops.etl
python -m mcu_ops.database
python -m pytest
python -m streamlit run app/streamlit_app.py
```

Use another `POSTGRES_PORT` in `.env` if 5432 is in use. `POSTGRES_HOST`, `POSTGRES_USER`,
`POSTGRES_DB` and `POSTGRES_PASSWORD` configure the SQLAlchemy connection.
`MCU_POSTGRES_URL` may supply a complete SQLAlchemy URL from a protected environment.
Never store credentials in a committed file. `docker compose stop postgres` stops the service
and retains its data volume.

## GitHub and Streamlit Community Cloud

1. Review `git status --short` and `git ls-files`. Source, documentation and screenshots
   belong in Git. Raw or exported data, reports, local databases and `.env` are ignored.
2. Create a GitHub repository using your account when ready to share. Add the remote with
   `git remote add origin <repository-url>` and push `git push -u origin main`.
3. Verify **Actions → Test and lint**. Use **Actions → Weekly fictional operations report →
   Run workflow** on the default branch and check the report artifact.
4. Sign in to Streamlit Community Cloud and choose **Create app**. Select your repository,
   branch `main`, and main file path `app/streamlit_app.py`. Select Python 3.12 in advanced
   settings. The root `requirements.txt` installs the project, including its SQL resources.
   [Streamlit app dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
5. Deploy the app and open the resulting URL. Wait for the initial deterministic snapshot.
   Check the executive page, change the dates or category, and verify the isolated duplicate
   check on Data Reliability. Cloud demo startup uses DuckDB and temporary storage.

Use the [Tableau guide](TABLEAU_GUIDE.md) for the separate manual workbook workflow.
