import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.slices import catas


class FakeTable:
    def get_item(self, **kwargs):
        return {'Item': {'lugares_reservados': 7}}


class FakeClient:
    def __init__(self, error=None):
        self.error = error
        self.transaction = None

    def transact_write_items(self, **kwargs):
        self.transaction = kwargs['TransactItems']
        if self.error:
            raise self.error


class FakeDynamoDB:
    def __init__(self, error=None):
        self.client = FakeClient(error)
        self.meta = SimpleNamespace(client=self.client)

    def Table(self, table_name):
        return FakeTable()


class CatasSliceTests(unittest.TestCase):
    fecha_cata = date(2026, 11, 21)

    def setUp(self):
        self.dynamodb = FakeDynamoDB()
        self.dynamodb_patch = patch.object(catas, 'dynamodb', self.dynamodb)
        self.fechas_patch = patch.object(catas, 'fechas_proximas', return_value=[self.fecha_cata])
        self.dynamodb_patch.start()
        self.fechas_patch.start()
        self.addCleanup(self.dynamodb_patch.stop)
        self.addCleanup(self.fechas_patch.stop)

    def reserva(self):
        return catas.ReservaCataRequest(
            nombre_completo='Ana Pérez',
            email='ANA@example.com',
            fecha=self.fecha_cata,
            cantidad_lugares=2,
        )

    def test_lista_cupos_por_fecha(self):
        resultado = catas.obtener_catas_proximas()

        self.assertEqual(resultado['catas'][0]['fecha'], self.fecha_cata.isoformat())
        self.assertEqual(resultado['catas'][0]['cupos_disponibles'], 3)

    def test_reserva_reclama_email_y_fecha_en_transaccion(self):
        resultado = catas.crear_reserva_cata(self.reserva())
        items = self.dynamodb.client.transaction

        self.assertEqual(resultado.cantidad_lugares, 2)
        self.assertEqual(items[0]['Update']['ExpressionAttributeValues'][':max_limit']['N'], '8')
        self.assertEqual(items[1]['Put']['Item']['id'], {
            'S': f'CATA_EMAIL#{self.fecha_cata.isoformat()}#'
                 f'{catas.hashlib.sha256(b"ana@example.com").hexdigest()}'
        })
        self.assertEqual(items[1]['Put']['ConditionExpression'], 'attribute_not_exists(id)')

    def test_email_duplicado_responde_conflict(self):
        error = ClientError(
            {
                'Error': {'Code': 'TransactionCanceledException'},
                'CancellationReasons': [
                    {'Code': 'None'},
                    {'Code': 'ConditionalCheckFailed'},
                    {'Code': 'None'},
                ],
            },
            'TransactWriteItems',
        )
        self.dynamodb.client.error = error

        with self.assertRaises(HTTPException) as raised:
            catas.crear_reserva_cata(self.reserva())

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn('ya tiene una reserva', raised.exception.detail)


if __name__ == '__main__':
    unittest.main()