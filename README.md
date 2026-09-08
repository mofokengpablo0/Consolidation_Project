# Consolidation Project — News Application

A Django-based news platform with role-based access (Readers, Journalists, Editors), a REST API, and Sphinx documentation. Runs on **MariaDB** (both the local/venv setup and the Docker setup use MariaDB, not SQLite).

> **For reviewers:** a working `SECRET_KEY` and database credentials are provided in [`REVIEWER_SECRETS.txt`](./REVIEWER_SECRETS.txt) at the repo root for grading convenience — copy its contents into a `.env` file (see [Environment variables & secrets](#environment-variables--secrets) below) to run the app immediately without generating your own values. This file will be removed once grading is complete and should not be used for any real deployment.

## Project Structure

```
Consolidation_Project/
├── Code Files/
│   └── news_project/          # Django project root (contains manage.py)
│       ├── accounts/          # User model, auth, roles
│       ├── news/              # Articles, publishers, newsletters, API
│       ├── config/            # Settings package (settings.py, urls.py, wsgi.py, asgi.py)
│       ├── docs/              # Sphinx documentation
│       ├── static/ media/ templates/
│       ├── manage.py
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── entrypoint.sh
│       ├── .env.example
│       └── REVIEWER_SECRETS.txt
└── README.md                  # This file
```

---

## Prerequisites (both options)

- Python 3.12+
- Git
- **Docker Desktop, installed AND running.** Both setup paths below use Docker to run the MariaDB database — even the "venv" option only skips Docker for the *Django app itself*, not the database. Before running any `docker` command, open Docker Desktop and wait for it to report "Docker Desktop is running" (the whale icon in your system tray should be steady, not animating). Running a `docker` command while the daemon is stopped will fail with a connection error, not a helpful message — if any `docker` command below fails immediately, check this first. On Docker Playground / Iximiuz Labs, the daemon is already running for you, so this step doesn't apply there.

---

## Option 1: Run with venv (Django app locally, database in Docker)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/mofokengpablo0/Consolidation_Project.git
   cd "Consolidation_Project/Code Files/news_project"
   ```

2. **Create and activate a virtual environment**

   Windows (PowerShell):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   macOS/Linux:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create your `.env` file** — see [Environment variables & secrets](#environment-variables--secrets) below for how to generate a `SECRET_KEY` and choose your own database credentials.
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in real values.

5. **Start the database only** (MariaDB, via Docker — nothing else)
   ```bash
   docker compose up -d db
   ```
   This starts just the `db` service in the background and exposes it on `127.0.0.1:3306`. The database and user named in `.env` (`DB_NAME`, `DB_USER`, `DB_PASSWORD`) are created automatically the first time this container starts.

6. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser** (for `/admin/` access)
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Open the app**
   Visit `http://127.0.0.1:8000` in your browser.

10. **When finished**, stop the database container:
    ```bash
    docker compose stop db
    ```

---

## Option 2: Run everything with Docker (app + database)

Works identically on your local machine, a teammate's machine, or a browser-based environment like [Docker Playground](https://labs.play-with-docker.com/) or [Iximiuz Labs](https://labs.iximiuz.com/) — no local Python, MariaDB, or dependency installation needed at all.

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/mofokengpablo0/Consolidation_Project.git
   cd "Consolidation_Project/Code Files/news_project"
   ```

2. **Create your `.env` file** — see [Environment variables & secrets](#environment-variables--secrets) below.
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in real values — in particular, choose your own `DB_USER`/`DB_PASSWORD` here rather than using the example placeholders; these are what the MariaDB container will use to create the database and user automatically on first startup.

   Reviewers can instead copy the contents of `REVIEWER_SECRETS.txt` straight into `.env` to skip this step entirely.

3. **Build and start both containers**
   ```bash
   docker compose up --build
   ```

   > **Important:** make sure `.env` is filled in *before* running this for the first time. MariaDB only creates the database and user during its container's very first startup — if it starts once with missing or blank credentials, editing `.env` afterward won't fix it. If that happens, reset with `docker compose down -v` (see Troubleshooting below) and start again.

   This will:
   - Start a MariaDB container and create the database/user from your `.env` values
   - Build the Django image from the `Dockerfile`
   - Wait for the database to be ready, then apply migrations automatically
   - Collect static files
   - Start the app via Gunicorn on port `8000`

4. **Open the app**

   - **Local Docker:** visit `http://localhost:8000`
   - **Docker Playground:** click the port badge (or use "OPEN PORT" → `8000`) at the top of the session page
   - **Iximiuz Labs:** click the `+` next to your terminal tabs → **Add HTTP(S) Port Tab** → set Port to `8000`, Protocol to `HTTP` → click **ADD**

5. **Create a superuser** (in a separate terminal, while the app is running)
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

6. **(Optional) Connect to the database directly**, e.g. to inspect tables or run manual SQL — no local `mysql` client needed, it runs inside the container:
   ```bash
   docker compose exec db mysql -u root -p
   ```
   Enter the `DB_PASSWORD` value from your `.env` when prompted (the `MYSQL_ROOT_PASSWORD` is set to the same value).

7. **Stop the app**
   ```bash
   docker compose down
   ```
   Add `-v` (`docker compose down -v`) to also delete the database and media volumes and start fully fresh next time.

---

## Environment variables & secrets

`SECRET_KEY` and all database credentials are read from environment variables — **none of them are hardcoded or committed to this repository.**

### 1. Generate a `SECRET_KEY`

```bash
python manage.py shell
```
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```
```python
exit()
```
Copy the printed value.

### 2. Choose your own database credentials

Pick a database name, username, and password — these don't need to match any example shown here; you're defining them, not looking them up. The MariaDB container creates the database and user automatically using whatever you put in `.env`.

### 3. Fill in `.env`

```
SECRET_KEY=<paste-generated-key-here>

DB_ENGINE=mariadb
DB_NAME=<your-chosen-database-name>
DB_USER=<your-chosen-username>
DB_PASSWORD=<your-chosen-password>
DB_HOST=127.0.0.1
DB_PORT=3306
```

Notes on `DB_HOST`:
- **Option 1 (venv + Docker database only):** use `127.0.0.1` — your local Django process reaches the database container through its published port.
- **Option 2 (everything in Docker):** `docker-compose.yml` overrides this to `db` automatically (the service name), since containers reach each other by service name on Docker's internal network, not `127.0.0.1`. You don't need to change this yourself — it's already handled in the `web` service's `environment:` block.

`.env` is listed in `.gitignore` and will never be committed.

- **Docker setup:** `.env` is loaded automatically via `env_file` in `docker-compose.yml`.
- **venv setup:** this project reads settings with plain `os.getenv()`, which does **not** auto-load `.env` files by itself. Either export the values into your shell manually before running `manage.py` commands, or use a tool like `python-dotenv` if you'd prefer automatic loading (not currently a project dependency).

  PowerShell:
  ```powershell
  Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
  ```
  macOS/Linux:
  ```bash
  export $(grep -v '^#' .env | xargs)
  ```

**Reviewers/graders:** skip steps 1–2 above and instead copy the contents of `REVIEWER_SECRETS.txt` (repo root) directly into `.env` for working credentials with zero setup.

---

## Documentation

API and code documentation is built with Sphinx. To view it locally (from the repo root):

```bash
cd "Consolidation_Project/Code Files/news_project/docs"
.\make.bat html      # Windows
# or
make html             # macOS/Linux
```

If you're already inside `news_project` from an earlier step, just run `cd docs` instead.

Then open `docs/build/html/index.html` in your browser.

---

## Troubleshooting

**`WARN[0000] The "DB_NAME" variable is not set. Defaulting to a blank string.`**
`.env` is missing or empty. Run `cp .env.example .env` and fill in real values before starting the `db` service.

**`django.db.utils.OperationalError: Can't connect to MySQL server on '127.0.0.1'`** (Option 1)
Two possible causes:
1. The database container isn't running yet, or hasn't finished starting. Run `docker compose up -d db`, wait a few seconds, then check `docker compose ps` — the `db` service should show `healthy` before you run `migrate` or `runserver`.
2. You're running Django (or `test_app.py`) on a **different machine** than the one running the `db` container — e.g. Django on your local computer while `db` is running in a remote Docker Playground/Iximiuz Labs session. `127.0.0.1` always means "this machine," so it can't reach a container on a different machine. Both the app and the database must run in the same place — either both local, or both inside the same remote session (see Running Tests below for the container-exec approach).

**Database container started once with wrong/blank credentials, and fixing `.env` didn't help**
MariaDB only initializes its database and user the *first* time the container starts with an empty data volume. A stale volume keeps the old (bad) credentials regardless of what `.env` now says. Reset it:
```bash
docker compose down -v
docker compose up -d db      # Option 1
# or
docker compose up --build    # Option 2
```
`-v` deletes the database volume so it reinitializes cleanly from the current `.env`.

**`docker: command not found` or any `docker` command hangs/fails immediately**
Docker Desktop isn't running. Open it and wait for "Docker Desktop is running" before retrying (see Prerequisites above). Not applicable on Docker Playground / Iximiuz Labs, where Docker is already running.

---

## Running Tests

A comprehensive integration test suite is included. It must run in the **same environment as the database** — you cannot run it on your local machine while the database container is running in Docker Playground/Iximiuz Labs, or vice versa; `127.0.0.1` on your laptop and `127.0.0.1` inside a remote Playground session are different machines.

**If you're using Option 1 (venv locally + Docker database locally):** make sure `docker compose up -d db` is running on the *same machine*, then:
```bash
python test_app.py
```

**If you're using Option 2 (everything in Docker, e.g. on Docker Playground/Iximiuz Labs):** run the tests *inside* the `web` container, not on your local machine — this ensures the test process is on the same Docker network as `db`:
```bash
docker compose exec web python test_app.py
```