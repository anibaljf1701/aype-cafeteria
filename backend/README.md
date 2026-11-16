# AyPe Coffee API

> **Estado: en construcción.** El backend está en una etapa inicial y todavía faltan archivos y configuración para considerarlo completo y desplegable.

API para consultar el menú de cafés y crear reservas. Está implementada con FastAPI y preparada para ejecutarse en AWS Lambda mediante Mangum.

## Funcionalidad actual

- `GET /api/v1/menu`: consulta los elementos de la tabla DynamoDB del menú.
- `GET /api/v1/reservas/disponibilidad`: devuelve las tazas disponibles para el día de Buenos Aires.
- `POST /api/v1/reservas`: crea una reserva, con un máximo de 2 tazas por persona y un límite diario atómico de 50 tazas.
- Documentación interactiva de FastAPI disponible en `/docs` al ejecutar la API.

La reserva y el incremento del contador se guardan en una única transacción de DynamoDB. El contador diario usa la clave `CONTADOR#AAAA-MM-DD` y una condición sobre `tazas_reservadas`; el límite se comprueba antes de sumar la cantidad solicitada. Así, solicitudes concurrentes no pueden sobrepasar las 50 tazas ni dejar un contador incrementado sin su reserva correspondiente.

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

La aplicación usa la región `us-east-1` por defecto. Puede cambiarse mediante `AWS_REGION`. Los nombres de tabla se configuran con `RESERVAS_TABLE_NAME` y `MENU_TABLE_NAME`; por defecto son `aype-reservas` y `aype-menu`. `CORS_ALLOW_ORIGINS` acepta una lista separada por comas; por defecto permite `http://localhost:8080` y `http://127.0.0.1:8080`.

La tabla de reservas debe tener `id` como clave de partición. Las reservas normales y los registros `CONTADOR#AAAA-MM-DD` conviven en esa tabla; no se necesita un índice para contar las reservas. Las tablas deben crearse y configurarse en AWS antes de usar los endpoints. El rol de ejecución necesita permisos `dynamodb:GetItem` y `dynamodb:TransactWriteItems` sobre la tabla de reservas.

El frontend usa `http://127.0.0.1:8000` como URL local de la API. Para otro entorno, define `window.AYPE_API_BASE_URL` antes del script principal de `frontend/site/index.html` y agrega el origen del sitio a `CORS_ALLOW_ORIGINS`.

Para AWS Lambda, el handler de la aplicación es `app.main.handler`.

## Pendiente

Este repositorio contiene por ahora el código principal de la API, `requirements.txt` y `.gitignore`. Faltan, entre otros elementos, archivos de infraestructura o configuración de despliegue, pruebas automatizadas y configuración de entornos. El despliegue y la integración con recursos reales de AWS aún no están documentados ni verificados.