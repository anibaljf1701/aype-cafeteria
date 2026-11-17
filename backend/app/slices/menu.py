import os

import boto3
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix='/api/v1/menu', tags=['Menú'])
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
menu_table_name = os.getenv('MENU_TABLE_NAME', 'aype-menu')


@router.get('')
def obtener_menu():
    """Obtiene la lista de cafés de especialidad disponibles hoy."""
    table = dynamodb.Table(menu_table_name)
    try:
        response = table.scan()
        return {'menu': response.get('Items', [])}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))