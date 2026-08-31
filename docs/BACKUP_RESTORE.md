# Respaldo y restauración de PostgreSQL

Los siguientes comandos asumen que `compose.yaml` está activo y que las
variables se encuentran en `.env.production`.

## Crear un respaldo

Cree primero una carpeta fuera del repositorio:

```bash
mkdir -p backups
```

Ejecute un respaldo en formato personalizado:

```bash
docker compose --env-file .env.production exec -T db \
  pg_dump --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --format=custom > backups/erp-beauty-pro.dump
```

Compruebe que el archivo no esté vacío y guarde una copia cifrada en un
destino separado. No agregue respaldos a Git.

## Validar una restauración

La restauración es destructiva para la base objetivo. Debe probarse primero
en una base aislada:

```bash
docker compose --env-file .env.production exec -T db \
  createdb --username "$POSTGRES_USER" erp_beauty_pro_restore_test

docker compose --env-file .env.production exec -T db \
  pg_restore --username "$POSTGRES_USER" \
  --dbname erp_beauty_pro_restore_test --clean --if-exists --no-owner \
  < backups/erp-beauty-pro.dump
```

Luego consulte las tablas críticas y documente fecha, tamaño, responsable y
resultado. El cierre de Sprint 30 requiere evidencia de una restauración
exitosa, no solo de la creación del archivo.
