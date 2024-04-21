from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from ..inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaResponse,
)

from ..config import InertiaConfig
from ..utils import lazy

app = FastAPI()

InertiaDep = Annotated[Inertia, Depends(inertia_dependency_factory(InertiaConfig()))]

PROPS = {
    "always_str": "hello from str",
    "always_func": lambda: "hello from func",
    "lazy": lazy(lambda: "hello from lazy"),
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_first_request_do_not_include_lazy() -> None:
    with TestClient(app) as client:
        response = client.get("/", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "always_str": "hello from str",
                "always_func": "hello from func",
            },
            "url": f"{client.base_url}/",
            "version": "1.0",
        }


def test_partial_reload_include_lazy() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/",
            headers={
                "X-Inertia": "true",
                "X-Inertia-Partial-Data": "lazy",
                "X-Inertia-Partial-Component": COMPONENT,
            },
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "lazy": "hello from lazy",
            },
            "url": f"{client.base_url}/",
            "version": "1.0",
        }
