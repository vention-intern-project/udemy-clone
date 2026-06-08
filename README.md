Structure of the app:

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

feature/feature_name:
models.py defines the data model for that feature (SQLAlchemy models)
schemas.py defines Pydantic request and response models
service.py contains business logic
repository.py contains database access and query functions.

db/ for database engine, session, migrations
common/ shared helper functions or helpers
core/ settings, env