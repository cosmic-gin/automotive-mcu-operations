# Publish the project to GitHub

The local branch is `main`. These commands let you review the exact commits and choose when
to publish them. Open a new PowerShell window so it sees any recent GitHub CLI PATH updates.

## 1. Review the local release

```powershell
Set-Location 'C:\Users\Cosmic\Desktop\Job search\Automotive MCU Operations'
gh auth status
git status --short --branch
git log -3 --oneline
git remote -v
git ls-files
git check-ignore .env data/operations.duckdb reports/sample.md
```

Check that `gh auth status` shows the GitHub account you want to own the project.
If `gh` is missing from PATH, reopen PowerShell or use
`Set-Alias gh "$env:ProgramFiles\GitHub CLI\gh.exe"` when installed at that path. The ignored paths should print,
and the tracked file listing should contain source, docs, tests and screenshots.

If Git reports dubious ownership in your normal terminal, scope the trust exception to this
exact workspace. It was initialized under the sandbox account.

```powershell
git config --global --add safe.directory 'C:/Users/Cosmic/Desktop/Job search/Automotive MCU Operations'
```

## 2. Choose a GitHub repository

For a new repository, the following creates an empty private repository and attaches
it as `origin`. Use `--public` in place of `--private` when you want public portfolio access.

```powershell
gh auth setup-git
gh repo create cosmic-gin/automotive-mcu-operations --private --source=. --remote=origin --description "Fictional automotive MCU operations analytics with Python, PostgreSQL, DuckDB and Streamlit"
git remote -v
```

If you already created an empty repository, skip `gh repo create` and attach its URL.
If `origin` already exists, inspect it and use it when it points to your intended repository.

```powershell
gh auth setup-git
git remote add origin https://github.com/cosmic-gin/automotive-mcu-operations.git
git remote -v
git ls-remote --heads origin
```

If the destination already has commits, fetch and review its history first. A README created
on GitHub can introduce a separate history. An empty remote is the simplest first publication.

## 3. Push after reviewing the destination

This command publishes the commits on local `main` to `origin` and sets the upstream branch.

```powershell
git push -u origin main
git status --short --branch
gh repo view --web
```

## 4. Verify hosted automation

Wait for **Test and lint** in the repository's **Actions** tab. It runs the suite with a
disposable PostgreSQL service. Then dispatch the weekly reporting workflow once and inspect
the result. Enter the weekly run ID from the list at the prompt.

```powershell
gh run list --workflow ci.yml --limit 3
gh workflow run weekly-report.yml --ref main
gh run list --workflow weekly-report.yml --limit 3
$reportRunId = Read-Host 'Weekly report run ID'
gh run watch $reportRunId --exit-status
gh run download $reportRunId --dir reports/github-actions
```

The report artifact contains Markdown, execution status, validation summaries and quarantine
evidence for the rolling fictional snapshot. If you also want a hosted dashboard, follow
the [Streamlit deployment guide](DEPLOYMENT.md). Tableau workbook setup is documented
separately in the [Tableau guide](TABLEAU_GUIDE.md).

[GitHub CLI repository creation](https://cli.github.com/manual/gh_repo_create) ·
[GitHub CLI workflow dispatch](https://cli.github.com/manual/gh_workflow_run)
