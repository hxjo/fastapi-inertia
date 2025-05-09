from typing import Literal, Type, Dict, Any
from json import JSONEncoder

from fastapi.templating import Jinja2Templates
from .utils import InertiaJsonEncoder
from dataclasses import dataclass, field


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
    extra_template_context: Dict[str, Any] = field(default_factory=dict)
