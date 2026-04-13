## GP Appointments API (FastAPI + SQLite)

Backend-only project for managing GP (personal doctor) appointment scheduling via HTTP API.

### Documentation (for your PDF)

Един Word файл с пълната документация за изпит/курсова (API, архитектура, UML изход, самоанализ):

| Файл | Съдържание |
|------|------------|
| `docs/DOCUMENTATION.docx` | Генерира се с `python docs/generate_documentation_docx.py` (изисква `python-docx` от `requirements.txt`) |

Изходните markdown файлове в `docs/` (`02_ARCHITECTURE.md`, `03_UML.md`, `04_SELF_ANALYSIS.md`) остават за редакция в Git; `.docx` се прегенерира от скрипта при нужда.

### Requirements

- Python 3.11+

### Setup

```bash
cd gp-appointments
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### Database (Alembic)

Schema is managed with **Alembic** (not `create_all` at startup). After install:

```bash
alembic upgrade head
```

This creates or updates `app.db` in the project root (unless `DATABASE_URL` points elsewhere).

When you change `app/models.py`, generate a new revision and upgrade:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

For a clean slate you can still remove the file and re-run `alembic upgrade head`:

```bash
rm -f app.db
alembic upgrade head
```

Tests use an in-memory SQLite database and `Base.metadata.create_all` in the test fixture (no Alembic required for `pytest`).

### Security / configuration

- Set a strong **`JWT_SECRET`** in any shared or production environment. In `APP_ENV=dev` the default secret is allowed; in other environments the app refuses to start with the default.
- Optional: `DATABASE_URL`, `JWT_EXPIRE_MINUTES`, `PBKDF2_ITERATIONS`, `APP_ENV`.

### Run

```bash
uvicorn app.main:app --reload
```

Open API docs: `http://127.0.0.1:8000/docs`

### Auth (quick start)

1. Register: `POST /auth/register-doctor`, `POST /auth/register-patient`
2. Login: `POST /auth/login` with email/password; response includes `access_token`
3. Other endpoints: header `Authorization: Bearer <token>`

Doctor/patient **`id`** values and appointment **`doctor_id` / `patient_id`** are all **`users.id`**.

### Time handling

- Incoming datetimes may be timezone-aware; they are **normalized to UTC** and stored as **naive UTC** in SQLite.
- Business rules (24h / 12h windows, schedule checks) use that same **UTC** clock.

### Lint / types (optional)

```bash
ruff check app tests
ruff format app tests
mypy app
```

### Test

```bash
python -m pytest -q
```

### Notes

- Appointments must start and end on the **same calendar day** (no cross-midnight visits).
- A doctor may have **at most one** temporary schedule change; a new one replaces the previous.
- Domain errors from services are **`DomainError`** subclasses (e.g. `BadRequestError`, `ConflictError`) with an **`http_status`**; `main.py` maps them to JSON `{"detail": "..."}`.
