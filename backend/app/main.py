import os
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from mangum import Mangum
import boto3
from botocore.exceptions import ClientError

# Configuración de la API
app = FastAPI(
    title="AyPe Coffee API",
    description="Backend Serverless para gestión de menú y reservas limitadas (Máximo 50 tazas/día).",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            'CORS_ALLOW_ORIGINS',
            'http://localhost:8080,http://127.0.0.1:8080',
        ).split(',')
        if origin.strip()
    ],
    allow_methods=['GET', 'POST'],
    allow_headers=['Content-Type'],
)

# Inicialización de DynamoDB (Asume que los nombres de las tablas vienen por variables de entorno)
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
RESERVAS_TABLE = os.getenv('RESERVAS_TABLE_NAME', 'aype-reservas')
MENU_TABLE = os.getenv('MENU_TABLE_NAME', 'aype-menu')
MAX_TAZAS_DIARIAS = 50
ZONA_HORARIA = ZoneInfo('America/Argentina/Buenos_Aires')

# --- Modelos de Datos (Pydantic) ---
class ReservaRequest(BaseModel):
    nombre_cliente: str = Field(min_length=1, max_length=100)
    email: EmailStr
    variedad_cafe: str = Field(pattern='^(Ayme|Irupé|Kimey)$')
    cantidad_tazas: int = Field(ge=1, le=2)
    
class ReservaResponse(BaseModel):
    id_reserva: str
    fecha: str
    estado: str
    mensaje: str

# --- Endpoints ---

@app.get("/api/v1/menu", tags=["Menú"])
def obtener_menu():
    """Obtiene la lista de cafés de especialidad disponibles hoy."""
    table = dynamodb.Table(MENU_TABLE)
    try:
        response = table.scan()
        return {"menu": response.get('Items', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/v1/reservas/disponibilidad', tags=['Reservas'])
def obtener_disponibilidad():
    """Devuelve la disponibilidad del contador del día en curso."""
    table = dynamodb.Table(RESERVAS_TABLE)
    hoy = datetime.now(ZONA_HORARIA).date().isoformat()
    try:
        response = table.get_item(
            Key={'id': f'CONTADOR#{hoy}'},
            ConsistentRead=True,
        )
        reservadas = int(response.get('Item', {}).get('tazas_reservadas', 0))
        return {
            'fecha': hoy,
            'tazas_maximas': MAX_TAZAS_DIARIAS,
            'tazas_reservadas': reservadas,
            'tazas_disponibles': max(0, MAX_TAZAS_DIARIAS - reservadas),
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='No se pudo consultar la disponibilidad en este momento.',
        )


@app.post("/api/v1/reservas", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED, tags=["Reservas"])
def crear_reserva(reserva: ReservaRequest):
    """
    Crea una nueva reserva. 
    Regla de negocio: Máximo 2 tazas por persona y límite estricto de 50 tazas diarias totales.
    """
    table = dynamodb.Table(RESERVAS_TABLE)
    hoy = datetime.now(ZONA_HORARIA).date().isoformat()
    ahora = datetime.now(ZONA_HORARIA).isoformat()
    id_reserva = f'RES-{uuid4().hex}'
    id_contador = f'CONTADOR#{hoy}'
    nueva_reserva = {
        'id': {'S': id_reserva},
        'fecha': {'S': hoy},
        'nombre_cliente': {'S': reserva.nombre_cliente.strip()},
        'email': {'S': str(reserva.email)},
        'variedad_cafe': {'S': reserva.variedad_cafe},
        'cantidad_tazas': {'N': str(reserva.cantidad_tazas)},
        'timestamp': {'S': ahora},
    }

    try:
        dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    'Update': {
                        'TableName': RESERVAS_TABLE,
                        'Key': {'id': {'S': id_contador}},
                        'UpdateExpression': 'SET #fecha = :fecha ADD #reservadas :cantidad',
                        'ConditionExpression': (
                            'attribute_not_exists(#reservadas) OR #reservadas <= :max_limit'
                        ),
                        'ExpressionAttributeNames': {
                            '#fecha': 'fecha',
                            '#reservadas': 'tazas_reservadas',
                        },
                        'ExpressionAttributeValues': {
                            ':fecha': {'S': hoy},
                            ':cantidad': {'N': str(reserva.cantidad_tazas)},
                            ':max_limit': {
                                'N': str(MAX_TAZAS_DIARIAS - reserva.cantidad_tazas)
                            },
                        },
                    }
                },
                {
                    'Put': {
                        'TableName': RESERVAS_TABLE,
                        'Item': nueva_reserva,
                    }
                },
            ]
        )
    except ClientError as error:
        error_code = error.response.get('Error', {}).get('Code')
        if error_code == 'TransactionCanceledException':
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='No quedan suficientes tazas disponibles para esa reserva.',
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='No se pudo completar la reserva en este momento.',
        )
    
    return ReservaResponse(
        id_reserva=id_reserva,
        fecha=hoy,
        estado="CONFIRMADA",
        mensaje="Te esperamos en Lago Puelo para tu ritual."
    )

# --- Handler para AWS Lambda ---
# Mangum envuelve la aplicación FastAPI para que pueda ser invocada por AWS API Gateway / Lambda
handler = Mangum(app)