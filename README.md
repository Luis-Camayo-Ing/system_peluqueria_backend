# ERP Beauty Pro — Backend

API REST del ERP para peluquerías, construida con FastAPI, SQLAlchemy,
PostgreSQL y Alembic.

## Requisitos

- Python 3.14
- PostgreSQL 18
- Docker Desktop, opcional para el despliegue con contenedores

## Desarrollo local

```bash
python -m venv .venv
```

Active el entorno virtual y ejecute:

```bash
python -m pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`. Swagger se expone
en `/docs` únicamente fuera del entorno `production`.

Genere un secreto de producción con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

No almacene `.env`, contraseñas, respaldos ni secretos en Git.

## Validación

```bash
python -m pip check
python -m pip_audit -r requirements.txt
python -m compileall -q app tests
python -m unittest discover -s tests -p "test_*.py" -v
alembic upgrade head
alembic check
```

El pipeline ejecuta estas comprobaciones con PostgreSQL real y también
construye la imagen del contenedor. Los pushes a `main` publican la imagen
en GitHub Container Registry.

## Producción con Docker Compose

1. Instale Docker Desktop y habilite Docker Compose.
2. Copie `.env.production.example` como `.env.production`.
3. Reemplace todos los valores `CAMBIAR`, configure el dominio en
   `ALLOWED_HOSTS` y defina las imágenes publicadas.
4. Ejecute:

```bash
docker compose --env-file .env.production pull
docker compose --env-file .env.production up -d
docker compose --env-file .env.production ps
```

El servicio `migrate` aplica Alembic una sola vez después de que PostgreSQL
esté saludable. El frontend se publica por defecto en el puerto `8080` y el
backend permanece dentro de la red privada de Compose.

Consulte [despliegue](docs/DEPLOYMENT.md),
[respaldo y restauración](docs/BACKUP_RESTORE.md) y
[seguridad](docs/SECURITY.md) antes de promover una versión.
