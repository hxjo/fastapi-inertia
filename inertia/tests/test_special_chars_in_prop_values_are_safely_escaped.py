import re
from fastapi import FastAPI, Depends
from typing import Annotated
from starlette.testclient import TestClient

from inertia import Inertia, inertia_dependency_factory, InertiaResponse, InertiaConfig

from .utils import assert_response_content, templates

app = FastAPI()

InertiaDep = Annotated[
    Inertia, Depends(inertia_dependency_factory(InertiaConfig(templates=templates)))
]

# Include a property with special characters.
PROPS = {
    "special": "<>&'"
}

EXPECTED_PROPS = {**PROPS}
COMPONENT = "IndexPage"

@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)

def test_special_chars_are_escaped() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"

        html_output = response.text

        match = re.search(r'<div\s+id=["\']app["\'][^>]*\sdata-page=(["\'])(.*?)\1', html_output)
        assert match, "Could not find the div with id 'app' and a data-page attribute."
        data_page_value = match.group(2)

        assert "<" not in data_page_value, "Expected '<' to be escaped as \\u003c in data-page."
        assert ">" not in data_page_value, "Expected '>' to be escaped as \\u003e in data-page."
        assert "&" not in data_page_value, "Expected '&' to be escaped as \\u0026 in data-page."
        assert "'" not in data_page_value, "Expected '<' to be escaped as \\u0027 in data-page."

        expected_url = str(client.base_url) + "/"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS,
            expected_url=expected_url,
        )
