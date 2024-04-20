from fastapi import FastAPI, Depends
from typing import Annotated
from string import Template
import json

from starlette.testclient import TestClient

from inertia import InertiaRenderer, inertia_renderer_factory, InertiaConfig, InertiaResponse

app = FastAPI()

InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig()))
]

PROPS = {
    "message": "hello from index",
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_first_request_returns_html() -> None:
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
                            
                            
                        </head>
                        <body>
                            <div id='app' data-page='{"component": "$component_name", "props": $props, "url": "$url/", "version": "1.0"}'></div>
                            <script type="module" src="http://localhost:5173/src/main.js"></script>
                       </body>
                   </html>
        """).substitute(component_name=COMPONENT, props=json.dumps(PROPS), url=client.base_url).strip()
