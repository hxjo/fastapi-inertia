import logging

from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Any, Dict, Optional
import json
import requests

from .config import InertiaConfig
from .exceptions import InertiaVersionConflict
from .utils import get_flashed_messages, flash_message
from dataclasses import dataclass

logger = logging.getLogger(__name__)

InertiaResponse = HTMLResponse | JSONResponse


class InertiaRenderer:
    @dataclass
    class InertiaFiles:
        css_file: str
        js_file: str

    _request: Request
    _component: str
    _props: dict[str, Any]
    _inertia_files: InertiaFiles

    def __init__(self, request: Request, config_: InertiaConfig = InertiaConfig()):
        self._request = request
        self._component = ""
        self._props = {}
        self._config = config_
        self._set_inertia_files()

        if self._is_stale():
            raise InertiaVersionConflict(url=str(request.url))

        self._props.update({"messages": get_flashed_messages(request)})

    def _set_inertia_files(self) -> None:
        if self._config.SSR_ENABLED or self._config.ENV == "production":
            with open(self._config.MANIFEST_JSON_PATH, "r") as manifest_file:
                manifest = json.load(manifest_file)

            css_file = manifest["src/main.js"]["css"][0]
            js_file = manifest["src/main.js"]["file"]
            self._inertia_files = self.InertiaFiles(
                css_file=f"/src/{css_file}", js_file=f"/{js_file}"
            )
        else:
            css_file = "/src/assets/index.css"
            js_file = f"{self._config.DEV_URL}/src/main.js"
            self._inertia_files = self.InertiaFiles(css_file=css_file, js_file=js_file)

    def _is_inertia_request(self) -> bool:
        return "X-Inertia" in self._request.headers

    def _is_stale(self) -> bool:
        return bool(
            self._request.headers.get("X-Inertia-Version", self._config.VERSION)
            != self._config.VERSION
        )

    def _page_data(self) -> Dict[str, Any]:
        return {
            "component": self._component,
            "props": self._props,
            "url": str(self._request.url),
            "version": self._config.VERSION,
        }

    def _get_html_content(self, head: str, body: str) -> str:
        return f"""
                   <!DOCTYPE html>
                   <html>
                       <head>
                           {head}
                       <link rel="stylesheet" href="{self._inertia_files.css_file}">
                        </head>
                        <body>
                            {body}
                            <script type="module" src="{self._inertia_files.js_file}"></script>
                       </body>
                   </html>
                   """

    async def _render_ssr(self) -> HTMLResponse:
        data = json.dumps(self._page_data(), cls=self._config.JSON_ENCODER)
        response = requests.post(
            f"{self._config.SSR_URL}/render",
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
        flash_message(self._request, message, category)

    async def render(
        self, component: str, props: Optional[Dict[str, Any]] = None
    ) -> HTMLResponse | JSONResponse:
        self._component = component
        self._props.update(props or {})

        if "X-Inertia" in self._request.headers:
            return JSONResponse(
                content=self._page_data(),
                headers={
                    "Vary": "Accept",
                    "X-Inertia": "true",
                },
            )

        if self._config.SSR_ENABLED:
            try:
                return await self._render_ssr()
            except Exception as exc:
                logger.error(
                    f"An error occurred in rendering SSR (falling back to classic rendering): {exc}"
                )

        # Fallback to server-side template rendering
        page_json = json.dumps(
            json.dumps(self._page_data(), cls=self._config.JSON_ENCODER)
        )
        body = f"<div id='app' data-page='{page_json}'></div>"
        html_content = self._get_html_content("", body)

        return HTMLResponse(content=html_content)
