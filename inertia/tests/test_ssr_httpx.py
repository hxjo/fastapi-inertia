from typing import TypedDict
import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, Depends
from typing import Annotated, cast

import httpx
from starlette.testclient import TestClient

from inertia import Inertia, inertia_dependency_factory, InertiaResponse, InertiaConfig
from inertia.inertia import get_httpx_client

from .utils import assert_response_content, templates


app = FastAPI()
manifest_json = os.path.join(os.path.dirname(__file__), "dummy_manifest_js.json")


SSR_URL = "http://some_special_url"
InertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                ssr_enabled=True,
                environment="production",
                manifest_json_path=manifest_json,
                ssr_url=SSR_URL,
                templates=templates,
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


class ReturnedJson(TypedDict):
    head: list[str]
    body: str


RETURNED_JSON: ReturnedJson = {
    "head": ['<link ref="stylesheet" href="some-magical-url.com">'],
    "body": "<div>some body content</div>",
}


async def test_returns_html() -> None:
    async def get_httpx_client_mock() -> AsyncMock:
        mock = AsyncMock()
        mocked_response = MagicMock()
        mocked_response.json.return_value = RETURNED_JSON
        mock.post.return_value = mocked_response
        return mock

    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        httpx_mock = await get_httpx_client_mock()
        app.dependency_overrides[get_httpx_client] = lambda: httpx_mock
        response = client.get("/")
        httpx_mock.post.assert_called_once_with(
            url=f"{SSR_URL}/render",
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


async def test_fallback_to_classic_if_render_errors() -> None:
    async def get_httpx_client_mock() -> AsyncMock:
        mock = AsyncMock()
        mock.post.return_value = httpx.Response(status_code=500)
        return mock

    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        httpx_mock = await get_httpx_client_mock()
        app.dependency_overrides[get_httpx_client] = lambda: httpx_mock
        response = client.get("/")
        httpx_mock.post.assert_called_once_with(
            url=f"{SSR_URL}/render",
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
