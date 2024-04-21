from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.responses import RedirectResponse
from starlette.testclient import TestClient

from ..inertia import (
    Inertia,
    InertiaResponse, inertia_dependency_factory,
)

from ..config import InertiaConfig


app = FastAPI()
InertiaDep = Annotated[Inertia, Depends(inertia_dependency_factory(InertiaConfig()))]


PROPS = {
    "message": "hello from index",
}

COMPONENT = "IndexPage"


@app.get("/from-url", response_model=None)
async def from_url(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)

@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> RedirectResponse:
    return inertia.back()


@app.post("/", response_model=None)
async def index_post(inertia: InertiaDep) -> RedirectResponse:
    return inertia.back()


def test_redirects_on_get() -> None:
    with TestClient(app) as client:
        from_url = "/from-url"
        response = client.get("/", headers={"Referer": from_url, "X-Inertia": "true"})
        assert response.json() == {
            "component": COMPONENT,
            "props": PROPS,
            "url": f"{client.base_url}{from_url}",
            "version": "1.0",
        }


def test_redirects_on_post() -> None:
    with TestClient(app) as client:
        from_url = "/from-url"
        response = client.post("/", headers={"Referer": from_url, "X-Inertia": "true"})
        assert response.json() == {
            "component": COMPONENT,
            "props": PROPS,
            "url": f"{client.base_url}{from_url}",
            "version": "1.0",
        }
