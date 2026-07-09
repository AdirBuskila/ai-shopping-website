from fastapi import FastAPI

from app.controllers import auth, favorites, health, products


def create_app() -> FastAPI:
    app = FastAPI(title="AI Shopping API", version="0.1.0")
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(products.router)
    app.include_router(favorites.router)
    return app


app = create_app()
