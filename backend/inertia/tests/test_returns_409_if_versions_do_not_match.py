from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from ..inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaConfig,
    InertiaResponse,
)
from ..exceptions import InertiaVersionConflictException, inertia_exception_handler


app = FastAPI()
app.add_exception_handler(InertiaVersionConflictException, inertia_exception_handler)  # type: ignore[arg-type]

InertiaDep = Annotated[Inertia, Depends(inertia_dependency_factory(InertiaConfig()))]

PROPS = {
    "message": "hello from index",
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_returns_409_if_versions_do_not_match() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/", headers={"X-Inertia-Version": str(float(InertiaConfig.version) + 1)}
        )
        assert response.status_code == 409
        assert response.headers.get("X-Inertia-Location") == f"{client.base_url}/"
