import logging
import os
import warnings

from fastapi import Depends, Request, Response, status
from fastapi.responses import JSONResponse, HTMLResponse
from typing import (
    Annotated,
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    TypedDict,
    Union,
    cast,
)
import json
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from inertia.templating import InertiaExtension

from .config import InertiaConfig
from .utils import InertiaContext, _read_manifest_file
from .exceptions import InertiaVersionConflictException
from .utils import LazyProp
from dataclasses import dataclass

try:
    import requests
except (ModuleNotFoundError, ImportError):
    requests = None  # type: ignore

try:
    import httpx
except (ModuleNotFoundError, ImportError):
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)

InertiaResponse = Union[HTMLResponse, JSONResponse]

T = TypeVar("T")


class FlashMessage(TypedDict):
    """
    Flash message type
    """

    message: str
    category: str


class Inertia:
    """
    Inertia class to handle Inertia.js responses
    To be used as a dependency in FastAPI
    You should use the `inertia_dependency_factory` function to create a dependency, in order
    to pass the configuration to the Inertia class
    """

    @dataclass
    class InertiaFiles:
        """
        Helper class to store the CSS and JS file urls for Inertia.js
        """

        css_file_urls: List[str]
        js_file_url: str

    _request: Request
    _component: str
    _props: dict[str, Any]
    _config: InertiaConfig
    _inertia_files: InertiaFiles
    _client: Union["httpx.AsyncClient", None]

    def __init__(
        self,
        request: Request,
        config_: InertiaConfig,
        client: Union["httpx.AsyncClient", None] = None,
    ) -> None:
        """
        Constructor
        :param request: FastAPI Request object
        :param config_: InertiaConfig object
        """
        self._request = request
        self._component = ""
        self._props = {}
        self._config = config_
        self._client = client
        self._set_inertia_files()

        if self._is_stale:
            raise InertiaVersionConflictException(url=str(request.url))

    @property
    def _partial_keys(self) -> list[str]:
        """
        Get the keys of the partial data
        :return: List of keys
        """
        return self._request.headers.get("X-Inertia-Partial-Data", "").split(",")

    @property
    def _is_inertia_request(self) -> bool:
        """
        Check if the request is an Inertia request (requesting JSON)
        :return: True if the request is an Inertia request, False otherwise
        """
        return "X-Inertia" in self._request.headers

    @property
    def _is_stale(self) -> bool:
        """
        Check if the Inertia request is stale (different from the current version)
        :return: True if the version is stale, False otherwise
        """
        return bool(
            self._request.headers.get("X-Inertia-Version", self._config.version)
            != self._config.version
        )

    @property
    def _is_a_partial_render(self) -> bool:
        """
        Check if the request is a partial render
        :return: True if the request is a partial render, False otherwise
        """
        return (
            "X-Inertia-Partial-Data" in self._request.headers
            and self._request.headers.get("X-Inertia-Partial-Component", "")
            == self._component
        )

    def _get_page_data(self) -> Dict[str, Any]:
        """
        Get the data for the page
        :return: A dictionary with the page data
        """
        return {
            "component": self._component,
            "props": self._build_props(),
            "url": str(self._request.url),
            "version": self._config.version,
        }

    def _get_flashed_messages(self) -> list[FlashMessage]:
        """
        Get the flashed messages from the session (pop them from the session)
        :return: List of flashed messages
        """
        return (
            cast(list[FlashMessage], self._request.session.pop("_messages"))
            if "_messages" in self._request.session
            else []
        )

    def _get_flashed_errors(self) -> dict[str, str]:
        """
        Get the flashed errors from the session (pop them from the session)
        :return: Dict of flashed errors
        """
        return (
            cast(dict[str, str], self._request.session.pop("_errors"))
            if "_errors" in self._request.session
            else {}
        )

    def _assert_a_request_package_is_installed(self) -> None:
        """
        Assert that at least one of the request packages is installed (httpx or requests)
        :raises ImportError: If none of the packages are
        :warns DeprecatedWarning: If requests is installed
        """
        if not httpx and not requests:
            raise ImportError(
                "You need to install either requests or httpx to use Inertia in SSR mode"
            )
        if requests:
            warnings.warn(
                "requests is deprecated: Please use httpx instead. It will be removed in 1.0.0",
                DeprecationWarning,
                stacklevel=2,
            )

    def _set_inertia_files(self) -> None:
        """
        Set the Inertia files (CSS and JS) based on the configuration
        """
        if self._config.environment == "production" or self._config.ssr_enabled:
            manifest = _read_manifest_file(self._config.manifest_json_path)
            asset_manifest = manifest[
                f"{self._config.root_directory}/{self._config.entrypoint_filename}"
            ]
            css_file_urls = asset_manifest.get("css", []) or []
            js_file_url = asset_manifest["file"]

            self._inertia_files = self.InertiaFiles(
                css_file_urls=[
                    os.path.join("/", self._config.assets_prefix, file)
                    for file in css_file_urls
                ],
                js_file_url=os.path.join("/", self._config.assets_prefix, js_file_url),
            )
        else:
            js_file_url = f"{self._config.dev_url}/{self._config.root_directory}/{self._config.entrypoint_filename}"
            self._inertia_files = self.InertiaFiles(
                css_file_urls=[], js_file_url=js_file_url
            )

    @classmethod
    def _deep_transform_callables(
        cls, prop: Union[Callable[..., Any], Dict[str, Any], BaseModel, Any]
    ) -> Any:
        """
        Deeply transform callables in a dictionary, evaluating them if they are callables
        If the value is a BaseModel, it will call the model_dump method.
        Recursive function

        :param prop: Property to transform
        :return: Transformed property
        """
        if not isinstance(prop, dict):
            if callable(prop):
                return prop()
            if isinstance(prop, BaseModel):
                return json.loads(prop.model_dump_json())
            return prop

        prop_ = prop.copy()
        for key in list(prop_.keys()):
            prop_[key] = cls._deep_transform_callables(prop_[key])

        return prop_

    def _build_props(self) -> Union[Dict[str, Any], Any]:
        """
        Build the props for the page.
        If the request is a partial render, it will only include the partial keys
        :return: A dictionary with the props
        """
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
        """
        Get the HTML content for the response
        :param head: The content for the head tag
        :param body: The content for the body tag
        :return: The HTML content
        """
        css_links = (
            "\n".join(
                [
                    f'<link rel="stylesheet" href="{url}">'
                    for url in self._inertia_files.css_file_urls
                ]
            )
            if len(self._inertia_files.css_file_urls) > 0
            else ""
        )

        return f"""
                   <!DOCTYPE html>
                   <html>
                       <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            {head}
                            {css_links}
                        </head>
                        <body>
                            {body}
                            <script type="module" src="{self._inertia_files.js_file_url}"></script>
                       </body>
                   </html>
                   """

    async def _render_ssr(self) -> HTMLResponse:
        """
        Render the page using SSR, calling the Inertia SSR server.
        :return: The HTML response
        """
        self._assert_a_request_package_is_installed()
        data = json.dumps(self._get_page_data(), cls=self._config.json_encoder)
        request_kwargs: Dict[str, Any] = {
            "url": f"{self._config.ssr_url}/render",
            "json": data,
            "headers": {"Content-Type": "application/json"},
        }
        response: Union["httpx._models.Response", "requests.Response"]
        if self._client is not None:
            response = await self._client.post(**request_kwargs)
        else:
            response = requests.post(**request_kwargs)

        response.raise_for_status()
        response_json = response.json()

        head = response_json["head"]
        displayable_head = "\n".join(head)
        body = response_json["body"]

        return self._config.templates.TemplateResponse(
            name=self._config.root_template_filename,
            request=self._request,
            context={
                "inertia": InertiaContext(
                    environment=self._config.environment,
                    dev_url=self._config.dev_url,
                    is_ssr=True,
                    ssr_head=displayable_head,
                    ssr_body=body,
                    js=self._inertia_files.js_file_url,
                    css=self._inertia_files.css_file_urls,
                ),
            },
        )

    def _render_json(self) -> JSONResponse:
        """
        Render the page using JSON
        :return: The JSON response
        """
        return JSONResponse(
            content=self._get_page_data(),
            headers={
                "Vary": "Accept",
                "X-Inertia": "true",
            },
        )

    def share(self, **props: Any) -> None:
        """
        Share props between functions. Useful to share props between dependencies/middlewares and routes
        :param props: Props to share
        """
        self._props.update(props)

    def flash(self, message: str, category: str) -> None:
        """
        Flash a message to the session
        If flash messages are not enabled, it will raise a NotImplementedError
        :param message: message to flash
        :param category: category of the message
        """
        if not self._config.use_flash_messages:
            raise NotImplementedError("Flash messages are not enabled")

        if "_messages" not in self._request.session:
            self._request.session["_messages"] = []

        message_: FlashMessage = {"message": message, "category": category}
        self._request.session["_messages"].append(message_)

    @staticmethod
    def location(url: str) -> Response:
        """
        Return a response with a location header.
        Useful to redirect to a different page (outside of this server)
        :param url: URL to redirect to
        :return: Response
        """
        return Response(
            status_code=status.HTTP_409_CONFLICT,
            headers={"X-Inertia-Location": url},
        )

    def back(self) -> RedirectResponse:
        """
        Redirect back to the previous page
        :return: RedirectResponse
        """
        status_code = (
            status.HTTP_307_TEMPORARY_REDIRECT
            if self._request.method == "GET"
            else status.HTTP_303_SEE_OTHER
        )
        return RedirectResponse(
            url=self._request.headers["Referer"], status_code=status_code
        )

    async def render(
        self, component: str, props: Optional[Dict[str, Any]] = None
    ) -> InertiaResponse:
        """
        Render the page
        If the request is an Inertia request, it will return a JSONResponse
        If SSR is enabled, it will try to render the page using SSR.
        If an error occurs, it will fall back to server-side template rendering
        :param component: The component name to render
        :param props: The props to pass to the component
        :return: InertiaResponse
        """
        if self._config.use_flash_messages:
            self._props.update(
                {self._config.flash_message_key: self._get_flashed_messages()}
            )

        if self._config.use_flash_errors:
            self._props.update(
                {self._config.flash_error_key: self._get_flashed_errors()}
            )

        self._component = component
        self._props.update(props or {})

        if self._is_inertia_request:
            return self._render_json()

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
        return self._config.templates.TemplateResponse(
            name=self._config.root_template_filename,
            request=self._request,
            context={
                "inertia": InertiaContext(
                    environment=self._config.environment,
                    dev_url=self._config.dev_url,
                    is_ssr=False,
                    data=page_json,
                    js=self._inertia_files.js_file_url,
                    css=self._inertia_files.css_file_urls,
                ),
            },
        )


async def get_httpx_client() -> AsyncGenerator[Union[None, "httpx.AsyncClient"], None]:
    try:
        async with httpx.AsyncClient() as client:
            yield client
    except Exception as e:
        logger.error(f"An error occurred in creating the HTTPX client: {e}")
        yield None


HttpxClientDep = Annotated[Union["httpx.AsyncClient", None], Depends(get_httpx_client)]


def inertia_dependency_factory(
    config_: InertiaConfig,
) -> Callable[[Request, HttpxClientDep], Inertia]:
    """
    Create a dependency for Inertia, passing the configuration
    :param config_: InertiaConfig object
    :return: Dependency
    """

    config_.templates.env.add_extension(InertiaExtension)

    def inertia_dependency(request: Request, client: HttpxClientDep) -> Inertia:
        """
        Dependency for Inertia
        :param request: FastAPI Request object
        :return: Inertia object
        """
        return Inertia(request, config_, client)

    return inertia_dependency
