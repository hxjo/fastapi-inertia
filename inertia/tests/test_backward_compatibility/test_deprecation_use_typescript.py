import json
import os
from datetime import datetime

from fastapi import FastAPI, Depends
from typing import Annotated, cast

import pytest
from starlette.testclient import TestClient

from inertia import Inertia, inertia_dependency_factory, InertiaResponse, InertiaConfig

from inertia.tests.utils import assert_response_content


PROPS = {"message": "hello from index", "created_at": datetime.now()}

EXPECTED_PROPS = {
    **PROPS,
    "created_at": cast(datetime, PROPS["created_at"]).isoformat(),
}

COMPONENT = "IndexPage"

manifest_json_ts = os.path.join(
    os.path.dirname(__file__), "..", "dummy_manifest_ts.json"
)


@pytest.fixture()
def app() -> FastAPI:
    app = FastAPI()

    with pytest.deprecated_call():
        TypescriptInertiaDep = Annotated[
            Inertia,
            Depends(
                inertia_dependency_factory(
                    InertiaConfig(
                        use_typescript=True,
                    )
                )
            ),
        ]
    with pytest.deprecated_call():
        TypescriptProductionInertiaDep = Annotated[
            Inertia,
            Depends(
                inertia_dependency_factory(
                    InertiaConfig(
                        manifest_json_path=manifest_json_ts,
                        environment="production",
                        use_typescript=True,
                    )
                )
            ),
        ]

    @app.get("/typescript", response_model=None)
    async def typescript(inertia: TypescriptInertiaDep) -> InertiaResponse:
        return await inertia.render(COMPONENT, PROPS)

    @app.get("/typescript-production", response_model=None)
    async def typescript_production(
        inertia: TypescriptProductionInertiaDep,
    ) -> InertiaResponse:
        return await inertia.render(COMPONENT, PROPS)

    return app


def test_first_request_returns_html_typescript_still_works(app: FastAPI) -> None:
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


def test_first_request_returns_html_production_typescript_still_works(
    app: FastAPI,
) -> None:
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
