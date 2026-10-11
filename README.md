# ELECTICORE

ELECTICORE is a Flask-based campus portal for secure student elections, confidential anti-ragging reports, a searchable faculty directory, campus events, and downloadable study resources.

## Features

- JWT-authenticated student accounts and role-based administration
- One-student-one-vote enforcement at database level
- Election tally review and controlled publication after voting closes
- Confidential safety reporting with status tracking and institution-approved SMTP delivery
- Incident date, time, location, and context stored with safety reports
- Admin case-status management and direct student notifications
- Optional OpenAI-assisted committee/director email drafting and preliminary low/moderate/extreme urgency estimates, with a reliable local fallback
- Faculty search, event listings, and event reminders saved in the browser
- Authenticated upload and download of PDF, DOC, DOCX, PPT, PPTX, TXT, and ZIP study resources
- Upload size limit, safe server-side filenames, and browser security headers

## Run locally

From PowerShell in the project folder:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m flask --app backend.app db upgrade
python backend\app.py
```

Open `http://127.0.0.1:5000`. For a fresh setup, copy `.env.example` to `.env` and set strong, distinct secret values before starting the app.

Create an account from the profile button. To assign a trusted staff role after creating the account, run:

```powershell
python backend/manage.py promote person@college.edu admin
```

Use `committee` instead of `admin` for staff who should review safety reports but not manage elections.

Admins can create elections and events, review report cases, send notifications to registered students, and review election tallies after voting closes. Publishing a tally makes the official results visible to signed-in campus users. Individual ballots are never included in published results.

## Database migrations

Schema changes are managed by Flask-Migrate/Alembic. Do not use `db.create_all()` or manually alter tables.

For a fresh database, run:

```powershell
python -m flask --app backend.app db upgrade
```

For the prototype database that already has every table in the initial migration, back it up and then mark it as being at the initial revision without attempting to recreate its tables:

```powershell
python -m flask --app backend.app db stamp head
```

For future model changes, create and review a migration before applying it:

```powershell
python -m flask --app backend.app db migrate -m "describe the schema change"
python -m flask --app backend.app db upgrade
```

## Deployment

Set `APP_ENV=production`, strong `SECRET_KEY` and `JWT_SECRET_KEY`, and an approved `DATABASE_URL` before deploying. The supplied `Procfile` runs Waitress on port 8000. For a small single-instance deployment with a persistent disk mounted at `/var/data`, set `DATABASE_URL=sqlite:////var/data/electicore.db` and `UPLOAD_DIR=/var/data/uploads`. For Docker deployments:

```bash
docker build -t electicore .
docker run --env-file .env -p 8000:8000 electicore
```

SQLite suits demonstrations and a small single-instance deployment. Use PostgreSQL and persistent object storage for institution-wide or multi-instance production use. Never commit `.env`, the SQLite database, uploaded files, or SMTP credentials.

## Safety and privacy

ELECTICORE is an account-linked confidential reporting channel; reports are not anonymous. In immediate danger, contact campus security, local emergency services, or the National Anti-Ragging Helpline. Only enable SMTP after the institution approves the recipient and account. OpenAI email drafting and the preliminary low/moderate/extreme urgency estimate are opt-in per report. When the student opts in and `OPENAI_API_KEY` is configured, only the incident description and location are sent to the configured OpenAI API model. The estimate is advisory and must be reviewed by a person; it is not a determination or emergency service. If AI is unavailable or the student does not opt in, the report uses the factual local email template and is marked unassessed. The report reference, date, time, people involved, and additional details are appended locally and are not included in the OpenAI request.
