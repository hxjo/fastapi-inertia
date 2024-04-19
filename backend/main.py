import os
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .inertia import (
    InertiaResponse,
    InertiaRenderer,
    inertia_renderer_factory,
    inertia_exception_handler,
    InertiaVersionConflictException,
    InertiaConfig,
    lazy,
)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret_key")
app.add_exception_handler(InertiaVersionConflictException, inertia_exception_handler)


manifest_json = os.path.join(
    os.path.dirname(__file__), "..", "vue", "dist", "client", "manifest.json"
)
inertia_config = InertiaConfig(
    manifest_json_path=manifest_json,
)
InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(inertia_config))
]


vue_dir = (
    os.path.join(os.path.dirname(__file__), "..", "vue", "dist", "client")
    if inertia_config.environment != "development" or inertia_config.ssr_enabled is True
    else os.path.join(os.path.dirname(__file__), "..", "vue", "src")
)

app.mount("/src", StaticFiles(directory=vue_dir), name="src")
app.mount(
    "/assets", StaticFiles(directory=os.path.join(vue_dir, "assets")), name="assets"
)




def some_dependency(inertia: InertiaDep) -> None:
    inertia.share(message="hello from dependency")


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    props = {
        "message": "hello from index",
        "lazy_prop": lazy(lambda: "hello from lazy prop"),
    }
    return await inertia.render("Index", props)


@app.get("/2", response_model=None)
async def index2(inertia: InertiaDep) -> RedirectResponse:
    inertia.flash("hello from index2 (through flash)")
    return RedirectResponse(url="/3")


@app.get("/3", response_model=None, dependencies=[Depends(some_dependency)])
async def index2_with_flashed_data(inertia: InertiaDep) -> InertiaResponse:
    inertia.flash("hello from index3 (through flash)")
    return await inertia.render("Index2")
