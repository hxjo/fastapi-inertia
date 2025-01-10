from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from inertia import Inertia, inertia_dependency_factory, InertiaResponse, InertiaConfig

from .utils import assert_response_content, templates

app = FastAPI()

InertiaDep = Annotated[
    Inertia, Depends(inertia_dependency_factory(InertiaConfig(templates=templates)))
]

PROPS = {
    "normal": "Quick fox jumped over lazy dog",
    "apostrophe": "Q'uick fox jump'ed o'ver lazy dog",
}

EXPECTED_PROPS = {**PROPS}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_first_request_returns_html() -> None:
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
