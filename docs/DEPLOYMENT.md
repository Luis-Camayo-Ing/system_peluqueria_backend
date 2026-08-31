# Despliegue y rollback

## Preparación

- `develop` debe contener los PR aprobados de frontend y backend.
- CI debe estar verde en ambos repositorios.
- Debe existir un respaldo restaurable de PostgreSQL.
- `.env.production` debe mantenerse fuera de Git y tener permisos limitados.
- `SECRET_KEY` debe ser aleatorio, tener al menos 32 caracteres y conservarse
  entre despliegues para no invalidar sesiones inesperadamente.

## Despliegue

```bash
docker compose --env-file .env.production pull
docker compose --env-file .env.production config
docker compose --env-file .env.production up -d
docker compose --env-file .env.production ps
```

Verifique:

```bash
curl --fail http://localhost:8080/healthz
curl --fail http://localhost:8080/api/v1/salud
curl --fail http://localhost:8080/api/v1/salud/base-datos
```

Realice después una prueba funcional de inicio de sesión, agenda, ventas,
inventario, caja, compras, administración y reportes.

## Rollback

1. Identifique las etiquetas anteriores `sha-...` del frontend y backend.
2. Cambie `FRONTEND_IMAGE` y `BACKEND_IMAGE` en `.env.production`.
3. Si hubo una migración incompatible, restaure el respaldo validado.
4. Ejecute nuevamente `docker compose pull` y `docker compose up -d`.

No ejecute `docker compose down -v`: la opción `-v` elimina el volumen de
PostgreSQL y destruye los datos persistentes.
