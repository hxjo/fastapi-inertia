from typing import TypedDict
import json
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Depends
from typing import Annotated, cast

from starlette.testclient import TestClient

from inertia import Inertia, inertia_dependency_factory, InertiaResponse, InertiaConfig

from .utils import assert_response_content

app = FastAPI()
manifest_json = os.path.join(os.path.dirname(__file__), "dummy_manifest_js.json")

SSR_URL = "http://some_special_url"
InertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                ssr_enabled=True, manifest_json_path=manifest_json, ssr_url=SSR_URL
            )
        )
    ),
]
PROPS = {"message": "hello from index", "created_at": datetime.now()}

EXPECTED_PROPS = {
    **PROPS,
    "created_at": cast(datetime, PROPS["created_at"]).isoformat(),
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@patch("requests.post")
def test_calls_inertia_render(post_function: MagicMock) -> None:
    with TestClient(app) as client:
        client.get("/")
        post_function.assert_called_once_with(
            f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": EXPECTED_PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )


class ReturnedJson(TypedDict):
    head: list[str]
    body: str


RETURNED_JSON: ReturnedJson = {
    "head": ['<link ref="stylesheet" href="some-magical-url.com">'],
    "body": "<div>some body content</div>",
}


@patch("requests.post", return_value=MagicMock(json=lambda: RETURNED_JSON))
def test_returns_html(post_function: MagicMock) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        response = client.get("/")
        post_function.assert_called_once_with(
            f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": EXPECTED_PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        assert_response_content(
            response,
            expected_script_asset_url=js_file,
            expected_css_asset_urls=css_files,
            expected_additional_head_content=RETURNED_JSON["head"],
            expected_body_content=RETURNED_JSON["body"],
        )


@patch("requests.post", side_effect=Exception())
def test_fallback_to_classic_if_render_errors(post_function: MagicMock) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        response = client.get("/")
        post_function.assert_called_once_with(
            f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": EXPECTED_PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS,
            expected_url=f"{client.base_url}/",
            expected_script_asset_url=js_file,
            expected_css_asset_urls=css_files,
        )
