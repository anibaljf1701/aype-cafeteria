import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.slices.catas import router as catas_router
from app.slices.menu import router as menu_router
from app.slices.reservas import router as reservas_router

def create_app() -> FastAPI:
    app = FastAPI(
        title='AyPe Coffee API',
        description='Backend Serverless para gestión de menú y reservas limitadas (Máximo 50 tazas/día).',
        version='1.0.0',
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
        allow_methods=['GET', 'POST', 'OPTIONS'],
        allow_headers=['Content-Type'],
        max_age=600,
    )
    app.include_router(menu_router)
    app.include_router(reservas_router)
    app.include_router(catas_router)
    return app


app = create_app()
handler = Mangum(app)