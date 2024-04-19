import os
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .inertia import (
    InertiaVersionConflict,
    InertiaRenderer,
    InertiaConfig,
    inertia_renderer_factory,
)
from .inertia.renderer import InertiaResponse
from .inertia.exceptions import inertia_exception_handler

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret_key")


manifest_json = os.path.join(
    os.path.dirname(__file__), "..", "vue", "dist", "client", "manifest.json"
)
inertia_config = InertiaConfig(
    MANIFEST_JSON_PATH=manifest_json,
)
InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(inertia_config))
]


vue_dir = (
    os.path.join(os.path.dirname(__file__), "..", "vue", "dist", "client")
    if inertia_config.ENV != "development" or inertia_config.SSR_ENABLED is True
    else os.path.join(os.path.dirname(__file__), "..", "vue", "src")
)

app.mount("/src", StaticFiles(directory=vue_dir), name="src")
app.mount(
    "/assets", StaticFiles(directory=os.path.join(vue_dir, "assets")), name="assets"
)


app.add_exception_handler(InertiaVersionConflict, inertia_exception_handler)


def some_dependency(inertia: InertiaDep) -> None:
    inertia.share(message="hello from dependency")


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render("Index", {"message": "hello from index"})


@app.get("/2", response_model=None, dependencies=[Depends(some_dependency)])
async def index2(inertia: InertiaDep) -> RedirectResponse:
    inertia.flash("hello from index2")
    return RedirectResponse(url="/3")


@app.get("/3", response_model=None, dependencies=[Depends(some_dependency)])
async def index2_with_flashed_data(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render("Index2")
