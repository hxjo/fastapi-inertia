import json
import os
from datetime import datetime

from fastapi import FastAPI, Depends
from typing import Annotated, cast

from starlette.testclient import TestClient

from inertia import Inertia, inertia_dependency_factory, InertiaResponse, InertiaConfig

from .utils import assert_response_content, templates

app = FastAPI()
manifest_json = os.path.join(os.path.dirname(__file__), "dummy_manifest_js.json")
manifest_json_ts = os.path.join(os.path.dirname(__file__), "dummy_manifest_ts.json")

CUSTOM_URL = "http://some_other_url"

InertiaDep = Annotated[
    Inertia, Depends(inertia_dependency_factory(InertiaConfig(templates=templates)))
]

CustomUrlInertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(dev_url=CUSTOM_URL, templates=templates)
        )
    ),
]

ProductionInertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                manifest_json_path=manifest_json,
                environment="production",
                templates=templates,
            )
        )
    ),
]


ProductionWithAssetPrefixInertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                manifest_json_path=manifest_json,
                environment="production",
                assets_prefix="/assets",
                templates=templates,
            )
        )
    ),
]

TypescriptInertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(entrypoint_filename="main.ts", templates=templates)
        )
    ),
]

TypescriptProductionInertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                manifest_json_path=manifest_json_ts,
                environment="production",
                entrypoint_filename="main.ts",
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


@app.get("/typescript", response_model=None)
async def typescript(inertia: TypescriptInertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@app.get("/production", response_model=None)
async def production(inertia: ProductionInertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@app.get("/production-asset-prefix", response_model=None)
async def production_asset_prefix(
    inertia: ProductionWithAssetPrefixInertiaDep,
) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@app.get("/typescript-production", response_model=None)
async def typescript_production(
    inertia: TypescriptProductionInertiaDep,
) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


@app.get("/custom-url", response_model=None)
async def custom_url(inertia: CustomUrlInertiaDep) -> InertiaResponse:
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


def test_first_request_returns_html_custom_url() -> None:
    with TestClient(app) as client:
        response = client.get("/custom-url")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        expected_url = str(client.base_url) + "/custom-url"
        script_asset_url = CUSTOM_URL + "/src/main.js"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS,
            expected_url=expected_url,
            expected_script_asset_url=script_asset_url,
        )


def test_first_request_returns_html_typescript() -> None:
    with TestClient(app) as client:
        response = client.get("/typescript")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        expected_url = str(client.base_url) + "/typescript"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS,
            expected_url=expected_url,
            expected_script_asset_url="http://localhost:5173/src/main.ts",
        )


def test_first_request_returns_html_production() -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_files = [f"/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        response = client.get("/production")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        expected_url = str(client.base_url) + "/production"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS,
            expected_url=expected_url,
            expected_script_asset_url=js_file,
            expected_css_asset_urls=css_files,
        )


def test_first_request_returns_html_production_typescript() -> None:
    with open(manifest_json_ts, "r") as manifest_file:
        manifest = json.load(manifest_file)

    css_files = [f"/{file}" for file in manifest["src/main.ts"]["css"]]
    js_file = manifest["src/main.ts"]["file"]
    js_file = f"/{js_file}"
    with TestClient(app) as client:
        response = client.get("/typescript-production")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        expected_url = str(client.base_url) + "/typescript-production"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS,
            expected_url=expected_url,
            expected_script_asset_url=js_file,
            expected_css_asset_urls=css_files,
        )


def test_first_request_returns_html_production_with_prefix_on_assets() -> None:
    with open(manifest_json, "r") as manifest_file:
        manifest = json.load(manifest_file)
    css_files = [f"/assets/{file}" for file in manifest["src/main.js"]["css"]]
    js_file = manifest["src/main.js"]["file"]
    js_file = f"/assets/{js_file}"
    with TestClient(app) as client:
        response = client.get("/production-asset-prefix")
        assert response.status_code == 200
        assert response.headers.get("content-type").split(";")[0] == "text/html"
        expected_url = str(client.base_url) + "/production-asset-prefix"
        assert_response_content(
            response,
            expected_component=COMPONENT,
            expected_props=EXPECTED_PROPS,
            expected_url=expected_url,
            expected_script_asset_url=js_file,
            expected_css_asset_urls=css_files,
        )
