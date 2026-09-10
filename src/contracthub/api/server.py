"""FastAPI Application Entrypoint for ContractHub."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

from contracthub.api.confluent_routes import router as confluent_router
from contracthub.api.native_routes import router as native_router
from contracthub.storage.database import init_db
from contracthub.web.studio import get_studio_html


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize storage tables on startup
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ContractHub",
        description="Universal Schema Registry and Breaking Change Linter",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount Native API
    app.include_router(native_router)

    # Mount Confluent Wire Protocol Compatibility Layer
    app.include_router(confluent_router)

    # Embedded Web Studio
    @app.get("/studio", response_class=HTMLResponse, tags=["Studio"])
    def studio_view():
        return HTMLResponse(content=get_studio_html())

    @app.get("/", include_in_schema=False)
    def root_redirect():
        return RedirectResponse(url="/studio")

    return app


app = create_app()
