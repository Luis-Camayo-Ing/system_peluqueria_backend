# Seguridad operativa

- Todos los endpoints empresariales requieren autenticación o permisos RBAC.
- Los UUID de usuarios, empleados, servicios y roles se validan contra la
  empresa autenticada.
- Los roles y permisos del sistema no pueden modificarse o eliminarse mediante
  las operaciones administrativas ordinarias.
- En producción se rechazan `DEBUG=true`, secretos cortos, hosts comodín y
  orígenes CORS comodín.
- Swagger y OpenAPI no se publican en producción.
- El backend no debe exponerse directamente a Internet; Nginx actúa como punto
  de entrada y aplica limitación al inicio de sesión y cabeceras de seguridad.
- Los tokens se transportan únicamente sobre HTTPS.

Antes de una liberación ejecute `pip-audit`, revise los hallazgos de GitHub y
rote cualquier credencial que haya aparecido en logs o commits.
