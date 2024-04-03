import os
from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles
from .inertia import inertia, settings as inertia_settings, InertiaMiddleware, share

app = FastAPI()

app.add_middleware(InertiaMiddleware)
assets_dir = (
    os.path.join(os.path.dirname(__file__), "..", "vue", "src")
    if inertia_settings.INERTIA_ENV == 'dev'
    else os.path.join(os.path.dirname(__file__), "..", "vue", "dist")
)

app.mount("/src", StaticFiles(directory=assets_dir), name="static")

@app.get("/")
@inertia('Index')
async def index(request: Request):
    share(request, name="John Doe")
    return {"message": "Hello, World!"}

@app.get("/toto")
@inertia('Index2')
async def index2(request: Request):
    share(request, name="John Doe")
    return {"message": "Hello, World 2!"}
