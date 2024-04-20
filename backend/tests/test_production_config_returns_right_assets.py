import os
from fastapi import FastAPI, Depends
from typing import Annotated
from string import Template
import json

from starlette.testclient import TestClient

from inertia import InertiaRenderer, inertia_renderer_factory, InertiaConfig, InertiaResponse

app = FastAPI()

manifest_json = os.path.join(os.path.dirname(__file__), "dummy_manifest_js.json")
InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig(
        manifest_json_path=manifest_json,
        environment="production"
    )))
]

PROPS = {
    "message": "hello from index",
}

COMPONENT = "IndexPage"

with open(manifest_json, "r") as manifest_file:
    manifest = json.load(manifest_file)

css_file = f"/src/{manifest[f"src/main.js"]["css"][0]}"
js_file = f"/{manifest[f"src/main.js"]["file"]}"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_production_config_returns_right_assets() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get('content-type').split(';')[0] == 'text/html'
        assert response.text.strip() == Template("""
                   <!DOCTYPE html>
                   <html>
                       <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            
                            <link rel="stylesheet" href="$css_file">
                        </head>
                        <body>
                            <div id='app' data-page='{"component": "$component_name", "props": $props, "url": "$url/", "version": "1.0"}'></div>
                            <script type="module" src="$js_file"></script>
                       </body>
                   </html>
        """).substitute(component_name=COMPONENT, props=json.dumps(PROPS), url=client.base_url, js_file=js_file, css_file=css_file).strip()
