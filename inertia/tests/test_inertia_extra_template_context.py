import re

from fastapi import FastAPI, Depends
from typing import Annotated

from starlette.testclient import TestClient

from inertia import (
    Inertia,
    inertia_dependency_factory,
    InertiaResponse,
    InertiaConfig,
)
from .utils import templates


app = FastAPI()

InertiaDep = Annotated[
    Inertia,
    Depends(
        inertia_dependency_factory(
            InertiaConfig(
                templates=templates,
                root_template_filename="extra_context.html",
                extra_template_context={"extra_context": "Context value"},
            )
        )
    ),
]

PROPS = {
    "always_str": "hello from str",
}

COMPONENT = "IndexPage"


@app.get("/", response_model=None)
async def index(inertia: InertiaDep) -> InertiaResponse:
    return await inertia.render(COMPONENT, PROPS)


def test_adding_extra_template_context() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

        pattern = r'<div>Context value</div>'
        assert re.search(pattern, response.text)
