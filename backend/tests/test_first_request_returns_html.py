import json
import os
from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from inertia import InertiaRenderer, inertia_renderer_factory, InertiaConfig, InertiaResponse
from .utils import get_stripped_html

app = FastAPI()
manifest_json = os.path.join(os.path.dirname(__file__), "dummy_manifest_js.json")
manifest_json_ts = os.path.join(os.path.dirname(__file__), "dummy_manifest_ts.json")

CUSTOM_URL = "http://some_other_url"

InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig()))
]

CustomUrlInertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig(
        dev_url=CUSTOM_URL
    )))
]

ProductionInertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig(
        manifest_json_path=manifest_json,
        environment="production"
    )))
]

TypescriptInertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig(
        use_typescript=True
    )))
]

TypescriptProductionInertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig(
        manifest_json_path=manifest_json_ts,
        environment="production",
        use_typescript=True
    )))
]

PROPS = {
    "message": "hello from index",
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@app.get("/typescript", response_model=None)
async def typescript(inertia: TypescriptInertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@app.get("/production", response_model=None)
async def production(inertia: ProductionInertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@app.get("/typescript-production", response_model=None)
async def typescript_production(inertia: TypescriptProductionInertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)

@app.get("/custom-url", response_model=None)
async def custom_url(inertia: CustomUrlInertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_first_request_returns_html() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get('content-type').split(';')[0] == 'text/html'
        expected_url = str(client.base_url) + "/"
        assert response.text.strip() == get_stripped_html(component_name=COMPONENT, props=PROPS, url=expected_url)



def test_first_request_returns_html_custom_url() -> None:
    with TestClient(app) as client:
        response = client.get("/custom-url")
        assert response.status_code == 200
        assert response.headers.get('content-type').split(';')[0] == 'text/html'
        expected_url = str(client.base_url) + "/custom-url"
        script_asset_url = CUSTOM_URL + "/src/main.js"
        assert response.text.strip() == get_stripped_html(component_name=COMPONENT, props=PROPS, url=expected_url, script_asset_url=script_asset_url)


def test_first_request_returns_html_typescript() -> None:
    with TestClient(app) as client:
        response = client.get("/typescript")
        assert response.status_code == 200
        assert response.headers.get('content-type').split(';')[0] == 'text/html'
        expected_url = str(client.base_url) + "/typescript"
        assert response.text.strip() == get_stripped_html(component_name=COMPONENT, props=PROPS, url=expected_url, script_asset_url="http://localhost:5173/src/main.ts")


def test_first_request_returns_html_production() -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_file = f"/src/{manifest[f"src/main.js"]["css"][0]}"
    js_file = f"/{manifest[f"src/main.js"]["file"]}"
    with TestClient(app) as client:
        response = client.get("/production")
        assert response.status_code == 200
        assert response.headers.get('content-type').split(';')[0] == 'text/html'
        expected_url = str(client.base_url) + "/production"
        assert response.text.strip() == get_stripped_html(component_name=COMPONENT, props=PROPS, url=expected_url, script_asset_url=js_file, css_asset_url=css_file)


def test_first_request_returns_html_production_typescript() -> None:
    with open(manifest_json_ts, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_file = f"/src/{manifest[f"src/main.ts"]["css"][0]}"
    js_file = f"/{manifest[f"src/main.ts"]["file"]}"
    with TestClient(app) as client:
        response = client.get("/typescript-production")
        assert response.status_code == 200
        assert response.headers.get('content-type').split(';')[0] == 'text/html'
        expected_url = str(client.base_url) + "/typescript-production"
        assert response.text.strip() == get_stripped_html(component_name=COMPONENT, props=PROPS, url=expected_url, script_asset_url=js_file, css_asset_url=css_file)

