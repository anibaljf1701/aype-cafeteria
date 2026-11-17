import hashlib
import os
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field


router = APIRouter(prefix='/api/v1/reservas', tags=['Reservas'])
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
reservas_table_name = os.getenv('RESERVAS_TABLE_NAME', 'aype-reservas')
max_tazas_diarias = 50
zona_horaria = ZoneInfo('America/Argentina/Buenos_Aires')


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


@router.get('/disponibilidad')
def obtener_disponibilidad():
    """Devuelve la disponibilidad del contador del día en curso."""
    table = dynamodb.Table(reservas_table_name)
    hoy = datetime.now(zona_horaria).date().isoformat()
    try:
        response = table.get_item(
            Key={'id': f'CONTADOR#{hoy}'},
            ConsistentRead=True,
        )
        reservadas = int(response.get('Item', {}).get('tazas_reservadas', 0))
        return {
            'fecha': hoy,
            'tazas_maximas': max_tazas_diarias,
            'tazas_reservadas': reservadas,
            'tazas_disponibles': max(0, max_tazas_diarias - reservadas),
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='No se pudo consultar la disponibilidad en este momento.',
        )


@router.post('', response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
def crear_reserva(reserva: ReservaRequest):
    """Crea una reserva respetando el límite diario y el máximo personal."""
    hoy = datetime.now(zona_horaria).date().isoformat()
    ahora = datetime.now(zona_horaria).isoformat()
    id_reserva = f'RES-{uuid4().hex}'
    id_contador = f'CONTADOR#{hoy}'
    email_normalizado = str(reserva.email).strip().casefold()
    email_hash = hashlib.sha256(email_normalizado.encode('utf-8')).hexdigest()
    id_persona = f'PERSONA#{hoy}#{email_hash}'
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
                        'TableName': reservas_table_name,
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
                                'N': str(max_tazas_diarias - reserva.cantidad_tazas)
                            },
                        },
                    }
                },
                {
                    'Update': {
                        'TableName': reservas_table_name,
                        'Key': {'id': {'S': id_persona}},
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
                                'N': str(2 - reserva.cantidad_tazas)
                            },
                        },
                    }
                },
                {
                    'Put': {
                        'TableName': reservas_table_name,
                        'Item': nueva_reserva,
                    }
                },
            ]
        )
    except ClientError as error:
        error_code = error.response.get('Error', {}).get('Code')
        if error_code == 'TransactionCanceledException':
            cancellation_reasons = error.response.get('CancellationReasons', [])
            if len(cancellation_reasons) > 1 and cancellation_reasons[1].get('Code') == 'ConditionalCheckFailed':
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='El límite es de 2 tazas por email por día.',
                )
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
        estado='CONFIRMADA',
        mensaje='Te esperamos en Lago Puelo para tu ritual.',
    )