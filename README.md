# ET Master Workflow Automation

Automates daily sync from `Master_DB` into target Google Sheet tabs (such as `FYE` / `FYE 1`), including optional red-row highlighting for audit clients.

## Features

- Sync source data from `Master_DB` to a target worksheet
- Use `Company Registered Name` as primary key
- Update existing rows
- Append new rows
- Remove rows no longer present (after source filtering)
- Exclude `Engagement Status = Terminated`
- Highlight full rows in red when `Services with ET Management` contains `Audit`
- Run manually or schedule daily at **09:00 AM Vietnam time**
- Run in Docker / Docker Compose

## Project Files

- `test.py`: Main sync job
- `highlight_red_audit.py`: Conditional formatting helper
- `sheduler.py`: APScheduler runner (daily 09:00, `Asia/Ho_Chi_Minh`)
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container build recipe
- `docker-compose.yml`: Container runtime configuration
- `service_account.json`: Google service account key (local secret, do not commit)

## Prerequisites

- Python 3.10+ (recommended 3.11)
- Google Sheets API and Google Drive API enabled
- Service account has Editor access to:
  - source spreadsheet (`Master_DB`)
  - target spreadsheet (`FYE` / `FYE 1`)
- `service_account.json` placed in project root

## Local Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Update these values in `test.py`:

- `SERVICE_ACCOUNT_FILE`
- `SHEET_ID`
- `WORKSHEET_NAME`
- `SOURCE_SHEET_ID`
- `SOURCE_WORKSHEET_NAME`

## Run Manually

```powershell
python .\test.py
```

## Schedule Daily at 09:00 Vietnam Time

```powershell
python .\sheduler.py
```

Scheduler timezone is `Asia/Ho_Chi_Minh`.

## Docker Usage

Build and start:

```powershell
docker compose up -d --build
```

View logs:

```powershell
docker compose logs -f
```

Stop:

```powershell
docker compose down
```

## Corporate SSL Note (Docker Build)

If Docker build fails with `SSLCertVerificationError`, add trusted hosts to your `pip install` layer in `Dockerfile`:

```dockerfile
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt
```

## Data Logic Summary

- Primary key: `Company Registered Name`
- Normalize FYE values (`strip` + `capitalize`)
- Exclude rows where `Engagement Status == "Terminated"`
- Ignore rows with empty primary key
- Deduplicate source by primary key (`keep="last"`)
- Update columns (if present in target):
  - `Client ID`
  - `UEN (Unique Entity Number)`
  - `Financial Year End`
  - `Services with ET Management`
- New-row columns:
  - `Client ID`
  - `UEN (Unique Entity Number)`
  - `Company Registered Name`
  - `Financial Year End`
  - `Services with ET Management`
  - `Engagement Status`

## Audit Highlighting

`highlight_red_audit.py` creates conditional formatting so the **entire row** turns red when `Services with ET Management` contains `Audit`.

## Security

- Never commit `service_account.json`
- Keep secrets in `.gitignore`
- Rotate credentials if exposed

## Troubleshooting

- `ValueError: '<column>' is not in list`
  - Target worksheet header is missing required column name
- Script says rows were added but target sheet looks unchanged
  - Verify `WORKSHEET_NAME`, sheet permissions, and logs
- Docker build fails with SSL certificate errors
  - Apply the trusted-host pip workaround shown above