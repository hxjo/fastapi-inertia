from fastapi import FastAPI, Depends
from typing import Annotated, TypedDict, cast

from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

from inertia import InertiaRenderer, inertia_renderer_factory, InertiaConfig, InertiaResponse

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="secret_key")

InertiaDep = Annotated[
    InertiaRenderer, Depends(inertia_renderer_factory(InertiaConfig(
        use_flash_messages=True,
    ))),
]


PROPS= {
    "message": "hello from index",
    "messages": [{"message": "hello from flash message", "category": "info"}]
}

COMPONENT = "IndexPage"


def dependency(inertia: InertiaDep) -> None:
    messages = cast(list[dict[str, str]], PROPS.get("messages"))
    inertia.flash(**messages[0])


@app.get("/", response_model=None, dependencies=[Depends(dependency)])
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, {
        "message": PROPS.get("message"),
    })


def test_flash_message_is_included_from_dependency() -> None:
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

