import unittest

from app.main import create_app


class AppFactoryTests(unittest.TestCase):
    def test_create_app_registra_rutas_de_todos_los_slices(self):
        app = create_app()
        paths = {route.path for route in app.routes}

        self.assertTrue({
            '/api/v1/menu',
            '/api/v1/reservas',
            '/api/v1/reservas/disponibilidad',
            '/api/v1/catas/proximas',
            '/api/v1/catas/reservas',
        }.issubset(paths))


if __name__ == '__main__':
    unittest.main()