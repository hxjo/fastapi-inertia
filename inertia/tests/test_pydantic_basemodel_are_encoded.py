from datetime import datetime
from fastapi import FastAPI, Depends
from typing import Annotated, cast
from pydantic import BaseModel

from starlette.testclient import TestClient

from .utils import assert_response_content, templates
from inertia import Inertia, inertia_dependency_factory, InertiaResponse, InertiaConfig


app = FastAPI()

InertiaDep = Annotated[
    Inertia, Depends(inertia_dependency_factory(InertiaConfig(templates=templates)))
]


class Person(BaseModel):
    name: str
    age: int
    created_at: datetime


PROPS = {
    "person": {"name": "John Doe", "age": 42, "created_at": datetime.now()},
}
EXPECTED_PROPS = {
    "person": {
        **PROPS["person"],
        "created_at": cast(datetime, PROPS["person"]["created_at"]).isoformat(),
    }
}

EXPECTED_PROPS_MULTIPLE = {"persons": [EXPECTED_PROPS["person"] for _ in range(2)]}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    name = PROPS["person"]["name"]
    age = PROPS["person"]["age"]
    created_at = PROPS["person"]["created_at"]
    return await inertia.render(
        COMPONENT,
        {
            "person": Person(
                name=cast(str, name),
                age=cast(int, age),
                created_at=cast(datetime, created_at),
            )
        },
    )


@app.get("/multiple", response_model=None)
async def index_multiple(inertia: InertiaDep) -> InertiaResponse:
    name = PROPS["person"]["name"]
    age = PROPS["person"]["age"]
    created_at = PROPS["person"]["created_at"]
    return await inertia.render(
        COMPONENT,
        {
            "persons": [
                Person(
                    name=cast(str, name),
                    age=cast(int, age),
                    created_at=cast(datetime, created_at),
                )
                for _ in range(2)
            ]
        },
    )


def test_pydantic_basemodel_are_encoded_on_json_response() -> None:
    with TestClient(app) as client:
        response = client.get("/", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": EXPECTED_PROPS,
            "url": f"{client.base_url}/",
            "version": "1.0",
        }


def test_pydantic_basemodel_are_encoded_on_html_response() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        expected_url = str(client.base_url) + "/"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS,
            expected_url=expected_url,
        )


def test_pydantic_model_list_are_encoded_on_json_response() -> None:
    with TestClient(app) as client:
        response = client.get("/multiple", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "application/json"
        assert response.json() == {
            "component": COMPONENT,
            "props": EXPECTED_PROPS_MULTIPLE,
            "url": f"{client.base_url}/multiple",
            "version": "1.0",
        }


def test_pydantic_model_list_are_encoded_on_html_response() -> None:
    with TestClient(app) as client:
        response = client.get("/multiple")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        expected_url = str(client.base_url) + "/multiple"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS_MULTIPLE,
            expected_url=expected_url,
        )
