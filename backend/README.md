# AyPe Coffee API

> **Estado: en construcción.** El backend está en una etapa inicial y todavía faltan archivos y configuración para considerarlo completo y desplegable.

API para consultar el menú de cafés y crear reservas. Está implementada con FastAPI y preparada para ejecutarse en AWS Lambda mediante Mangum.

## Funcionalidad actual

- `GET /api/v1/menu`: consulta los elementos de la tabla DynamoDB del menú.
- `GET /api/v1/reservas/disponibilidad`: devuelve las tazas disponibles para el día de Buenos Aires.
- `POST /api/v1/reservas`: crea una reserva, con un máximo de 2 tazas por persona y un límite diario atómico de 50 tazas.
- `GET /api/v1/catas/proximas`: devuelve las fechas semanales próximas y sus cupos disponibles.
- `POST /api/v1/catas/reservas`: reserva de 1 o 2 lugares para una fecha; el mismo email solo puede reservar una vez por fecha.
- Documentación interactiva de FastAPI disponible en `/docs` al ejecutar la API.

La reserva, el contador diario y el acumulador personal se guardan en una única transacción de DynamoDB. El contador global usa la clave `CONTADOR#AAAA-MM-DD`; el personal usa `PERSONA#AAAA-MM-DD#<sha256-del-email-normalizado>`. Las condiciones verifican los topes de 50 tazas globales y 2 por email antes de sumar. Así, solicitudes concurrentes no pueden sobrepasar ninguno de los límites ni dejar contadores incrementados sin su reserva correspondiente. El email se normaliza con `strip().casefold()` antes de calcular la clave.

## Requisitos

- Python 3.10 o posterior.
- AWS y tablas DynamoDB configuradas para el entorno de ejecución.
- Las dependencias listadas en `requirements.txt`.

## Ejecución local

Desde la raíz del proyecto, instala las dependencias y Uvicorn:

```bash
python -m pip install -r requirements.txt uvicorn
```

Configura credenciales y acceso a AWS para que boto3 pueda conectarse a DynamoDB. Después, inicia el servidor:

```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`; la documentación interactiva, en `http://127.0.0.1:8000/docs`.

## Configuración de AWS

La aplicación usa la región `us-east-1` por defecto. Puede cambiarse mediante `AWS_REGION`. Los nombres de tabla se configuran con `RESERVAS_TABLE_NAME` y `MENU_TABLE_NAME`; por defecto son `aype-reservas` y `aype-menu`. `CORS_ALLOW_ORIGINS` acepta los orígenes del frontend separados por comas; en desarrollo permite `http://localhost:8080` y `http://127.0.0.1:8080`. FastAPI responde a `GET`, `POST` y `OPTIONS` y acepta `Content-Type`.

La tabla de reservas debe tener `id` como clave de partición. Las reservas de tazas y catas, sus contadores y las claves de email conviven en esa tabla; no se necesita un índice para contar los cupos. Las tablas deben crearse y configurarse en AWS antes de usar los endpoints. El rol de ejecución necesita permisos `dynamodb:GetItem` y `dynamodb:TransactWriteItems` sobre la tabla de reservas.

El calendario de catas es semanal y se identifica por fecha ISO (`AAAA-MM-DD`). Se configura con `CATA_DIA_SEMANA` (0 lunes a 6 domingo; valor predeterminado `5`, sábado), `CATA_CUPO_TOTAL` (predeterminado `10`) y `CATA_SEMANAS_PROXIMAS` (predeterminado `8`). El endpoint público lee los contadores por fecha y el POST crea la reserva y reclama el email normalizado en la misma transacción; los intentos duplicados o sin cupo responden `409 Conflict`.

El contenedor del frontend genera `/config.js` al arrancar NGINX desde `AYPE_API_BASE_URL` (por defecto `http://127.0.0.1:8000`). Pasa la URL base de la API al contenedor para cada entorno; no se compila ni se incrusta en `index.html`. Configura `CORS_ALLOW_ORIGINS` en la API con el origen público del frontend, no con la URL de la API.

Para AWS Lambda, el handler de la aplicación es `app.main.handler`.

## Pendiente

Este repositorio contiene por ahora el código principal de la API, `requirements.txt` y `.gitignore`. Faltan, entre otros elementos, archivos de infraestructura o configuración de despliegue, pruebas automatizadas y configuración de entornos. El despliegue y la integración con recursos reales de AWS aún no están documentados ni verificados.