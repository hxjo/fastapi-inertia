from typing import Literal, Type
from json import JSONEncoder

from fastapi.templating import Jinja2Templates
from .utils import InertiaJsonEncoder
from dataclasses import dataclass


@dataclass
class InertiaConfig:
    """
    Configuration class for Inertia
    """

    templates: Jinja2Templates
    environment: Literal["development", "production"] = "development"
    version: str = "1.0"
    json_encoder: Type[JSONEncoder] = InertiaJsonEncoder
    dev_url: str = "http://localhost:5173"
    ssr_url: str = "http://localhost:13714"
    ssr_enabled: bool = False
    manifest_json_path: str = ""
    root_directory: str = "src"
    root_template_filename: str = "index.html"
    entrypoint_filename: str = "main.js"
    use_flash_messages: bool = False
    use_flash_errors: bool = False
    flash_message_key: str = "messages"
    flash_error_key: str = "errors"
    assets_prefix: str = ""
