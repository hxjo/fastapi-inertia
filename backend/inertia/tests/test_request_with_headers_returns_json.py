from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from ..inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaResponse,
)

from ..config import InertiaConfig

app = FastAPI()

InertiaDep = Annotated[Inertia, Depends(inertia_dependency_factory(InertiaConfig()))]

PROPS = {
    "message": "hello from index",
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_request_with_headers_returns_json() -> None:
    with TestClient(app) as client:
        response = client.get("/", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": PROPS,
            "url": f"{client.base_url}/",
            "version": "1.0",
        }
