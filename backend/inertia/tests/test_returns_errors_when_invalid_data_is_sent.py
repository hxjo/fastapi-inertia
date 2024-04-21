from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from typing import Annotated
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from starlette.testclient import TestClient

from inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaResponse,
    InertiaConfig,
    InertiaVersionConflictException,
    inertia_version_conflict_exception_handler,
    inertia_request_validation_exception_handler,
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

InertiaDep = Annotated[
    Inertia, Depends(inertia_dependency_factory(InertiaConfig(use_flash_messages=True)))
]


COMPONENT = "IndexPage"


class ExpectedPayload(BaseModel):
    message: str


@app.post("/", response_model=None)
async def index_post(
    payload: ExpectedPayload, *, inertia: InertiaDep
) -> InertiaResponse:
    return await inertia.render(COMPONENT)


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT)


@app.get("/{pk}", response_model=None)
async def index_id(pk: int, inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT)


def test_redirects_back_with_errors_on_inertia_request() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/", headers={"X-Inertia": "true", "Referer": "/"}, json={"message": 12}
        )
        assert response.status_code == 200
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "messages": [],
                "errors": {"message": "Input should be a valid string"},
            },
            "url": f"{client.base_url}/",
            "version": "1.0",
        }


def test_redirects_back_with_errors_on_inertia_request_error_in_url() -> None:
    with TestClient(app) as client:
        response = client.get("/fizz", headers={"X-Inertia": "true", "Referer": "/"})
        assert response.status_code == 200
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "messages": [],
                "errors": {
                    "pk": "Input should be a valid integer, unable to parse string as an integer"
                },
            },
            "url": f"{client.base_url}/",
            "version": "1.0",
        }


def test_redirects_back_with_errors_in_error_bag_on_inertia_request() -> None:
    error_bag = "some_error_bag"
    with TestClient(app) as client:
        response = client.post(
            "/",
            headers={
                "X-Inertia": "true",
                "Referer": "/",
                "X-Inertia-Error-Bag": error_bag,
            },
            json={"message": 12},
        )
        assert response.status_code == 200
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "messages": [],
                "errors": {
                    error_bag: {"message": "Input should be a valid string"},
                },
            },
            "url": f"{client.base_url}/",
            "version": "1.0",
        }


def test_throws_422_on_non_inertia_request() -> None:
    with TestClient(app) as client:
        response = client.post("/", json={"message": 12})
        assert response.status_code == 422
