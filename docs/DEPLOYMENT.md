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

## Free portfolio deployment on Streamlit Community Cloud

### 1. Publish the source to GitHub

Follow the [GitHub push guide](GITHUB_PUSH.md) to review the files, attach your repository and
push `main`. A public repository gives recruiters access to the source and makes the app public
by default. If you keep the repository private, authorize private repository access in
Community Cloud and make the app public separately. [Connect GitHub](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account) · [App visibility](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)

The dashboard builds its own reference snapshot. The separate weekly GitHub Actions workflow
uses the rolling replay and stores its outputs as run artifacts.

### 2. Configure the deployment

Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with the GitHub
account that administers the repository. Choose **Create app**, then **Yup, I have an app**.
You can also start from **Deploy now** under **Streamlit Community Cloud** in the local app's
deployment menu.

| Field | Value |
| --- | --- |
| Repository | `cosmic-gin/automotive-mcu-operations`, or the repository you pushed |
| Branch | `main` |
| Main file path | `app/streamlit_app.py` |
| App URL | Optional. Try `automotive-mcu-operations` if available |
| Advanced settings → Python version | `3.12` |
| Advanced settings → Secrets | Leave blank |

Save the advanced settings and click **Deploy**. The root `requirements.txt` installs the
project and its packaged SQL. The default backend is DuckDB. The app generates its fictional
reference data in temporary storage, so it needs only the committed source files.
[Deployment form](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) · [App dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)

### 3. Verify the recruiter experience

1. Wait for the build and first snapshot. If startup fails, open **Manage app** and inspect
   the logs, then confirm the branch, main file path and Python version.
2. Open the assigned `.streamlit.app` URL in a private browser window. If login is required,
   open **App settings → Sharing** and set the app to public before sharing the URL.
3. Verify the Executive overview displays **69.2%** on-time delivery and **269,913** open
   units for the unfiltered reference period. Select a category and check the KPI updates.
4. Open **Data reliability**. Confirm **67,366** accepted rows and use **Detect a duplicate
   order** to see a separate test row flagged with `duplicate_key`.
5. Add the verified URL to your CV. Community Cloud puts idle apps to sleep. A visitor can
   wake a public app from the sleep screen. A GitHub link gives recruiters a second way to see
   the project and screenshots. [Hibernation and logs](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)

## CV project entry

**Automotive MCU Operations Intelligence Platform** · Python, SQL, Streamlit, DuckDB, PostgreSQL

Built an interactive operations dashboard for 67,366 synthetic semiconductor records.
Implemented delivery and backlog KPIs, inventory reconciliation, and data-quality quarantine.
Verified the full pipeline on PostgreSQL and DuckDB.

Add a **Live demo** link once the public app opens without sign-in. Add a **GitHub** link if the
repository is public.

Use the [Tableau guide](TABLEAU_GUIDE.md) for the separate manual workbook workflow.
