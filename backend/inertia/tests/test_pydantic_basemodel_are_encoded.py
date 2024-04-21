from fastapi import FastAPI, Depends
from typing import Annotated, cast
from pydantic import BaseModel

from starlette.testclient import TestClient

from .utils import get_stripped_html
from ..inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaResponse,
)

from ..config import InertiaConfig

app = FastAPI()

InertiaDep = Annotated[Inertia, Depends(inertia_dependency_factory(InertiaConfig()))]

class Person(BaseModel):
    name: str
    age: int

PROPS = {
    "person": {
        "name": "John Doe",
        "age": 42,
    },
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    name = PROPS["person"]["name"]
    age = PROPS["person"]["age"]
    return await inertia.render(COMPONENT, {"person": Person(name=cast(str, name), age=cast(int, age))})


def test_pydantic_basemodel_are_encoded_on_json_response() -> None:
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

def test_pydantic_basemodel_are_encoded_on_html_response() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        expected_url = str(client.base_url) + "/"
        assert response.text.strip() == get_stripped_html(
            component_name=COMPONENT, props=PROPS, url=expected_url
        )
