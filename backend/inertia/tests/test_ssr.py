import json
import os
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from ..inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaConfig,
    InertiaResponse,
)
from .utils import get_stripped_html

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
PROPS = {
    "message": "hello from index",
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
                "props": PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )


RETURNED_JSON = {"head": ["some info in the head"], "body": "some info in the body"}


@patch("requests.post", return_value=MagicMock(json=lambda: RETURNED_JSON))
def test_returns_html(post_function: MagicMock) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_file = f"/src/{manifest["src/main.js"]["css"][0]}"
    js_file = f"/{manifest["src/main.js"]["file"]}"
    with TestClient(app) as client:
        response = client.get("/")
        post_function.assert_called_once_with(
            f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        assert response.text.strip() == get_stripped_html(
            component_name=COMPONENT,
            props=PROPS,
            url=f"{client.base_url}/",
            script_asset_url=js_file,
            css_asset_url=css_file,
            body_content=RETURNED_JSON["body"],
            additional_head_content="\n".join(RETURNED_JSON["head"]),
        )


@patch("requests.post", side_effect=Exception())
def test_fallback_to_classic_if_render_errors(post_function: MagicMock) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_file = f"/src/{manifest["src/main.js"]["css"][0]}"
    js_file = f"/{manifest["src/main.js"]["file"]}"
    with TestClient(app) as client:
        response = client.get("/")
        post_function.assert_called_once_with(
            f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        assert response.text.strip() == get_stripped_html(
            component_name=COMPONENT,
            props=PROPS,
            url=f"{client.base_url}/",
            script_asset_url=js_file,
            css_asset_url=css_file,
        )
