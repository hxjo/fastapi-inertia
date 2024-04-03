from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse
from json import dumps as json_encode
from functools import wraps
from .settings import settings
from .utils import LazyProp


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
        return request.headers.get("X-Inertia-Partial-Data", "").split(",")

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

    template = settings.INERTIA_TEMPLATE_ENV.get_template("app.html")
    content = template.render(
        page=json_encode(page_data(), cls=settings.INERTIA_JSON_ENCODER),
        **template_data,
    )
    return HTMLResponse(content=content)


def inertia(component: str) -> Any:
    def decorator(func: Any) -> Any:
        @wraps(func)
        async def inner(request: Request, *args: Any, **kwargs: Any) -> Any:
            props = await func(request, *args, **kwargs)

            if not isinstance(props, dict):
                return props

            return await render(request, component, props)

        return inner

    return decorator
