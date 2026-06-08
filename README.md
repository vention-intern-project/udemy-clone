Structure of the app:
```text
src/
  app/
    main.py
    core/
      config.py
    api/
      v1/
        router.py
        endpoints/
          auth.py
          users.py
    feature/
      users/
        models.py
        schemas.py
        service.py
        repository.py
    db/
    common/
tests/

```

### `feature/feature_name`

* **`models.py`** – defines the data model for that feature (SQLAlchemy models)
* **`schemas.py`** – defines Pydantic request and response models
* **`service.py`** – contains business logic
* **`repository.py`** – contains database access and query functions

### Core Directories

* **`db/`** – for database engine, session, migrations
* **`common/`** – shared helper functions or helpers
* **`core/`** – settings, env

## Docker

This project uses Docker for local development with `uv` and PostgreSQL.

### Run

```bash
docker compose up --build
```

API:

```text
http://localhost:8000
```

Stop services:

```bash
docker compose down
```


## Environment

Create a local `.env` file in the project root. A matching `.env.example` file is provided as a template.

Required variables:

```dotenv
APP_NAME=udemy-clone
DEBUG=true

POSTGRES_DB=udemy_clone
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/udemy_clone
```

`DATABASE_URL` uses the async PostgreSQL driver, so it should match the driver used by the app code.
