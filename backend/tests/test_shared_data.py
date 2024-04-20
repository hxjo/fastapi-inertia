from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from inertia import InertiaRenderer, inertia_renderer_factory, InertiaConfig, InertiaResponse

app = FastAPI()

InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig()))
]

PROPS = {
    "message": "hello from index",
    "dependency_message": "hello from dependency",
}

COMPONENT = "IndexPage"


def dependency(inertia: InertiaDep) -> None:
    inertia.share(message=PROPS.get("dependency_message"))


@app.get("/", response_model=None, dependencies=[Depends(dependency)])
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_shared_data_is_included_from_dependency() -> None:
    with TestClient(app) as client:
        response = client.get("/", headers={"X-Inertia": "true"})
        assert response.status_code == 200
        assert response.headers.get('content-type').split(';')[0] == 'application/json'
        assert response.json() == {
            "component": COMPONENT,
            "props": PROPS,
            "url": f"{client.base_url}/",
            "version": "1.0",
        }
