import hashlib
import os
from datetime import date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator


router = APIRouter(prefix='/api/v1/catas', tags=['Catas'])
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table_name = os.getenv('RESERVAS_TABLE_NAME', 'aype-reservas')
cupo_total = int(os.getenv('CATA_CUPO_TOTAL', '10'))
dia_semanal = int(os.getenv('CATA_DIA_SEMANAL', '5'))
semanas_proximas = int(os.getenv('CATA_SEMANAS_PROXIMAS', '8'))
zona_horaria = ZoneInfo('America/Argentina/Buenos_Aires')


class ReservaCataRequest(BaseModel):
    nombre_completo: str = Field(min_length=1, max_length=100)
    email: EmailStr
    fecha: date
    cantidad_lugares: int = Field(ge=1, le=2)

    @field_validator('nombre_completo')
    @classmethod
    def nombre_no_vacio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('El nombre completo es obligatorio.')
        return value


class ReservaCataResponse(BaseModel):
    id_reserva: str
    fecha: date
    cantidad_lugares: int
    estado: str
    mensaje: str


def fechas_proximas() -> list[date]:
    hoy = datetime.now(zona_horaria).date()
    dias_hasta_cata = (dia_semanal - hoy.weekday()) % 7
    primera_fecha = hoy + timedelta(days=dias_hasta_cata)
    return [primera_fecha + timedelta(weeks=semana) for semana in range(semanas_proximas)]


@router.get('/proximas')
def obtener_catas_proximas():
    table = dynamodb.Table(table_name)
    catas = []
    try:
        for fecha_cata in fechas_proximas():
            response = table.get_item(
                Key={'id': f'CATA#{fecha_cata.isoformat()}'},
                ConsistentRead=True,
            )
            reservados = int(response.get('Item', {}).get('lugares_reservados', 0))
            catas.append({
                'fecha': fecha_cata.isoformat(),
                'cupo_total': cupo_total,
                'lugares_reservados': reservados,
                'cupos_disponibles': max(0, cupo_total - reservados),
            })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='No se pudo consultar la disponibilidad de las catas.',
        )
    return {'catas': catas}


@router.post('/reservas', response_model=ReservaCataResponse, status_code=status.HTTP_201_CREATED)
def crear_reserva_cata(reserva: ReservaCataRequest):
    fecha_cata = reserva.fecha.isoformat()
    if reserva.fecha not in fechas_proximas():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='La fecha seleccionada no corresponde a una cata disponible.',
        )

    email_normalizado = str(reserva.email).strip().casefold()
    email_hash = hashlib.sha256(email_normalizado.encode('utf-8')).hexdigest()
    id_reserva = f'CATA-RES-{uuid4().hex}'
    ahora = datetime.now(zona_horaria).isoformat()
    client = dynamodb.meta.client

    try:
        client.transact_write_items(
            TransactItems=[
                {
                    'Update': {
                        'TableName': table_name,
                        'Key': {'id': {'S': f'CATA#{fecha_cata}'}},
                        'UpdateExpression': 'SET #fecha = :fecha ADD #reservados :cantidad',
                        'ConditionExpression': (
                            'attribute_not_exists(#reservados) OR #reservados <= :max_limit'
                        ),
                        'ExpressionAttributeNames': {
                            '#fecha': 'fecha',
                            '#reservados': 'lugares_reservados',
                        },
                        'ExpressionAttributeValues': {
                            ':fecha': {'S': fecha_cata},
                            ':cantidad': {'N': str(reserva.cantidad_lugares)},
                            ':max_limit': {'N': str(cupo_total - reserva.cantidad_lugares)},
                        },
                    }
                },
                {
                    'Put': {
                        'TableName': table_name,
                        'Item': {
                            'id': {'S': f'CATA_EMAIL#{fecha_cata}#{email_hash}'},
                            'fecha': {'S': fecha_cata},
                            'email_hash': {'S': email_hash},
                            'id_reserva': {'S': id_reserva},
                        },
                        'ConditionExpression': 'attribute_not_exists(id)',
                    }
                },
                {
                    'Put': {
                        'TableName': table_name,
                        'Item': {
                            'id': {'S': id_reserva},
                            'tipo': {'S': 'RESERVA_CATA'},
                            'fecha': {'S': fecha_cata},
                            'nombre_completo': {'S': reserva.nombre_completo},
                            'email': {'S': email_normalizado},
                            'cantidad_lugares': {'N': str(reserva.cantidad_lugares)},
                            'timestamp': {'S': ahora},
                        },
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
                    detail='Este email ya tiene una reserva para esa fecha.',
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='No quedan suficientes lugares disponibles para esa cata.',
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='No se pudo completar la reserva de cata en este momento.',
        )

    return ReservaCataResponse(
        id_reserva=id_reserva,
        fecha=reserva.fecha,
        cantidad_lugares=reserva.cantidad_lugares,
        estado='CONFIRMADA',
        mensaje='Tu lugar para la cata está confirmado. ¡Te esperamos!',
    )