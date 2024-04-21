import os
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from inertia import (
    InertiaResponse,
    Inertia,
    inertia_dependency_factory,
    inertia_version_conflict_exception_handler,
    inertia_request_validation_exception_handler,
    InertiaVersionConflictException,
    InertiaConfig,
    lazy,
)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret_key")
app.add_exception_handler(
    InertiaVersionConflictException,
    inertia_version_conflict_exception_handler,  # type: ignore[arg-type]
)
app.add_exception_handler(
    RequestValidationError,
    inertia_request_validation_exception_handler,  # type: ignore[arg-type]
)


manifest_json = os.path.join(
    os.path.dirname(__file__), "..", "vue", "dist", "client", "manifest.json"
)
inertia_config = InertiaConfig(
    manifest_json_path=manifest_json,
    environment="development",
    use_flash_messages=True,
    ssr_enabled=False,
)
InertiaDep = Annotated[Inertia, Depends(inertia_dependency_factory(inertia_config))]


vue_dir = (
    os.path.join(os.path.dirname(__file__), "..", "vue", "dist", "client")
    if inertia_config.environment != "development"
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
    return await inertia.render("IndexPage", props)


@app.get("/2", response_model=None)
async def other_page(inertia: InertiaDep) -> RedirectResponse:
    inertia.flash("hello from index2 (through flash)", category="message")
    return RedirectResponse(url="/3")


@app.get("/3", response_model=None, dependencies=[Depends(some_dependency)])
async def other_page_with_flashed_data(inertia: InertiaDep) -> InertiaResponse:
    inertia.flash("hello from index3 (through flash)", category="message")
    return await inertia.render("OtherPage")


@app.post("/some-form", response_model=None)
async def some_form(inertia: InertiaDep) -> RedirectResponse:
    return inertia.back()
