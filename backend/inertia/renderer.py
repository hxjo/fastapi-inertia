import logging

from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Any, Callable, Dict, Optional, TypeVar, TypedDict, Union, cast
import json
import requests

from .config import InertiaConfig
from .exceptions import InertiaVersionConflictException
from .utils import LazyProp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

InertiaResponse = HTMLResponse | JSONResponse

T = TypeVar("T")


class FlashMessage(TypedDict):
    message: str
    category: str


class InertiaRenderer:
    @dataclass
    class InertiaFiles:
        css_file: Union[str, None]
        js_file: str

    _request: Request
    _component: str
    _props: dict[str, Any]
    _inertia_files: InertiaFiles

    def __init__(self, request: Request, config_: InertiaConfig):
        self._request = request
        self._component = ""
        self._props = {}
        self._config = config_
        self._set_inertia_files()

        if self._is_stale:
            raise InertiaVersionConflictException(url=str(request.url))

    @property
    def _partial_keys(self) -> list[str]:
        return self._request.headers.get("X-Inertia-Partial-Data", "").split(",")

    @property
    def _is_inertia_request(self) -> bool:
        return "X-Inertia" in self._request.headers

    @property
    def _is_stale(self) -> bool:
        return bool(
            self._request.headers.get("X-Inertia-Version", self._config.version)
            != self._config.version
        )

    @property
    def _is_a_partial_render(self) -> bool:
        return (
            "X-Inertia-Partial-Data" in self._request.headers
            and self._request.headers.get("X-Inertia-Partial-Component", "")
            == self._component
        )

    def _get_page_data(self) -> Dict[str, Any]:
        return {
            "component": self._component,
            "props": self._build_props(),
            "url": str(self._request.url),
            "version": self._config.version,
        }

    def _get_flashed_messages(self) -> list[FlashMessage]:
        return (
            cast(list[FlashMessage], self._request.session.pop("_messages"))
            if "_messages" in self._request.session
            else []
        )

    def _set_inertia_files(self) -> None:
        if self._config.ssr_enabled or self._config.environment == "production":
            with open(self._config.manifest_json_path, "r") as manifest_file:
                manifest = json.load(manifest_file)

            extension = "ts" if self._config.use_typescript else "js"

            css_file = manifest[f"src/main.{extension}"]["css"][0]
            js_file = manifest[f"src/main.{extension}"]["file"]
            self._inertia_files = self.InertiaFiles(
                css_file=f"/src/{css_file}", js_file=f"/{js_file}"
            )
        else:
            extension = "ts" if self._config.use_typescript else "js"
            js_file = f"{self._config.dev_url}/src/main.{extension}"
            self._inertia_files = self.InertiaFiles(css_file=None, js_file=js_file)

    @classmethod
    def _deep_transform_callables(
        cls, prop: Union[Callable[..., Any], Dict[str, Any]]
    ) -> Any:
        if not isinstance(prop, dict):
            return prop() if callable(prop) else prop

        prop_ = prop.copy()
        for key in list(prop_.keys()):
            prop_[key] = cls._deep_transform_callables(prop_[key])

        return prop_

    def _build_props(self) -> Union[Dict[str, Any], Any]:
        _props = self._props.copy()

        for key in list(_props.keys()):
            if self._is_a_partial_render:
                if key not in self._partial_keys:
                    del _props[key]
            else:
                if isinstance(_props[key], LazyProp):
                    del _props[key]

        return self._deep_transform_callables(_props)

    def _get_html_content(self, head: str, body: str) -> str:
        css_link = (
            f'<link rel="stylesheet" href="{self._inertia_files.css_file}">'
            if self._inertia_files.css_file
            else ""
        )
        return f"""
                   <!DOCTYPE html>
                   <html>
                       <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            {head}
                            {css_link}
                        </head>
                        <body>
                            {body}
                            <script type="module" src="{self._inertia_files.js_file}"></script>
                       </body>
                   </html>
                   """

    async def _render_ssr(self) -> HTMLResponse:
        data = json.dumps(self._get_page_data(), cls=self._config.json_encoder)
        response = requests.post(
            f"{self._config.ssr_url}/render",
            json=data,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        response_json = response.json()

        head = response_json["head"]
        displayable_head = "\n".join(head)
        body = response_json["body"]

        html_content = self._get_html_content(displayable_head, body)

        return HTMLResponse(content=html_content, status_code=200)

    def share(self, **props: Any) -> None:
        self._props.update(props)

    def flash(self, message: str, category: str = "primary") -> None:
        if not self._config.use_flash_messages:
            raise NotImplementedError("Flash messages are not enabled")

        if "_messages" not in self._request.session:
            self._request.session["_messages"] = []

        message_: FlashMessage = {"message": message, "category": category}
        self._request.session["_messages"].append(message_)

    async def render(
        self, component: str, props: Optional[Dict[str, Any]] = None
    ) -> HTMLResponse | JSONResponse:
        if self._config.use_flash_messages:
            self._props.update({"messages": self._get_flashed_messages()})

        self._component = component
        self._props.update(props or {})

        if "X-Inertia" in self._request.headers:
            return JSONResponse(
                content=self._get_page_data(),
                headers={
                    "Vary": "Accept",
                    "X-Inertia": "true",
                },
            )

        if self._config.ssr_enabled:
            try:
                return await self._render_ssr()
            except Exception as exc:
                logger.error(
                    f"An error occurred in rendering SSR (falling back to classic rendering): {exc}"
                )

        # Fallback to server-side template rendering
        page_json = json.dumps(
            json.dumps(self._get_page_data(), cls=self._config.json_encoder)
        )
        body = f"<div id='app' data-page='{page_json}'></div>"
        html_content = self._get_html_content("", body)

        return HTMLResponse(content=html_content)


def inertia_renderer_factory(
    config_: InertiaConfig,
) -> Callable[[Request], InertiaRenderer]:
    def inertia_dependency(request: Request) -> InertiaRenderer:
        return InertiaRenderer(request, config_)

    return inertia_dependency
