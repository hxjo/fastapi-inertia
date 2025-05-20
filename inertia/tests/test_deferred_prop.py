from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaResponse,
    InertiaConfig,
    defer,
)
from .utils import templates


app = FastAPI()

InertiaDep = Annotated[
    Inertia, Depends(inertia_dependency_factory(InertiaConfig(templates=templates)))
]


PROPS = {
    "always_str": "hello from str",
    "users": defer(lambda: {"user1": "John Doe", "user2": "Jane Doe"}),
    "permissions": defer(lambda: ["read", "write", "delete"]),
}

PROPS_WITH_GROUPS = {
    "always_str": "hello from str",
    "users": defer(
        lambda: {"user1": "John Doe", "user2": "Jane Doe"}, group="user_group"
    ),
    "permissions": defer(lambda: ["read", "write", "delete"], group="permission_group"),
}

COMPONENT = "IndexPage"


@app.get("/without-groups", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@app.get("/with-groups", response_model=None)
async def index_with_groups(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS_WITH_GROUPS)


def test_first_request_returns_props_keys_to_defer_with_default_group() -> None:
    with TestClient(app) as client:
        response = client.get("/without-groups", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "always_str": "hello from str",
            },
            "deferredProps": {"default": ["users", "permissions"]},
            "url": f"{client.base_url}/without-groups",
            "version": "1.0",
        }


def test_first_request_returns_props_keys_to_defer_with_defined_groups() -> None:
    with TestClient(app) as client:
        response = client.get("/with-groups", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "always_str": "hello from str",
            },
            "deferredProps": {
                "user_group": ["users"],
                "permission_group": ["permissions"],
            },
            "url": f"{client.base_url}/with-groups",
            "version": "1.0",
        }


def test_subsequent_requests_include_users_deferred_props() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/with-groups",
            headers={
                "X-Inertia": "true",
                "X-Inertia-Partial-Data": "users",
                "X-Inertia-Partial-Component": COMPONENT,
            },
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "users": {"user1": "John Doe", "user2": "Jane Doe"},
            },
            "url": f"{client.base_url}/with-groups",
            "version": "1.0",
        }


def test_subsequent_requests_include_permissions_deferred_props() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/with-groups",
            headers={
                "X-Inertia": "true",
                "X-Inertia-Partial-Data": "permissions",
                "X-Inertia-Partial-Component": COMPONENT,
            },
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": {
                "permissions": ["read", "write", "delete"],
            },
            "url": f"{client.base_url}/with-groups",
            "version": "1.0",
        }
