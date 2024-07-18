from importlib import reload
import sys
from typing import Any, Generator, TypedDict
import json
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
from typing import Annotated, cast
import warnings

from fastapi import FastAPI, Depends

import pytest
from starlette.testclient import TestClient


from inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaResponse,
    InertiaConfig,
)

from ..utils import assert_response_content

manifest_json = os.path.join(os.path.dirname(__file__), "..", "dummy_manifest_js.json")

SSR_URL = "http://some_special_url"

PROPS = {"message": "hello from index", "created_at": datetime.now()}

EXPECTED_PROPS = {
    **PROPS,
    "created_at": cast(datetime, PROPS["created_at"]).isoformat(),
}

COMPONENT = "IndexPage"


class ModuleNotFoundRaiser:
    def find_spec(self, fullname: str, *args: Any, **kwargs: Any) -> None:
        if fullname == "httpx":
            raise ModuleNotFoundError()


@pytest.fixture()
def fail_httpx_import_module_not_found() -> Generator[None, None, None]:
    import_raiser = ModuleNotFoundRaiser()
    sys.meta_path.insert(0, import_raiser)
    original_httpx = None
    if "httpx" in sys.modules:
        original_httpx = sys.modules["httpx"]
        del sys.modules["httpx"]

    reload(sys.modules["inertia.inertia"])

    yield

    # Reset sys.meta_path and sys.modules after the test
    # sys.meta_path.remove(import_raiser)
    if "httpx" not in sys.modules and original_httpx is not None:
        sys.modules["httpx"] = original_httpx


class ImportRaiser:
    def find_spec(self, fullname: str, *args: Any, **kwargs: Any) -> None:
        if fullname == "httpx":
            warnings.warn("raising import error")
            raise ImportError()


@pytest.fixture()
def fail_httpx_import() -> Generator[None, None, None]:
    import_raiser = ImportRaiser()
    sys.meta_path.insert(0, import_raiser)
    original_httpx = None
    if "httpx" in sys.modules:
        original_httpx = sys.modules["httpx"]
        del sys.modules["httpx"]

    reload(sys.modules["inertia.inertia"])

    yield

    # Reset sys.meta_path and sys.modules after the test
    # sys.meta_path.remove(import_raiser)
    if "httpx" not in sys.modules and original_httpx is not None:
        sys.modules["httpx"] = original_httpx


InertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                ssr_enabled=True,
                manifest_json_path=manifest_json,
                ssr_url=SSR_URL,
            )
        )
    ),
]
app = FastAPI()


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


@patch("requests.post")
def test_calls_inertia_render_module_not_found(
    post_function: MagicMock, fail_httpx_import_module_not_found: None
) -> None:
    with TestClient(app) as client:
        with pytest.deprecated_call():
            client.get("/")
        post_function.assert_called_once_with(
            url=f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": EXPECTED_PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )


@patch("requests.post", return_value=MagicMock(json=lambda: RETURNED_JSON))
def test_returns_html_module_not_found(
    post_function: MagicMock, fail_httpx_import_module_not_found: None
) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        with pytest.deprecated_call():
            response = client.get("/")
        post_function.assert_called_once_with(
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


@patch("requests.post", side_effect=Exception())
def test_fallback_to_classic_if_render_errors_module_not_found(
    post_function: MagicMock, fail_httpx_import_module_not_found: None
) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        with pytest.deprecated_call():
            response = client.get("/")
        post_function.assert_called_once_with(
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


@patch("requests.post")
def test_calls_inertia_render_import_error(
    post_function: MagicMock, fail_httpx_import: None
) -> None:
    with TestClient(app) as client:
        with pytest.deprecated_call():
            client.get("/")
        post_function.assert_called_once_with(
            url=f"{SSR_URL}/render",
            json={
                "component": COMPONENT,
                "props": EXPECTED_PROPS,
                "url": f"{client.base_url}/",
                "version": "1.0",
            },
            headers={"Content-Type": "application/json"},
        )


@patch("requests.post", return_value=MagicMock(json=lambda: RETURNED_JSON))
def test_returns_html_import_error(
    post_function: MagicMock, fail_httpx_import: None
) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        with pytest.deprecated_call():
            response = client.get("/")
        post_function.assert_called_once_with(
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


@patch("requests.post", side_effect=Exception())
def test_fallback_to_classic_if_render_errors_import_error(
    post_function: MagicMock, fail_httpx_import: None
) -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        with pytest.deprecated_call():
            response = client.get("/")
        post_function.assert_called_once_with(
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
