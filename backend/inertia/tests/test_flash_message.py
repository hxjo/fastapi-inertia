import pytest
from fastapi import FastAPI, Depends
from typing import Annotated, cast

from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

from ..inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaResponse,
)

from ..config import InertiaConfig

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="secret_key")

FLASH_MESSAGE_KEY = "some_special_key"

InertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(use_flash_messages=True, flash_message_key=FLASH_MESSAGE_KEY)
        )
    ),
]
InvalidInertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(InertiaConfig(flash_message_key=FLASH_MESSAGE_KEY))
    ),
]


PROPS = {
    "message": "hello from index",
    FLASH_MESSAGE_KEY: [{"message": "hello from flash message", "category": "info"}],
}

COMPONENT = "IndexPage"


def dependency(inertia: InertiaDep) -> None:
    messages = cast(list[dict[str, str]], PROPS.get(FLASH_MESSAGE_KEY))
    inertia.flash(**messages[0])


@app.get("/", response_model=None, dependencies=[Depends(dependency)])
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(
        COMPONENT,
        {
            "message": PROPS.get("message"),
        },
    )


@app.get("/redirect", response_model=None, dependencies=[Depends(dependency)])
async def redirect_page(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(
        COMPONENT,
        {
            "message": PROPS.get("message"),
        },
    )


@app.get("/other-page", response_model=None)
async def other_page(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(
        COMPONENT,
        {
            "message": PROPS.get("message"),
        },
    )


@app.get("/invalid", response_model=None)
async def invalid_inertia_page(inertia: InvalidInertiaDep) -> None:
    inertia.flash(message="hello from flash message", category="info")


def test_flash_message_is_included_from_dependency() -> None:
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


def test_flash_message_is_not_included_on_second_request() -> None:
    with TestClient(app) as client:
        client.get("/", headers={"X-Inertia": "true"})
        response = client.get("/other-page", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "message": PROPS.get("message"),
                FLASH_MESSAGE_KEY: [],
            },
            "url": f"{client.base_url}/other-page",
            "version": "1.0",
        }


def test_flash_message_is_persisted_on_redirect() -> None:
    with TestClient(app) as client:
        headers = {"X-Inertia": "true"}
        response = client.get("/redirect", headers=headers)

        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": PROPS,
            "url": f"{client.base_url}/redirect",
            "version": "1.0",
        }


def test_invalid_inertia_dependency_raises() -> None:
    with TestClient(app) as client:
        with pytest.raises(NotImplementedError):
            client.get("/invalid", headers={"X-Inertia": "true"})
