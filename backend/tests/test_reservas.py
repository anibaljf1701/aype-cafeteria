import unittest
from types import SimpleNamespace
from unittest.mock import patch

from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.slices import reservas


class FakeClient:
    def __init__(self, error=None):
        self.error = error
        self.transactions = []

    def transact_write_items(self, **kwargs):
        self.transactions.append(kwargs['TransactItems'])
        if self.error:
            raise self.error


class FakeDynamoDB:
    def __init__(self, client):
        self.meta = SimpleNamespace(client=client)

    def Table(self, table_name):
        return object()


class ReservasAtomicasTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.dynamodb_patch = patch.object(reservas, 'dynamodb', FakeDynamoDB(self.client))
        self.dynamodb_patch.start()
        self.addCleanup(self.dynamodb_patch.stop)

    def reserva(self):
        return reservas.ReservaRequest(
            nombre_cliente='Ana Pérez',
            email='ana@example.com',
            variedad_cafe='Ayme',
            cantidad_tazas=2,
        )

    def test_limites_diario_y_personal_se_validan_en_una_transaccion(self):
        reservas.crear_reserva(self.reserva())

        self.assertEqual(len(self.client.transactions), 1)
        items = self.client.transactions[0]
        self.assertEqual(len(items), 3)

        contador_diario = items[0]['Update']
        self.assertIn('ADD #reservadas :cantidad', contador_diario['UpdateExpression'])
        self.assertIn('#reservadas <= :max_limit', contador_diario['ConditionExpression'])
        self.assertEqual(
            contador_diario['ExpressionAttributeValues'][':max_limit']['N'],
            str(reservas.max_tazas_diarias - 2),
        )

        contador_personal = items[1]['Update']
        self.assertIn('#reservadas <= :max_limit', contador_personal['ConditionExpression'])
        self.assertEqual(
            contador_personal['ExpressionAttributeValues'][':max_limit']['N'],
            '0',
        )
        self.assertIn('Put', items[2])

    def test_fallo_del_limite_diario_rechaza_la_reserva(self):
        self.client.error = ClientError(
            {
                'Error': {'Code': 'TransactionCanceledException'},
                'CancellationReasons': [
                    {'Code': 'ConditionalCheckFailed'},
                    {'Code': 'None'},
                    {'Code': 'None'},
                ],
            },
            'TransactWriteItems',
        )

        with self.assertRaises(HTTPException) as raised:
            reservas.crear_reserva(self.reserva())

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn('suficientes tazas', raised.exception.detail)


if __name__ == '__main__':
    unittest.main()
