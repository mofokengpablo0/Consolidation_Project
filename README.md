# Consolidation Project 

A Django-based news platform with role-based access (Readers, Journalists, Editors), a REST API, and Sphinx documentation. Runs on **MariaDB**.

> **For reviewers:** see the note at the end of Step 1 below — [`REVIEWER_SECRETS.txt`](./REVIEWER_SECRETS.txt) gives you working credentials with zero setup. This file is temporary and will be removed after grading.

## Project Structure

```
Consolidation_Project/
├── accounts/          # Users, roles, auth
├── news/              # Articles, publishers, newsletters, API
├── config/            # Settings package (settings.py, urls.py, wsgi.py, asgi.py)
├── static/            # Project static files
├── templates/         # Project templates
├── media/             # User-uploaded content (not committed)
├── data/              # SQLite fallback data (not committed)
├── docs/              # Sphinx documentation
├── tests/             # Test suite
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── REVIEWER_SECRETS.txt
└── README.md
```

---

## Prerequisites

- Python 3.12+
- Git
- **Docker Desktop, installed and running.** Both setups below use Docker for the MariaDB database — the "venv" option only skips Docker for the Django app itself. On Docker Playground / Iximiuz Labs, Docker is already running and this doesn't apply.

---

## Step 1: Get a `SECRET_KEY`

Every setup needs this first. Clone the repo, then generate a key.

**Windows (PowerShell)**
```powershell
git clone https://github.com/mofokengpablo0/Consolidation_Project.git
cd Consolidation_Project
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py shell
```

**macOS/Linux (bash)**
```bash
git clone https://github.com/mofokengpablo0/Consolidation_Project.git
cd Consolidation_Project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py shell
```

Inside the Python shell that opens (same command either way):
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
exit()
```

Copy the printed value, then create your `.env` file:

**Windows (PowerShell)**
```powershell
Copy-Item .env.example .env
notepad .env
```

**macOS/Linux (bash)**
```bash
cp .env.example .env
nano .env
```

Fill it in:
```
SECRET_KEY=<paste-your-generated-key-here>

DB_ENGINE=mariadb
DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=<pick-your-own-password>
DB_HOST=127.0.0.1
DB_PORT=3306
```

Save and close.

> **Reviewers:** skip everything above in this step — copy the contents of [`REVIEWER_SECRETS.txt`](./REVIEWER_SECRETS.txt) straight into `.env` instead. It already has a working `SECRET_KEY` and database credentials, so there's nothing left to generate or choose.

---

## Option A: Run everything in Docker (simplest)

App + database both run in containers. Works the same locally, on a teammate's machine, or on Docker Playground / Iximiuz Labs.

> Make sure `.env` is filled in *before* the first run — MariaDB only sets its password on the container's very first startup.

**Windows (PowerShell)**
```powershell
docker compose up --build
```

**macOS/Linux (bash)**
```bash
docker compose up --build
```

Same command either way. Once you see `Listening at: http://0.0.0.0:8000`:

- **Local Docker:** open `http://localhost:8000`
- **Docker Playground:** click the port badge for `8000` at the top of the page
- **Iximiuz Labs:** `+` next to your terminal tabs → **Add HTTP(S) Port Tab** → Port `8000`, Protocol `HTTP` → **ADD**

Create a superuser (open a second terminal while `docker compose up` is running):

**Windows (PowerShell)**
```powershell
docker compose exec web python manage.py createsuperuser
```

**macOS/Linux (bash)**
```bash
docker compose exec web python manage.py createsuperuser
```

Run the tests — **must** be run inside the `web` container, not on your host machine, since only the container can reach the `db` service by name:

**Windows (PowerShell)**
```powershell
docker compose exec web python test_app.py
```

**macOS/Linux (bash)**
```bash
docker compose exec web python test_app.py
```

Stop everything when you're done:

**Windows (PowerShell)**
```powershell
docker compose down
```

**macOS/Linux (bash)**
```bash
docker compose down
```

Add `-v` to also delete the database and start fully fresh next time.

---

## Option B: Django locally, database in Docker

Use this if you want to edit code with `runserver`'s auto-reload instead of rebuilding a container each time.

Start just the database (from the venv setup in Step 1, same terminal):

**Windows (PowerShell)**
```powershell
docker compose up -d db
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**macOS/Linux (bash)**
```bash
docker compose up -d db
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

Run the tests (same machine, same terminal, `db` already running):

**Windows (PowerShell)**
```powershell
python test_app.py
```

**macOS/Linux (bash)**
```bash
python test_app.py
```

Stop the database when you're done:

**Windows (PowerShell)**
```powershell
docker compose stop db
```

**macOS/Linux (bash)**
```bash
docker compose stop db
```

---

## Troubleshooting

**`WARN ... "DB_NAME" variable is not set`**
`.env` is missing or empty. Go back to Step 1.

**`Can't connect to MySQL server on '127.0.0.1'`**
Either the `db` container isn't running yet (`docker compose up -d db`, wait, then `docker compose ps` should show `healthy`), or you're running Django/tests on a different machine than the one running `db` — e.g. Django locally while `db` runs in a remote Docker Playground session. Both must be in the same place.

**Database has the wrong username/password after editing `.env`**
MariaDB only sets credentials on its *first* startup. Reset with:

**Windows (PowerShell)**
```powershell
docker compose down -v
```

**macOS/Linux (bash)**
```bash
docker compose down -v
```
Then start again.

**Any `docker` command fails immediately**
Docker Desktop isn't running — open it and wait for "Docker Desktop is running." Not applicable on Docker Playground / Iximiuz Labs.

---

## Documentation

Sphinx docs live in `docs/`. To build them (from the repo root):

**Windows (PowerShell)**
```powershell
cd docs
.\make.bat html
```

**macOS/Linux (bash)**
```bash
cd docs
make html
```

Open `docs/build/html/index.html`.