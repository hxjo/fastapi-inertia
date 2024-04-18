import os
from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles
from .inertia import inertia, settings as inertia_settings, InertiaMiddleware, share

app = FastAPI()

app.add_middleware(InertiaMiddleware)
vue_dir = (
    os.path.join(os.path.dirname(__file__), "..", "vue", "dist", "client")
    if inertia_settings.INERTIA_ENV != "dev" or inertia_settings.INERTIA_SSR_ENABLED is True
    else
    os.path.join(os.path.dirname(__file__), "..", "vue", "src")
)

app.mount("/src", StaticFiles(directory=vue_dir), name="static")
app.mount("/assets", StaticFiles(directory=os.path.join(vue_dir, 'assets')), name="static")


@app.get("/")
@inertia("Index")
async def index(request: Request) -> dict[str, str]:
    share(request, name="John Doe")
    return {"message": "Hello, World!"}


@app.get("/toto")
@inertia("Index2")
async def index2(request: Request) -> dict[str, str]:
    share(request, name="John Doe")
    return {"message": "Hello, World 2!"}
