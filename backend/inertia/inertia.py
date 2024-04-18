import json
import os
from typing import Any, Callable, TypeVar, cast

from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse, Response
from json import dumps as json_encode
from functools import wraps
from .settings import settings
from .utils import LazyProp
import requests


async def render(
    request: Request,
    component: str,
    props: dict[str, Any] | None = None,
    template_data: dict[str, Any] | None = None,
) -> HTMLResponse | JSONResponse:
    props = props or {}
    template_data = template_data or {}

    def is_a_partial_render() -> bool:
        return (
            "X-Inertia-Partial-Data" in request.headers
            and request.headers.get("X-Inertia-Partial-Component", "") == component
        )

    def partial_keys() -> list[str]:
        return cast(str, request.headers.get("X-Inertia-Partial-Data", "")).split(",")

    def deep_transform_callables(prop: Any) -> Any:
        if not isinstance(prop, dict):
            return prop() if callable(prop) else prop

        for key in list(prop.keys()):
            prop[key] = deep_transform_callables(prop[key])

        return prop

    def build_props() -> Any:
        _props = {
            **(
                request.state.inertia.all() if hasattr(request.state, "inertia") else {}
            ),
            **props,
        }

        for key in list(_props.keys()):
            if is_a_partial_render():
                if key not in partial_keys():
                    del _props[key]
            else:
                if isinstance(_props[key], LazyProp):
                    del _props[key]

        return deep_transform_callables(_props)

    async def render_ssr() -> HTMLResponse:
        data = json_encode(page_data(), cls=settings.INERTIA_JSON_ENCODER)
        response = requests.post(
            f"{settings.INERTIA_SSR_URL}/render",
            json=data,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        response_json = response.json()
        head = response_json["head"]
        displayable_head = "\n".join(head)
        body = response_json["body"]
        with open(settings.INERTIA_MANIFEST_JSON, "r") as manifest_file:
            manifest = json.load(manifest_file)

        # Get the CSS and JS file names from the manifest
        css_file = manifest["src/main.js"]["css"][0]
        js_file = manifest["src/main.js"]["file"]
        html_content = f"""
           <!DOCTYPE html>
           <html>
               <head>
                   {displayable_head}
               <link rel="stylesheet" href="/src/{css_file}">
                </head>
                <body>
                    {body}
                    <script type="module" src="/{js_file}"></script>
               </body>
           </html>
           """

        return HTMLResponse(content=html_content, status_code=200)

    def page_data() -> dict[str, Any]:
        return {
            "component": component,
            "props": build_props(),
            "url": str(request.url),
            "version": settings.INERTIA_VERSION,
        }

    if "X-Inertia" in request.headers:
        return JSONResponse(
            content=page_data(),
            headers={
                "Vary": "Accept",
                "X-Inertia": "true",
            },
        )

    if settings.INERTIA_SSR_ENABLED:
        try:
            return await render_ssr()
        except Exception as exc:
            print(exc)

    template = settings.INERTIA_TEMPLATE_ENV.get_template("app.html")
    content = template.render(
        page=json_encode(page_data(), cls=settings.INERTIA_JSON_ENCODER),
        **template_data,
    )
    return HTMLResponse(content=content)

T = TypeVar("T")


def inertia(component: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def inner(request: Request, *args: Any, **kwargs: Any) -> Response:
            props = await func(request, *args, **kwargs)

            if not isinstance(props, dict):
                return cast(Response, props)

            return await render(request, component, cast(dict[str, Any], props))

        return inner

    return decorator
