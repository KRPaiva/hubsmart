from fastapi import FastAPI

from app.routers import health, web


def create_app() -> FastAPI:
    app = FastAPI(title="HubSmart Brainstorm", docs_url="/docs", redoc_url=None)
    app.include_router(health.router)
    app.include_router(web.router)
    return app


app = create_app()
